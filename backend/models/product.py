from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductSpecBase(BaseModel):
    product_id: Optional[str] = Field(None, description="商品ID")
    spec_code: str = Field(..., min_length=1, max_length=50, description="规格编号")
    packaging: Optional[str] = Field(None, max_length=100, description="包装")
    sales_spec: Optional[str] = Field(None, max_length=100, description="销售规格")
    price: float = Field(..., ge=0, description="价格")
    cas_number: Optional[str] = Field(None, max_length=50, description="CAS号")
    is_active: bool = Field(default=True, description="是否有效")


class ProductSpecCreate(ProductSpecBase):
    pass


class ProductSpecUpdate(BaseModel):
    id: Optional[str] = Field(None, description="规格ID，更新时必传")
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
    brand_id: Optional[str] = Field(None, max_length=100, description="品牌ID")
    category_id: Optional[str] = Field(None, max_length=100, description="分类ID")
    tax_code: Optional[str] = Field(None, max_length=50, description="税务编码")
    is_active: bool = Field(default=True, description="是否有效")


class ProductCreate(ProductBase):
    specs: Optional[List["ProductSpecCreate"]] = Field(default_factory=list, description="商品规格列表")


class ProductUpdate(BaseModel):
    product_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    image_url: Optional[str] = Field(None, max_length=500)
    brand_id: Optional[str] = Field(None, max_length=100)
    category_id: Optional[str] = Field(None, max_length=100)
    tax_code: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    specs: Optional[List["ProductSpecUpdate"]] = Field(default_factory=list, description="商品规格列表")


class Product(ProductBase):
    id: str = Field(..., description="商品ID")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    category_name: Optional[str] = Field(None, description="分类名称")
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
                "brand_id": "507f1f77bcf86cd799439011",
                "brand_name": "茶语轩",
                "category_id": "507f1f77bcf86cd799439011",
                "category_name": "茶叶",
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


class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="品牌名称")
    logo_url: Optional[str] = Field(None, max_length=500, description="品牌Logo")
    description: Optional[str] = Field(None, max_length=500, description="品牌描述")
    is_active: bool = Field(default=True, description="是否有效")


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    logo_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class Brand(BrandBase):
    id: str = Field(..., description="品牌ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "茶语轩",
                "logo_url": "https://example.com/images/brand-logo.png",
                "description": "知名茶叶品牌",
                "is_active": True,
                "created_at": "2026-05-01T10:00:00",
                "updated_at": "2026-05-01T10:00:00"
            }
        }


class BrandListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Brand] = Field(..., description="品牌列表")
