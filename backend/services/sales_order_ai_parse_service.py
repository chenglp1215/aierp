"""AI 智能销售订单解析服务（使用 Function Calling）"""
import json
import re
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from app.routers.prompts.sales_order import (
    SALES_ORDER_AI_PARSE_SYSTEM_PROMPT,
    SALES_ORDER_AI_PARSE_USER_PROMPT,
)
from models_mysql.product import Product, ProductSpec, Brand
from models_mysql.customer import Customer
from services.ai_service_mysql import LlmConfigService
from validators.sales_order_ai_parse_validator import SalesOrderAiParseRequest

logger = logging.getLogger(__name__)


# 定义 LangChain tools
@tool
async def search_customer(keyword: str) -> str:
    """搜索客户。根据客户名称关键词搜索客户库，返回匹配的客户列表。

    Args:
        keyword: 客户名称关键词

    Returns:
        匹配的客户列表（JSON格式）
    """
    if not keyword or not keyword.strip():
        return json.dumps({"success": False, "message": "请提供搜索关键词", "customers": []})

    customers = await Customer.filter(
        customer_name__icontains=keyword.strip(),
        customer_status=1  # 1=正常
    ).all().limit(5)

    if not customers:
        return json.dumps({
            "success": True,
            "message": f"未找到包含 '{keyword}' 的客户",
            "customers": []
        })

    result = [
        {
            "id": c.id,
            "name": c.customer_name,
            "code": c.customer_code,
        }
        for c in customers
    ]

    return json.dumps({
        "success": True,
        "message": f"找到 {len(result)} 个匹配的客户",
        "customers": result
    }, ensure_ascii=False)


@tool
async def search_product(name: str, spec: str = "") -> str:
    """搜索商品规格。根据商品名称和规格描述搜索商品库，返回匹配的规格列表。

    Args:
        name: 商品名称（化学名/产品名）
        spec: 规格描述（如：500g、1kg、500ml等），可选

    Returns:
        匹配的商品规格列表（JSON格式）
    """
    if not name or not name.strip():
        return json.dumps({"success": False, "message": "请提供商品名称", "specs": []})

    name = name.strip()
    spec = (spec or "").strip().lower()

    # 第一步：按产品名称搜索
    products = await Product.filter(name__icontains=name, is_active=True).all()

    if not products:
        # 尝试按规格编号搜索
        specs_by_code = await ProductSpec.filter(
            spec_code__icontains=name,
            is_active=True
        ).all()
        if specs_by_code:
            product_ids = list({s.product_id for s in specs_by_code})
            products = await Product.filter(id__in=product_ids).all()

    if not products:
        return json.dumps({
            "success": True,
            "message": f"未找到商品 '{name}'",
            "specs": []
        })

    # 第二步：获取这些产品的所有规格
    product_ids = [p.id for p in products]
    all_specs = await ProductSpec.filter(
        product_id__in=product_ids,
        is_active=True
    ).all()

    # 第三步：如果有规格描述，筛选匹配的规格
    matched_specs = []
    if spec and all_specs:
        for s in all_specs:
            packaging = (s.packaging or "").lower()
            sales_spec = (s.sales_spec or "").lower()
            spec_code = (s.spec_code or "").lower()

            # 计算匹配得分
            score = 0
            if spec in packaging or packaging in spec:
                score += 10
            if spec in sales_spec or sales_spec in spec:
                score += 8
            if spec in spec_code:
                score += 5

            if score > 0:
                matched_specs.append((s, score))

        matched_specs.sort(key=lambda x: x[1], reverse=True)
        matched_specs = [s[0] for s in matched_specs]

    # 如果没有匹配到规格，使用所有规格
    if not matched_specs:
        matched_specs = all_specs[:5]
    else:
        matched_specs = matched_specs[:5]

    # 第四步：构建返回数据
    product_map = {p.id: p for p in products}

    # 获取品牌信息
    brand_ids = set()
    for p in products:
        if hasattr(p, 'brand_id') and p.brand_id:
            brand_ids.add(p.brand_id)
    brand_map = {}
    if brand_ids:
        brands = await Brand.filter(id__in=brand_ids).all()
        brand_map = {b.id: b.name for b in brands}

    result = []
    for s in matched_specs:
        product = product_map.get(s.product_id)
        if not product:
            continue
        result.append({
            "spec_id": s.id,
            "spec_code": s.spec_code,
            "product_id": s.product_id,
            "product_name": product.name,
            "brand_name": brand_map.get(product.brand_id, "") if hasattr(product, 'brand_id') else "",
            "packaging": s.packaging or "",
            "sales_spec": s.sales_spec or "",
            "price": s.price,
        })

    return json.dumps({
        "success": True,
        "message": f"找到 {len(result)} 个匹配的规格",
        "specs": result
    }, ensure_ascii=False)


