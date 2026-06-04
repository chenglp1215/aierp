"""收货地址 AI 智能解析服务"""
import json
import re
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.routers.prompts.shipping_address import (
    SHIPPING_ADDRESS_AI_PARSE_SYSTEM_PROMPT,
    SHIPPING_ADDRESS_AI_PARSE_USER_PROMPT,
)
from services.ai_service_mysql import LlmConfigService
from validators.shipping_address_ai_parse_validator import ShippingAddressAiParseRequest

logger = logging.getLogger(__name__)


class ShippingAddressAiParseService:
    """收货地址 AI 解析服务"""

    async def parse_shipping_address(self, request: ShippingAddressAiParseRequest) -> dict[str, Any]:
        """
        调用 LLM 解析收货地址信息

        Args:
            request: 包含 text 和 images 的请求体

        Returns:
            解析后的结构化地址数据 {receiver, phone, province, city, district, address}

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
            "max_tokens": config_data.get("max_tokens") or 1024,
            "timeout": config_data.get("timeout") or 60,
        }
        if config_data.get("api_key"):
            llm_kwargs["api_key"] = config_data["api_key"]
        if config_data.get("api_base_url"):
            llm_kwargs["base_url"] = config_data["api_base_url"]

        # 4. 检查模型是否支持多模态
        has_images = bool(request.images)
        model_name = llm_kwargs["model"].lower()
        non_vision_models = ["deepseek-chat", "deepseek-coder", "glm-4-flash", "qwen-turbo"]
        supports_vision = not any(kw in model_name for kw in non_vision_models)

        if has_images and not supports_vision:
            logger.warning(f"模型 {model_name} 不支持图片输入，将忽略图片仅使用文本")
            request = ShippingAddressAiParseRequest(text=request.text, images=None)

        # 5. 创建 LLM
        llm = ChatOpenAI(**llm_kwargs)

        # 6. 构造消息
        messages = self._build_messages(request)

        # 7. 调用 LLM
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await llm.ainvoke(messages)
                raw_content = response.content

                # 尝试解析 JSON
                parsed = self._parse_llm_response(raw_content)
                if parsed is None:
                    # JSON 解析失败，要求重新输出
                    logger.warning(f"JSON 解析失败 (attempt {attempt + 1}): {raw_content[:200]}")
                    messages.append(response)
                    messages.append(HumanMessage(content="你的输出不是有效的 JSON 格式。请重新输出完整的 JSON 对象，不要包含任何注释或额外文本。"))
                    continue

                # 校验并清洗结果
                result = self._sanitize_result(parsed)
                return result

            except Exception as e:
                error_msg = str(e)
                logger.error(f"LLM 调用失败 (attempt {attempt + 1}): {error_msg}")
                if "does not support images" in error_msg or "vision" in error_msg.lower():
                    raise RuntimeError("当前模型不支持图片识别，请使用支持多模态的模型") from e
                if attempt == max_retries - 1:
                    raise RuntimeError(f"AI解析失败：{error_msg}") from e

        raise RuntimeError("AI 解析超时，请简化输入后重试")

    def _build_messages(self, request: ShippingAddressAiParseRequest) -> list:
        """构造消息列表"""
        messages = [SystemMessage(content=SHIPPING_ADDRESS_AI_PARSE_SYSTEM_PROMPT)]

        content_parts: list[dict[str, Any]] = []

        user_text = SHIPPING_ADDRESS_AI_PARSE_USER_PROMPT
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
        """检测图片 MIME 类型"""
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
        """解析 LLM 返回的 JSON"""
        if not raw_content:
            return None

        # 尝试直接解析
        try:
            result = json.loads(raw_content)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # 尝试从代码块提取
        json_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        matches = re.findall(json_block_pattern, raw_content, re.DOTALL)
        for match in matches:
            try:
                result = json.loads(match.strip())
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                continue

        # 尝试提取第一个 { 到最后一个 }
        first_brace = raw_content.find("{")
        last_brace = raw_content.rfind("}")
        if first_brace != -1 and last_brace > first_brace:
            try:
                result = json.loads(raw_content[first_brace:last_brace + 1])
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        return None

    def _sanitize_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        """清洗解析结果"""
        defaults = {
            "receiver": None,
            "phone": None,
            "province": None,
            "city": None,
            "district": None,
            "address": None,
        }

        result = {}
        for key, default in defaults.items():
            value = raw.get(key)
            if value is not None:
                value = str(value).strip()
                if value.lower() == "null" or value == "":
                    value = None
            result[key] = value if value is not None else default

        return result


# 服务实例
shipping_address_ai_parse_service = ShippingAddressAiParseService()
