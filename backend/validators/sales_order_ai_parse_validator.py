"""AI 智能销售订单解析请求校验器"""
from typing import Optional
from pydantic import BaseModel, field_validator

# 单张图片最大 5MB（base64 编码后约为原始大小的 1.37 倍）
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_BASE64_LENGTH = int(MAX_IMAGE_SIZE_BYTES * 1.37)
MAX_IMAGES_COUNT = 3
MAX_TEXT_LENGTH = 5000


class SalesOrderAiParseRequest(BaseModel):
    """AI 销售订单解析请求体"""
    text: Optional[str] = None
    images: Optional[list[str]] = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"文本描述不能超过{MAX_TEXT_LENGTH}字符")
        return v

    @field_validator("images")
    @classmethod
    def validate_images(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None and len(v) > MAX_IMAGES_COUNT:
            raise ValueError(f"最多支持{MAX_IMAGES_COUNT}张图片")
        if v is not None:
            for i, img in enumerate(v):
                if len(img) > MAX_IMAGE_BASE64_LENGTH:
                    raise ValueError(f"第{i + 1}张图片超过5MB限制")
        return v

    def has_input(self) -> bool:
        """检查是否至少提供了 text 或 images"""
        return bool(self.text and self.text.strip()) or bool(self.images and len(self.images) > 0)
