from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Brand(BaseModel):
    id: Optional[str] = Field(None, description="品牌ID（创建时不需要，由系统自动生成）")
    name: str = Field(..., min_length=1, max_length=100, description="品牌名称")
    logo_url: Optional[str] = Field(None, max_length=500, description="品牌Logo")
    description: Optional[str] = Field(None, max_length=500, description="品牌描述")
    purchaser_id: Optional[str] = Field(None, description="采购人员ID")
    purchaser_name: Optional[str] = Field(None, description="采购人员名称（关联查询时自动填充）")
    is_active: bool = Field(default=True, description="是否有效")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间（由系统自动生成）")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间（由系统自动更新）")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "茶语轩",
                "logo_url": "https://example.com/images/brand-logo.png",
                "description": "知名茶叶品牌",
                "purchaser_id": "507f1f77bcf86cd799439012",
                "purchaser_name": "张三",
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



class Category(BaseModel):
    id: Optional[str] = Field(None, description="分类ID（创建时不需要，由系统自动生成）")   
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    parent_id: Optional[str] = Field(None, description="父类ID，为空则为顶层分类")
    tax_code: Optional[str] = Field(None, max_length=50, description="税务编码")
    sort_order: int = Field(default=0, description="排序，数字越小越靠前")
    is_shop_display: bool = Field(default=True, description="是否商城展示")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    level: int = Field(default=1, description="分类层级：1-一级 2-二级 3-三级")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "电子产品",
                "parent_id": None,
                "tax_code": "TAX001",
                "sort_order": 1,
                "is_shop_display": True,
                "level": 1,
                "created_at": "2026-04-29T10:00:00",
                "updated_at": "2026-04-29T10:00:00"
            }
        }


class ProductSpec(BaseModel):
    id: Optional[str] = Field(None, description="规格ID（创建时不需要，由系统自动生成）")
    product_id: Optional[str] = Field(None, description="商品ID（创建时不需要，由系统自动填充）")
    spec_code: str = Field(..., min_length=1, max_length=50, description="规格编号")
    packaging: Optional[str] = Field(None, max_length=100, description="包装")
    sales_spec: Optional[str] = Field(None, max_length=100, description="销售规格")
    price: float = Field(..., ge=0, description="价格")
    cas_number: Optional[str] = Field(None, max_length=50, description="CAS号")
    is_active: bool = Field(default=True, description="是否有效")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间（由系统自动生成）")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间（由系统自动更新）")
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
            }
        }


class Product(BaseModel):
    id: Optional[str] = Field(None, description="商品ID（创建时不需要，由系统自动生成）")
    product_code: Optional[str] = Field(None, max_length=50, description="商品编号（留空则自动生成）")
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    image_url: Optional[str] = Field(None, max_length=500, description="商品图片")
    brand_id: Optional[str] = Field(None, max_length=100, description="品牌ID")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    category_id: Optional[str] = Field(None, max_length=100, description="分类ID")
    category_name: Optional[str] = Field(None, description="分类名称")
    tax_code: Optional[str] = Field(None, max_length=50, description="税务编码")
    is_active: bool = Field(default=True, description="是否有效")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间（由系统自动生成）")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间（由系统自动更新）")
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
