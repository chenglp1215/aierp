from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProductBase(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=50, description="商品编号")
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    price: float = Field(..., ge=0, description="商品价格")
    packaging_spec: Optional[str] = Field(None, max_length=100, description="商品包装规格")
    brand: Optional[str] = Field(None, max_length=100, description="品牌")
    description: Optional[str] = Field(None, description="简介")
    image_url: Optional[str] = Field(None, max_length=500, description="图片URL")
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="商品状态")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, ge=0)
    packaging_spec: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[ProductStatus] = None


class Product(ProductBase):
    id: str = Field(..., description="商品ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "product_code": "PROD20260420001",
                "name": "有机红茶",
                "price": 128.00,
                "packaging_spec": "100g/罐",
                "brand": "茶语轩",
                "description": "精选有机茶叶，传统工艺制作",
                "image_url": "https://example.com/images/red-tea.jpg",
                "status": "active"
            }
        }


class ProductListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Product] = Field(..., description="商品列表")
