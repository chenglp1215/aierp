from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductSpecBase(BaseModel):
    spec_code: str = Field(..., min_length=1, max_length=50, description="规格编号")
    packaging: Optional[str] = Field(None, max_length=100, description="包装")
    sales_spec: Optional[str] = Field(None, max_length=100, description="销售规格")
    price: float = Field(..., ge=0, description="价格")
    cas_number: Optional[str] = Field(None, max_length=50, description="CAS号")
    is_active: bool = Field(default=True, description="是否有效")


class ProductSpecCreate(ProductSpecBase):
    pass


class ProductSpecUpdate(BaseModel):
    spec_code: Optional[str] = Field(None, min_length=1, max_length=50)
    packaging: Optional[str] = Field(None, max_length=100)
    sales_spec: Optional[str] = Field(None, max_length=100)
    price: Optional[float] = Field(None, ge=0)
    cas_number: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class ProductSpec(ProductSpecBase):
    id: str = Field(..., description="规格ID")
    product_id: str = Field(..., description="商品ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    stock_quantity: Optional[int] = Field(0, description="库存数量")
    stock_status: Optional[str] = Field(None, description="库存状态")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439013",
                "product_id": "507f1f77bcf86cd799439012",
                "spec_code": "SPEC20260420001",
                "packaging": "100g/罐",
                "sales_spec": "100g*24罐/箱",
                "price": 128.00,
                "cas_number": "68917-21-1",
                "is_active": True,
                "stock_quantity": 500,
                "stock_status": "normal"
            }
        }


class ProductBase(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=50, description="商品编号")
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    image_url: Optional[str] = Field(None, max_length=500, description="商品图片")
    brand: Optional[str] = Field(None, max_length=100, description="品牌")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    tax_code: Optional[str] = Field(None, max_length=50, description="税务编码")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    product_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    image_url: Optional[str] = Field(None, max_length=500)
    brand: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    tax_code: Optional[str] = Field(None, max_length=50)


class Product(ProductBase):
    id: str = Field(..., description="商品ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    specs: List[ProductSpec] = Field(default_factory=list, description="商品规格列表")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "product_code": "PROD20260420001",
                "name": "有机红茶",
                "image_url": "https://example.com/images/red-tea.jpg",
                "brand": "茶语轩",
                "category": "茶叶",
                "tax_code": "TAX001",
                "created_at": "2026-04-20T10:00:00",
                "updated_at": "2026-04-20T10:00:00",
                "specs": [
                    {
                        "id": "507f1f77bcf86cd799439013",
                        "product_id": "507f1f77bcf86cd799439012",
                        "spec_code": "SPEC20260420001",
                        "packaging": "100g/罐",
                        "sales_spec": "100g*24罐/箱",
                        "price": 128.00,
                        "cas_number": "68917-21-1",
                        "is_active": True,
                        "stock_quantity": 500,
                        "stock_status": "normal"
                    }
                ]
            }
        }


class ProductListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Product] = Field(..., description="商品列表")


class ProductSpecListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[ProductSpec] = Field(..., description="规格列表")
