"""
客户管理 - 数据模型
全新设计，包含客户基础属性、联系人、财务信息、收货信息等
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============ 枚举定义 ============

class CustomerType(str, Enum):
    """客户类型枚举"""
    TERMINAL = "terminal"      # 终端
    DEALER = "dealer"         # 经销商


class CustomerStatus(str, Enum):
    """客户状态枚举"""
    NORMAL = "normal"         # 正常
    INACTIVE = "inactive"     # 未激活
    BLACKLISTED = "blacklisted"  # 黑名单


# ============ 财务信息模型 ============

class InvoiceType(str, Enum):
    """开票类型枚举"""
    VAT = "增值税"
    ORDINARY = "普通发票"
    SPECIAL_VAT = "增值税专用发票"
    NO_INVOICE = "不开票"


class InvoiceInfo(BaseModel):
    """开票信息（财务信息）"""
    id: Optional[str] = Field(None, description="开票信息ID")
    invoice_title: str = Field(..., min_length=1, max_length=200, description="开票抬头")
    invoice_type: str = Field(..., min_length=1, max_length=50, description="开票类型")
    tax_number: str = Field(..., min_length=1, max_length=50, description="税务编码")
    bank_name: str = Field(..., min_length=1, max_length=200, description="银行开户行")
    bank_account: str = Field(..., min_length=1, max_length=50, description="银行账号")
    is_default: bool = Field(default=False, description="是否为默认开票信息")


class InvoiceInfoCreate(BaseModel):
    """创建开票信息"""
    invoice_title: str = Field(..., min_length=1, max_length=200, description="开票抬头")
    invoice_type: str = Field(..., min_length=1, max_length=50, description="开票类型")
    tax_number: str = Field(..., min_length=1, max_length=50, description="税务编码")
    bank_name: str = Field(..., min_length=1, max_length=200, description="银行开户行")
    bank_account: str = Field(..., min_length=1, max_length=50, description="银行账号")
    is_default: bool = Field(default=False, description="是否为默认开票信息")


class InvoiceInfoUpdate(BaseModel):
    """更新开票信息"""
    invoice_title: Optional[str] = Field(None, min_length=1, max_length=200)
    invoice_type: Optional[str] = Field(None, min_length=1, max_length=50)
    tax_number: Optional[str] = Field(None, min_length=1, max_length=50)
    bank_name: Optional[str] = Field(None, min_length=1, max_length=200)
    bank_account: Optional[str] = Field(None, min_length=1, max_length=50)
    is_default: Optional[bool] = None


# ============ 收货信息模型 ============

class ShippingAddress(BaseModel):
    """收货地址"""
    id: Optional[str] = Field(None, description="收货地址ID")
    recipient_name: str = Field(..., min_length=1, max_length=100, description="收货人")
    recipient_phone: str = Field(..., min_length=1, max_length=20, description="收货电话")
    province: str = Field(..., min_length=1, max_length=100, description="收货省份")
    province_code: Optional[str] = Field(None, max_length=20, description="省份代码")
    city: str = Field(..., min_length=1, max_length=100, description="城市")
    city_code: Optional[str] = Field(None, max_length=20, description="城市代码")
    district: Optional[str] = Field(None, max_length=100, description="区县")
    address: str = Field(..., min_length=1, max_length=500, description="详细地址")
    is_default: bool = Field(default=False, description="是否为默认收货地址")


class ShippingAddressCreate(BaseModel):
    """创建收货地址"""
    recipient_name: str = Field(..., min_length=1, max_length=100, description="收货人")
    recipient_phone: str = Field(..., min_length=1, max_length=20, description="收货电话")
    province: str = Field(..., min_length=1, max_length=100, description="收货省份")
    province_code: Optional[str] = Field(None, max_length=20, description="省份代码")
    city: str = Field(..., min_length=1, max_length=100, description="城市")
    city_code: Optional[str] = Field(None, max_length=20, description="城市代码")
    district: Optional[str] = Field(None, max_length=100, description="区县")
    address: str = Field(..., min_length=1, max_length=500, description="详细地址")
    is_default: bool = Field(default=False, description="是否为默认收货地址")


class ShippingAddressUpdate(BaseModel):
    """更新收货地址"""
    recipient_name: Optional[str] = Field(None, min_length=1, max_length=100)
    recipient_phone: Optional[str] = Field(None, min_length=1, max_length=20)
    province: Optional[str] = Field(None, min_length=1, max_length=100)
    province_code: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    city_code: Optional[str] = Field(None, max_length=20)
    district: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    is_default: Optional[bool] = None


# ============ 联系人信息模型 ============

class ContactInfo(BaseModel):
    """联系人信息"""
    contact_person: Optional[str] = Field(None, max_length=100, description="联系人")
    contact_phone: Optional[str] = Field(None, max_length=20, description="联系电话")
    contact_email: Optional[str] = Field(None, max_length=100, description="电子邮箱")


class ContactInfoCreate(BaseModel):
    """创建联系人信息"""
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)


class ContactInfoUpdate(BaseModel):
    """更新联系人信息"""
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)


# ============ 客户主模型 ============

class CustomerBase(BaseModel):
    """客户基础属性"""
    name: str = Field(..., min_length=1, max_length=200, description="客户名称（必填）")
    customer_type: CustomerType = Field(..., description="客户类型（必填）：terminal-终端, dealer-经销商")
    research_group: Optional[str] = Field(None, max_length=200, description="课题组信息（终端客户时填写）")
    contact_info: Optional[ContactInfo] = Field(default_factory=ContactInfo, description="联系人信息")
    sales_user_id: Optional[str] = Field(None, description="销售人ID")
    sales_user_name: Optional[str] = Field(None, max_length=100, description="销售人名称")


class CustomerCreate(BaseModel):
    """创建客户"""
    name: str = Field(..., min_length=1, max_length=200, description="客户名称（必填）")
    customer_type: CustomerType = Field(..., description="客户类型（必填）：terminal-终端, dealer-经销商")
    research_group: Optional[str] = Field(None, max_length=200, description="课题组信息（终端客户时填写）")
    contact_info: Optional[ContactInfo] = Field(default_factory=ContactInfo, description="联系人信息")
    invoice_infos: List[InvoiceInfoCreate] = Field(default_factory=list, description="开票信息列表")
    shipping_addresses: List[ShippingAddressCreate] = Field(default_factory=list, description="收货地址列表")


class CustomerUpdate(BaseModel):
    """更新客户"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_type: Optional[CustomerType] = None
    research_group: Optional[str] = Field(None, max_length=200)
    contact_info: Optional[ContactInfoUpdate] = None


