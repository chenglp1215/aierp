"""
客户折扣管理 - 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CustomerDiscountCreate(BaseModel):
    """创建客户折扣"""
    customer_id: str = Field(..., description="客户ID（必填）")
    brand_id: str = Field(..., description="品牌ID（必填）")
    discount_value: float = Field(..., ge=0, le=1, description="折扣值（0-1之间，如0.85表示85折）")
    is_active: bool = Field(default=True, description="是否生效")


class CustomerDiscountUpdate(BaseModel):
    """更新客户折扣"""
    discount_value: Optional[float] = Field(None, ge=0, le=1, description="折扣值（0-1之间）")
    is_active: Optional[bool] = Field(None, description="是否生效")


class CustomerDiscount(BaseModel):
    """客户折扣完整信息"""
    id: str = Field(..., description="折扣记录ID")
    customer_id: str = Field(..., description="客户ID")
    brand_id: str = Field(..., description="品牌ID")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    discount_value: float = Field(..., description="折扣值")
    is_active: bool = Field(default=True, description="是否生效")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "DIS001",
                "customer_id": "64a1b2c3d4e5f6a7b8c9d0e1",
                "brand_id": "brand001",
                "brand_name": "品牌A",
                "discount_value": 0.85,
                "is_active": True,
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z"
            }
        }


class CustomerDiscountListResponse(BaseModel):
    """客户折扣列表响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[CustomerDiscount] = Field(..., description="客户折扣列表")


class CustomerDiscountSimple(BaseModel):
    """客户折扣简单信息"""
    id: str = Field(..., description="折扣记录ID")
    customer_id: str = Field(..., description="客户ID")
    brand_id: str = Field(..., description="品牌ID")
    discount_value: float = Field(..., description="折扣值")
    is_active: bool = Field(default=True, description="是否生效")
