"""收货地址 AI 解析请求验证器"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ShippingAddressAiParseRequest(BaseModel):
    """收货地址 AI 解析请求"""
    text: Optional[str] = Field(None, description="文本描述（如：张三 13800138000 北京市海淀区中关村大街1号）")
    images: Optional[List[str]] = Field(None, description="图片 base64 数组（不含 data:image/xxx;base64, 前缀）")

    def has_input(self) -> bool:
        """检查是否有输入"""
        return bool(self.text and self.text.strip()) or bool(self.images and len(self.images) > 0)