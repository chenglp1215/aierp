from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"
    GOVERNMENT = "government"


class CustomerLevel(str, Enum):
    VIP = "vip"
    NORMAL = "normal"
    POTENTIAL = "potential"


class CustomerStatus(str, Enum):
    BLACKLISTED = "blacklisted"
    NORMAL = "normal"
    INACTIVE = "inactive"


class ShippingAddress(BaseModel):
    id: Optional[str] = Field(None, description="地址ID")
    recipient_name: str = Field(..., min_length=1, max_length=100, description="收货人姓名")
    recipient_phone: str = Field(..., min_length=1, max_length=20, description="收货人电话")
    province: Optional[str] = Field(None, max_length=100, description="省份")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    district: Optional[str] = Field(None, max_length=100, description="区县")
    address: str = Field(..., min_length=1, max_length=500, description="详细地址")
    is_default: bool = Field(default=False, description="是否为默认地址")
    remarks: Optional[str] = Field(None, description="备注")


class ShippingAddressCreate(BaseModel):
    recipient_name: str = Field(..., min_length=1, max_length=100, description="收货人姓名")
    recipient_phone: str = Field(..., min_length=1, max_length=20, description="收货人电话")
    province: Optional[str] = Field(None, max_length=100, description="省份")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    district: Optional[str] = Field(None, max_length=100, description="区县")
    address: str = Field(..., min_length=1, max_length=500, description="详细地址")
    is_default: bool = Field(default=False, description="是否为默认地址")
    remarks: Optional[str] = Field(None, description="备注")


class ShippingAddressUpdate(BaseModel):
    recipient_name: Optional[str] = Field(None, min_length=1, max_length=100)
    recipient_phone: Optional[str] = Field(None, min_length=1, max_length=20)
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    is_default: Optional[bool] = None
    remarks: Optional[str] = None


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="客户名称")
    customer_type: CustomerType = Field(default=CustomerType.COMPANY, description="客户类型")
    level: CustomerLevel = Field(default=CustomerLevel.NORMAL, description="客户级别")
    status: CustomerStatus = Field(default=CustomerStatus.NORMAL, description="客户状态")

    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, description="电子邮箱")

    address: Optional[str] = Field(None, max_length=500, description="地址")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    province: Optional[str] = Field(None, max_length=100, description="省份")

    industry: Optional[str] = Field(None, max_length=100, description="行业")
    tax_number: Optional[str] = Field(None, max_length=50, description="税号")
    bank_name: Optional[str] = Field(None, max_length=200, description="开户银行")
    bank_account: Optional[str] = Field(None, max_length=50, description="银行账号")

    credit_limit: float = Field(default=0, ge=0, description="信用额度")
    remarks: Optional[str] = Field(None, description="备注")


class CustomerCreate(CustomerBase):
    shipping_addresses: List[ShippingAddressCreate] = Field(default_factory=list, description="收货地址列表")


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_type: Optional[CustomerType] = None
    level: Optional[CustomerLevel] = None
    status: Optional[CustomerStatus] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    industry: Optional[str] = None
    tax_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    credit_limit: Optional[float] = None
    remarks: Optional[str] = None


class Customer(CustomerBase):
    id: str = Field(..., description="客户ID")
    customer_code: str = Field(..., description="客户编码")
    shipping_addresses: List[ShippingAddress] = Field(default_factory=list, description="收货地址列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "customer_code": "CUST20260416001",
                "name": "深圳市腾达科技有限公司",
                "customer_type": "company",
                "level": "vip",
                "status": "normal",
                "contact_person": "张三",
                "contact_phone": "13800138000",
                "contact_email": "zhangsan@example.com",
                "address": "深圳市南山区科技园路100号",
                "city": "深圳市",
                "province": "广东省",
                "industry": "科技",
                "credit_limit": 500000.0,
                "shipping_addresses": [
                    {
                        "id": "addr001",
                        "recipient_name": "李四",
                        "recipient_phone": "13900139000",
                        "province": "广东省",
                        "city": "深圳市",
                        "district": "南山区",
                        "address": "科技园路100号A栋1001室",
                        "is_default": True
                    }
                ]
            }
        }


class CustomerListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Customer] = Field(..., description="客户列表")
