from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    parent_id: Optional[str] = Field(None, description="父类ID，为空则为顶层分类")
    tax_code: Optional[str] = Field(None, max_length=50, description="税务编码")
    sort_order: int = Field(default=0, description="排序，数字越小越靠前")
    is_shop_display: bool = Field(default=True, description="是否商城展示")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    parent_id: Optional[str] = Field(None, description="父类ID，为空则为顶层分类")
    tax_code: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = Field(None)
    is_shop_display: Optional[bool] = None


class Category(CategoryBase):
    id: str = Field(..., description="分类ID")
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


class CategoryTreeNode(BaseModel):
    id: str = Field(..., description="分类ID")
    name: str = Field(..., description="分类名称")
    parent_id: Optional[str] = Field(None, description="父类ID")
    tax_code: Optional[str] = Field(None, description="税务编码")
    sort_order: int = Field(..., description="排序")
    is_shop_display: bool = Field(..., description="是否商城展示")
    level: int = Field(..., description="分类层级")
    children: List["CategoryTreeNode"] = Field(default_factory=list, description="子分类")

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
                "children": []
            }
        }


class CategoryListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Category] = Field(..., description="分类列表")


CategoryTreeNode.model_rebuild()
