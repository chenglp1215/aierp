from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


def parse_datetime(value):
    """解析日期时间，支持空字符串"""
    if value == "" or value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        if value.strip() == "":
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return None
    return None


class DeliveryType(str, Enum):
    INVENTORY = "inventory"
    DIRECT = "direct"


class PickupType(str, Enum):
    SELF_PICKUP = "self_pickup"
    EXPRESS = "express"


class ExpressType(str, Enum):
    SF = "sf"
    YTO = "yto"
    ZTO = "zto"
    JD = "jd"
    EMS = "ems"
    OTHER = "other"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"


class SalesOrderItem(BaseModel):
    product_id: str = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    product_code: Optional[str] = Field(None, description="商品编码")
    quantity: int = Field(..., gt=0, description="数量")
    unit_price: float = Field(..., ge=0, description="单价")
    subtotal: float = Field(..., description="小计金额")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "507f1f77bcf86cd799439012",
                "product_name": "戴尔OptiPlex 7090商用台式机",
                "product_code": "DELL-OPT-7090",
                "quantity": 10,
                "unit_price": 12800.0,
                "subtotal": 128000.0
            }
        }


class SalesOrderBase(BaseModel):
    customer_id: str = Field(..., description="客户ID")
    customer_name: str = Field(..., description="客户名称")
    receiver_name: Optional[str] = Field(None, description="收货人姓名")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    delivery_address: Optional[str] = Field(None, description="交货地址")
    order_date: Optional[datetime] = Field(default_factory=datetime.now, description="订单日期")
    expected_delivery_date: Optional[datetime] = Field(None, description="预计交货日期")
    remarks: Optional[str] = Field(None, description="备注")
    delivery_type: DeliveryType = Field(..., description="发货方式：inventory库存发货/direct采购直发")
    warehouse_id: Optional[str] = Field(None, description="发货仓库ID（库存发货时必填）")
    warehouse_name: Optional[str] = Field(None, description="发货仓库名称")
    pickup_type: PickupType = Field(..., description="自取或快递")
    express_type: Optional[ExpressType] = Field(None, description="快递方式")
    express_no: Optional[str] = Field(None, description="快递单号")
    express_fee: float = Field(default=0, ge=0, description="快递费用")
    discount_ratio: float = Field(default=100, ge=0, le=100, description="折扣比例(%)")


class SalesOrderCreate(SalesOrderBase):
    items: List[SalesOrderItem] = Field(..., description="订单明细")

    @model_validator(mode='before')
    @classmethod
    def parse_dates_before(cls, data):
        if isinstance(data, dict):
            for field in ['order_date', 'expected_delivery_date']:
                if field in data:
                    data[field] = parse_datetime(data[field])
            if data.get('express_type') == '':
                data['express_type'] = None
        return data


class SalesOrderUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    contact_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    order_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    remarks: Optional[str] = None
    delivery_type: Optional[DeliveryType] = None
    warehouse_id: Optional[str] = None
    warehouse_name: Optional[str] = None
    pickup_type: Optional[PickupType] = None
    express_type: Optional[ExpressType] = None
    express_no: Optional[str] = None
    express_fee: Optional[float] = None
    discount_ratio: Optional[float] = None
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None


class SalesOrder(SalesOrderBase):
    id: str = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单编号")
    items: List[SalesOrderItem] = Field(default=[], description="订单明细")
    total_amount: float = Field(..., description="订单总金额")
    discount_amount: float = Field(default=0, description="折扣金额")
    final_amount: float = Field(..., description="最终金额")
    status: OrderStatus = Field(default=OrderStatus.DRAFT, description="订单状态")
    payment_status: PaymentStatus = Field(default=PaymentStatus.UNPAID, description="付款状态")
    procurement_order_id: Optional[str] = Field(None, description="关联采购单ID（采购直发时）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "order_no": "SO20260416001",
                "customer_id": "507f1f77bcf86cd799439012",
                "customer_name": "深圳市腾达科技有限公司",
                "contact_phone": "13800138000",
                "delivery_address": "深圳市南山区科技园路100号",
                "order_date": "2026-04-16T10:00:00",
                "delivery_type": "inventory",
                "warehouse_id": "507f1f77bcf86cd799439020",
                "warehouse_name": "深圳中心仓",
                "pickup_type": "express",
                "express_type": "sf",
                "express_fee": 50.0,
                "discount_ratio": 95,
                "items": [],
                "total_amount": 128000.0,
                "discount_amount": 6400.0,
                "final_amount": 121600.0,
                "status": "pending",
                "payment_status": "unpaid"
            }
        }


class SalesOrderListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[SalesOrder] = Field(..., description="订单列表")