class SalesOrderAiParseService:
    """AI 销售订单解析服务（使用 Function Calling）"""

    async def parse_by_ai(self, request: SalesOrderAiParseRequest) -> dict[str, Any]:
        """
        调用 LLM 解析销售订单信息（使用 Function Calling 让 LLM 自己调用工具匹配客户和商品）

        Args:
            request: 包含 text 和 images 的请求体

        Returns:
            解析后的结构化订单数据

        Raises:
            ValueError: 输入校验失败
            RuntimeError: LLM 调用失败或返回格式异常
        """
        # 1. 校验输入
        if not request.has_input():
            raise ValueError("请提供文本描述或图片")

        # 2. 从数据库获取 LLM 配置
        config_service = LlmConfigService()
        config_data = await config_service.get_config()
        if not config_data:
            raise RuntimeError("AI服务未配置，请在智能设置中配置LLM")

        # 3. 构造 ChatOpenAI 实例，绑定 tools
        llm_kwargs = {
            "model": config_data.get("default_model") or "gpt-4",
            "temperature": config_data.get("temperature") or 0.1,
            "max_tokens": config_data.get("max_tokens") or 4096,
            "timeout": config_data.get("timeout") or 120,
        }
        if config_data.get("api_key"):
            llm_kwargs["api_key"] = config_data["api_key"]
        if config_data.get("api_base_url"):
            llm_kwargs["base_url"] = config_data["api_base_url"]

        # 4. 如果有图片，检查模型是否支持多模态
        has_images = bool(request.images)
        model_name = llm_kwargs["model"].lower()
        non_vision_models = ["deepseek-chat", "deepseek-coder", "glm-4-flash", "qwen-turbo"]
        supports_vision = not any(kw in model_name for kw in non_vision_models)

        if has_images and not supports_vision:
            logger.warning(f"模型 {model_name} 不支持图片输入，将忽略图片仅使用文本")
            request = SalesOrderAiParseRequest(text=request.text, images=None)

        # 5. 创建带 tools 的 LLM
        llm = ChatOpenAI(**llm_kwargs)
        tools = [search_customer, search_product]
        llm_with_tools = llm.bind_tools(tools)

        # 6. 构造多模态消息
        messages = self._build_messages(request)

        # 7. 多轮对话，让 LLM 调用工具并校验结果
        max_iterations = 15  # 增加迭代次数，包含校验重试
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                response = await llm_with_tools.ainvoke(messages)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"LLM 调用失败: {error_msg}")
                if "does not support images" in error_msg or "vision" in error_msg.lower():
                    raise RuntimeError("当前模型不支持图片识别，请使用支持多模态的模型") from e
                raise RuntimeError(f"AI解析失败：{error_msg}") from e

            # 如果 LLM 想要调用工具
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    logger.info(f"LLM 调用工具: {tool_name}({tool_args})")

                    # 执行工具
                    if tool_name == "search_customer":
                        tool_result = await search_customer.ainvoke(tool_args)
                    elif tool_name == "search_product":
                        tool_result = await search_product.ainvoke(tool_args)
                    else:
                        tool_result = json.dumps({"error": f"未知工具: {tool_name}"})

                    # 将工具结果添加到消息历史
                    messages.append(response)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })

            else:
                # LLM 不再调用工具，尝试解析和校验 JSON
                raw_content = response.content
                parsed = self._parse_llm_response(raw_content)

                if parsed is None:
                    # JSON 解析失败，要求 LLM 重新输出
                    logger.warning("JSON 解析失败，要求 LLM 重新输出")
                    messages.append(response)
                    messages.append(HumanMessage(content="你的输出不是有效的 JSON 格式。请重新输出完整的 JSON 对象，不要包含任何注释或额外文本。"))
                    continue

                # 校验 JSON 结构
                validation_errors = self._validate_result_structure(parsed)
                if validation_errors:
                    # 结构校验失败，要求 LLM 修正
                    logger.warning(f"JSON 结构校验失败: {validation_errors}")
                    messages.append(response)
                    error_msg = "你的 JSON 输出有以下问题，请修正后重新输出完整的 JSON：\n" + "\n".join(f"- {e}" for e in validation_errors)
                    messages.append(HumanMessage(content=error_msg))
                    continue

                # 校验通过，返回结果
                break
        else:
            # 超过最大迭代次数
            raise RuntimeError("AI 解析超时，请简化输入后重试")

        # 8. 数据清洗
        result = self._sanitize_result(parsed)

        # 9. 后处理：补充 matched 中缺失的字段
        result = await self._enrich_matched_data(result)

        return result

    def _build_messages(self, request: SalesOrderAiParseRequest) -> list:
        """构造多模态消息列表"""
        messages = [SystemMessage(content=SALES_ORDER_AI_PARSE_SYSTEM_PROMPT)]

        content_parts: list[dict[str, Any]] = []

        user_text = SALES_ORDER_AI_PARSE_USER_PROMPT
        if request.text and request.text.strip():
            user_text += f"\n\n文本描述：{request.text}"

        content_parts.append({"type": "text", "text": user_text})

        if request.images:
            for img_base64 in request.images:
                mime_type = self._detect_image_mime(img_base64)
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{img_base64}"
                    }
                })

        messages.append(HumanMessage(content=content_parts))
        return messages

    def _detect_image_mime(self, base64_str: str) -> str:
        """通过 base64 内容检测图片 MIME 类型"""
        try:
            import base64
            header_bytes = base64.b64decode(base64_str[:16])
            header_hex = header_bytes.hex().upper()

            if header_hex.startswith("FFD8"):
                return "image/jpeg"
            elif header_hex.startswith("89504E47"):
                return "image/png"
            elif header_hex.startswith("47494638"):
                return "image/gif"
            elif header_hex.startswith("52494646"):
                return "image/webp"
        except Exception:
            pass
        return "image/jpeg"

    def _validate_result_structure(self, data: dict[str, Any]) -> list[str]:
        """校验 JSON 结构是否完整

        Returns:
            错误信息列表，空列表表示校验通过
        """
        errors = []

        # 必须包含的字段
        required_fields = ["customer", "items", "order_info", "deliver_info", "invoice_info"]
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必填字段: {field}")

        # 校验 customer
        customer = data.get("customer", {})
        if not isinstance(customer, dict):
            errors.append("customer 必须是对象")
        elif "extracted_name" not in customer:
            errors.append("customer 缺少 extracted_name 字段")

        # 校验 items
        items = data.get("items", [])
        if not isinstance(items, list):
            errors.append("items 必须是数组")
        else:
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"items[{i}] 必须是对象")
                    continue

                # 每个 item 必须包含的字段
                item_required = ["qty", "price"]
                for field in item_required:
                    if field not in item:
                        errors.append(f"items[{i}] 缺少必填字段: {field}")

                # qty 和 price 必须是数字
                if "qty" in item and not isinstance(item["qty"], (int, float)):
                    errors.append(f"items[{i}].qty 必须是数字")
                if "price" in item and not isinstance(item["price"], (int, float)):
                    errors.append(f"items[{i}].price 必须是数字")

                # matched 如果存在，必须是数组
                if "matched" in item and not isinstance(item["matched"], list):
                    errors.append(f"items[{i}].matched 必须是数组")

        # 校验 order_info
        order_info = data.get("order_info", {})
        if not isinstance(order_info, dict):
            errors.append("order_info 必须是对象")

        # 校验 deliver_info
        deliver_info = data.get("deliver_info", {})
        if not isinstance(deliver_info, dict):
            errors.append("deliver_info 必须是对象")

        # 校验 invoice_info
        invoice_info = data.get("invoice_info", {})
        if not isinstance(invoice_info, dict):
            errors.append("invoice_info 必须是对象")

        return errors

    def _parse_llm_response(self, raw_content: str) -> dict[str, Any] | None:
        """解析 LLM 返回的 JSON，支持多种格式容错"""
        if not raw_content:
            return None

        # 尝试直接解析
        try:
            result = json.loads(raw_content)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # 尝试从 ```json ... ``` 中提取
        json_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        matches = re.findall(json_block_pattern, raw_content, re.DOTALL)
        for match in matches:
            try:
                result = json.loads(match.strip())
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                continue

        # 尝试查找第一个 { 到最后一个 } 之间的内容
        first_brace = raw_content.find("{")
        last_brace = raw_content.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            try:
                result = json.loads(raw_content[first_brace:last_brace + 1])
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        logger.warning(f"无法解析 LLM 返回的 JSON: {raw_content[:200]}")
        return None

    def _sanitize_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        """数据清洗：数值兜底、字符串清理、结构保障"""
        result = {
            "customer": raw.get("customer", {}) or {},
            "order_info": raw.get("order_info", {}) or {},
            "items": raw.get("items", []) or [],
            "deliver_info": raw.get("deliver_info", {}) or {},
            "invoice_info": raw.get("invoice_info", {}) or {},
        }

        # 确保 customer 结构完整
        customer_defaults = {
            "extracted_name": None,
            "matched": [],
        }
        customer = result["customer"]
        for key, default in customer_defaults.items():
            if key not in customer:
                customer[key] = default
        result["customer"] = customer

        # 确保 order_info 结构完整，数值字段兜底
        order_defaults = {
            "order_date": None,
            "settle_type": None,
            "expect_deliver_date": None,
            "remark": None,
            "freight_amt": 0,
        }
        order_info = result["order_info"]
        for key, default in order_defaults.items():
            if key not in order_info:
                order_info[key] = default
        order_info["freight_amt"] = self._safe_float(order_info.get("freight_amt"), min_val=0)
        result["order_info"] = order_info

        # 确保 items 结构完整
        item_defaults = {
            "extracted_name": None,
            "extracted_spec": None,
            "qty": 0,
            "price": 0,
            "discount": 1,
            "shipping_method": None,
            "matched": [],
        }
        normalized_items = []
        for item in result["items"]:
            if isinstance(item, dict):
                for key, default in item_defaults.items():
                    if key not in item:
                        item[key] = default
                item["qty"] = self._safe_int(item.get("qty"), min_val=0)
                item["price"] = self._safe_float(item.get("price"), min_val=0)
                item["discount"] = self._safe_float(item.get("discount"), min_val=0, max_val=1)
                if item.get("extracted_name"):
                    item["extracted_name"] = str(item["extracted_name"]).strip()
                if item.get("extracted_spec"):
                    item["extracted_spec"] = str(item["extracted_spec"]).strip()
                normalized_items.append(item)
        result["items"] = normalized_items

        # 确保 deliver_info 结构完整
        deliver_defaults = {
            "addr": None,
            "province": None,
            "city": None,
            "district": None,
            "person_name": None,
            "person_tel": None,
        }
        deliver_info = result["deliver_info"]
        if isinstance(deliver_info, dict):
            for key, default in deliver_defaults.items():
                if key not in deliver_info:
                    deliver_info[key] = default
            for key in deliver_defaults.keys():
                if deliver_info.get(key):
                    deliver_info[key] = str(deliver_info[key]).strip()
        else:
            result["deliver_info"] = deliver_defaults
        result["deliver_info"] = deliver_info

        # 确保 invoice_info 结构完整
        invoice_defaults = {
            "invoice_title": None,
            "tax_number": None,
            "bank_name": None,
            "bank_account": None,
            "address": None,
            "phone": None,
        }
        invoice_info = result["invoice_info"]
        if isinstance(invoice_info, dict):
            for key, default in invoice_defaults.items():
                if key not in invoice_info:
                    invoice_info[key] = default
            for key in invoice_defaults.keys():
                if invoice_info.get(key):
                    invoice_info[key] = str(invoice_info[key]).strip()
        else:
            result["invoice_info"] = invoice_defaults
        result["invoice_info"] = invoice_info

        return result

    def _safe_int(self, val: Any, min_val: int = None, max_val: int = None) -> int:
        """安全转换为整数"""
        try:
            result = int(val)
        except (TypeError, ValueError):
            result = 0
        if min_val is not None and result < min_val:
            result = min_val
        if max_val is not None and result > max_val:
            result = max_val
        return result

    def _safe_float(self, val: Any, min_val: float = None, max_val: float = None) -> float:
        """安全转换为浮点数"""
        try:
            result = float(val)
        except (TypeError, ValueError):
            result = 0.0
        if min_val is not None and result < min_val:
            result = min_val
        if max_val is not None and result > max_val:
            result = max_val
        return result

    async def _enrich_matched_data(self, result: dict[str, Any]) -> dict[str, Any]:
        """补充 matched 中缺失的字段

        LLM 可能没有完整复制工具返回的数据，需要后处理补充
        """
        items = result.get("items", [])
        for item in items:
            matched = item.get("matched", [])
            if not matched:
                continue

            for m in matched:
                # 如果 spec_id 存在但 product_id 缺失，从数据库查询
                if m.get("spec_id") and not m.get("product_id"):
                    try:
                        spec = await ProductSpec.get_or_none(id=m["spec_id"])
                        if spec:
                            m["product_id"] = spec.product_id
                            # 补充其他可能缺失的字段
                            if not m.get("spec_code"):
                                m["spec_code"] = spec.spec_code
                            if not m.get("packaging"):
                                m["packaging"] = spec.packaging or ""
                            if not m.get("price"):
                                m["price"] = spec.price

                            # 获取产品信息
                            if not m.get("product_name"):
                                product = await Product.get_or_none(id=spec.product_id)
                                if product:
                                    m["product_name"] = product.name
                                    # 获取品牌
                                    if not m.get("brand_name") and product.brand_id:
                                        brand = await Brand.get_or_none(id=product.brand_id)
                                        if brand:
                                            m["brand_name"] = brand.name
                    except Exception as e:
                        logger.warning(f"补充 matched 数据失败: {e}")

        return result
