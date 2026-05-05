"""
供应商管理 - 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SupplierBrand(BaseModel):
    """供应商供货品牌"""
    brand_id: str = Field(..., description="品牌ID")
    discount: float = Field(default=1.0, ge=0, le=1, description="折扣率（0-1）")
    is_priority: bool = Field(default=False, description="是否优先选择")

    class Config:
        json_schema_extra = {
            "example": {
                "brand_id": "507f1f77bcf86cd799439011",
                "discount": 0.95,
                "is_priority": True
            }
        }


class BankAccount(BaseModel):
    """银行账户信息"""
    bank_name: Optional[str] = Field(None, description="开户行")
    account_name: Optional[str] = Field(None, description="账户名")
    account_no: Optional[str] = Field(None, description="账号")

    class Config:
        json_schema_extra = {
            "example": {
                "bank_name": "中国工商银行",
                "account_name": "张三",
                "account_no": "6222021234567890123"
            }
        }


class SupplierBase(BaseModel):
    """供应商基础模型"""
    name: str = Field(..., min_length=1, max_length=200, description="供应商名称")
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=200, description="联系邮箱")
    address: Optional[str] = Field(None, description="地址")
    bank_account: Optional[BankAccount] = Field(None, description="银行账户信息")
    supplied_brands: List[SupplierBrand] = Field(default_factory=list, description="供货品牌列表")
    remark: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(default=True, description="是否激活")


class SupplierCreate(SupplierBase):
    """创建供应商"""
    pass


class SupplierUpdate(BaseModel):
    """更新供应商"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="供应商名称")
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=200, description="联系邮箱")
    address: Optional[str] = Field(None, description="地址")
    bank_account: Optional[BankAccount] = Field(None, description="银行账户信息")
    supplied_brands: Optional[List[SupplierBrand]] = Field(None, description="供货品牌列表")
    remark: Optional[str] = Field(None, description="备注")
    is_active: Optional[bool] = None


class Supplier(SupplierBase):
    """供应商完整模型"""
    id: str = Field(..., description="供应商ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "某某供应商有限公司",
                "contact_person": "张三",
                "contact_phone": "13800138000",
                "contact_email": "zhangsan@example.com",
                "address": "北京市朝阳区某某街道123号",
                "bank_account": {
                    "bank_name": "中国工商银行",
                    "account_name": "某某供应商有限公司",
                    "account_no": "6222021234567890123"
                },
                "supplied_brands": [
                    {
                        "brand_id": "507f1f77bcf86cd799439011",
                        "discount": 0.95,
                        "is_priority": True
                    }
                ],
                "remark": "优质供应商",
                "is_active": True,
                "created_at": "2026-05-03T10:00:00",
                "updated_at": "2026-05-03T10:00:00"
            }
        }


class SupplierListResponse(BaseModel):
    """供应商列表响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Supplier] = Field(..., description="供应商列表")
