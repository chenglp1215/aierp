"""AI 智能客户信息解析服务"""
import json
import re
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.routers.prompts.customer import (
    PARSE_CUSTOMER_SYSTEM_PROMPT,
    PARSE_CUSTOMER_USER_PROMPT,
)
from services.ai_service_mysql import LlmConfigService
from validators.customer_ai_parse_validator import CustomerAiParseRequest

logger = logging.getLogger(__name__)


class CustomerAiParseService:
    """AI 客户信息解析服务"""

    async def parse_customer(self, request: CustomerAiParseRequest) -> dict[str, Any]:
        """
        调用 LLM 解析客户信息

        Args:
            request: 包含 text 和 images 的请求体

        Returns:
            解析后的结构化客户数据

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

        # 3. 构造 ChatOpenAI 实例
        llm_kwargs = {
            "model": config_data.get("default_model") or "gpt-4",
            "temperature": config_data.get("temperature") or 0.1,
            "max_tokens": config_data.get("max_tokens") or 4096,
            "timeout": config_data.get("timeout") or 60,
        }
        if config_data.get("api_key"):
            llm_kwargs["api_key"] = config_data["api_key"]
        if config_data.get("api_base_url"):
            llm_kwargs["base_url"] = config_data["api_base_url"]

        # 4. 如果有图片，检查模型是否支持多模态
        has_images = bool(request.images)
        model_name = llm_kwargs["model"].lower()
        # 已知不支持图片的模型
        non_vision_models = ["deepseek-chat", "deepseek-coder", "glm-4-flash", "qwen-turbo"]
        supports_vision = not any(kw in model_name for kw in non_vision_models)

        if has_images and not supports_vision:
            logger.warning(f"模型 {model_name} 不支持图片输入，将忽略图片仅使用文本")
            request = CustomerAiParseRequest(text=request.text, images=None)

        llm = ChatOpenAI(**llm_kwargs)

        # 5. 构造多模态消息
        messages = self._build_messages(request)

        # 6. 调用 LLM
        try:
            response = await llm.ainvoke(messages)
            raw_content = response.content
        except Exception as e:
            error_msg = str(e)
            logger.error(f"LLM 调用失败: {error_msg}")
            if "does not support images" in error_msg or "vision" in error_msg.lower():
                raise RuntimeError("当前模型不支持图片识别，请使用支持多模态的模型") from e
            raise RuntimeError(f"AI解析失败：{error_msg}") from e

        # 7. 解析返回的 JSON
        parsed = self._parse_llm_response(raw_content)
        if parsed is None:
            raise RuntimeError("AI解析结果格式异常，请重试或手动填写")

        # 8. 填充默认值确保结构完整
        return self._ensure_structure(parsed)

    def _build_messages(self, request: CustomerAiParseRequest) -> list:
        """构造多模态消息列表"""
        messages = [SystemMessage(content=PARSE_CUSTOMER_SYSTEM_PROMPT)]

        content_parts: list[dict[str, Any]] = []

        user_text = PARSE_CUSTOMER_USER_PROMPT
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

    def _ensure_structure(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """确保返回数据结构完整，缺失部分填充默认值"""
        result = {
            "customer": parsed.get("customer", {}) or {},
            "research_groups": parsed.get("research_groups", []) or [],
            "invoice_info": parsed.get("invoice_info", {}) or {},
            "shipping_address": parsed.get("shipping_address", {}) or {},
        }

        customer_defaults = {
            "customer_name": None,
            "customer_type": "terminal",
            "contact_person": None,
            "contact_phone": None,
            "email": None,
            "province": None,
            "city": None,
            "district": None,
            "address": None,
            "settlement_method": None,
            "remark": None,
        }
        customer = result["customer"]
        for key, default in customer_defaults.items():
            if key not in customer or customer[key] is None:
                customer[key] = default
        result["customer"] = customer

        rg_defaults = {
            "group_name": None,
            "contact_person": None,
            "contact_phone": None,
            "research_field": None,
        }
        normalized_groups = []
        for group in result["research_groups"]:
            if isinstance(group, dict):
                for key, default in rg_defaults.items():
                    if key not in group:
                        group[key] = default
                normalized_groups.append(group)
        result["research_groups"] = normalized_groups

        invoice_defaults = {
            "invoice_title": None,
            "tax_number": None,
            "bank_name": None,
            "bank_account": None,
            "address_phone": None,
        }
        invoice = result["invoice_info"]
        if isinstance(invoice, dict):
            for key, default in invoice_defaults.items():
                if key not in invoice:
                    invoice[key] = default
        else:
            result["invoice_info"] = invoice_defaults
        result["invoice_info"] = invoice

        shipping_defaults = {
            "receiver": None,
            "phone": None,
            "province": None,
            "city": None,
            "district": None,
            "address": None,
        }
        shipping = result["shipping_address"]
        if isinstance(shipping, dict):
            for key, default in shipping_defaults.items():
                if key not in shipping:
                    shipping[key] = default
        else:
            result["shipping_address"] = shipping_defaults
        result["shipping_address"] = shipping

        return result