class Customer(CustomerBase):
    """客户完整信息"""
    id: str = Field(..., description="客户ID")
    customer_code: str = Field(..., description="客户编码")
    status: CustomerStatus = Field(default=CustomerStatus.NORMAL, description="客户状态")
    invoice_infos: List[InvoiceInfo] = Field(default_factory=list, description="开票信息列表")
    shipping_addresses: List[ShippingAddress] = Field(default_factory=list, description="收货地址列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "customer_code": "CUST20260501001",
                "name": "深圳市腾达科技有限公司",
                "customer_type": "terminal",
                "research_group": "张教授课题组",
                "status": "normal",
                "contact_info": {
                    "contact_person": "张三",
                    "contact_phone": "13800138000",
                    "contact_email": "zhangsan@example.com"
                },
                "sales_user_id": "user001",
                "sales_user_name": "李经理",
                "invoice_infos": [
                    {
                        "id": "INV001",
                        "invoice_title": "深圳市腾达科技有限公司",
                        "tax_number": "91440300MA5DXXXXX",
                        "bank_name": "中国工商银行深圳分行",
                        "bank_account": "4000123456789012345",
                        "is_default": True
                    }
                ],
                "shipping_addresses": [
                    {
                        "id": "ADDR001",
                        "recipient_name": "李四",
                        "recipient_phone": "13900139000",
                        "province": "广东省",
                        "province_code": "440000",
                        "city": "深圳市",
                        "city_code": "440300",
                        "district": "南山区",
                        "address": "科技园路100号A栋1001室",
                        "is_default": True
                    }
                ],
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z"
            }
        }


class CustomerListResponse(BaseModel):
    """客户列表响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Customer] = Field(..., description="客户列表")


class CustomerSimple(BaseModel):
    """客户简单信息（用于下拉选择等场景）"""
    id: str = Field(..., description="客户ID")
    customer_code: str = Field(..., description="客户编码")
    name: str = Field(..., description="客户名称")
    customer_type: CustomerType = Field(..., description="客户类型")
    contact_phone: Optional[str] = Field(None, description="联系电话")


# ============ 销售人模型 ============

class SalesUser(BaseModel):
    """销售员信息"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    full_name: str = Field(..., description="姓名")
    department: Optional[str] = Field(None, description="部门")
    is_active: bool = Field(default=True, description="是否在职")


class CustomerTransferRequest(BaseModel):
    """客户转移请求"""
    new_sales_user_id: str = Field(..., description="新销售员ID")
