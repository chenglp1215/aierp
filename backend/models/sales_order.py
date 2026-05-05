from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from models.common import parse_datetime, SettleType, ShippingMethod  # noqa: F401 - 供外部导入


class OrderStatus(str, Enum):
    """订单状态枚举"""
    DRAFT = "draft"  # 草稿
    AUDITED = "audited"  # 已审核
    PARTIALLY_PUSHED_TO_PURCHASE = "partially_pushed_to_purchase"  # 部分下推采购
    PUSHED_TO_PURCHASE = "pushed_to_purchase"  # 已下推采购
    CLOSED = "closed"  # 已关闭
    CANCELLED = "cancelled"  # 已取消


class DeliveryStatus(str, Enum):
    """发货状态枚举"""
    NONE = "none"  # 未发货
    PARTIAL = "partial"  # 部分发货
    FULL = "full"  # 全部发货


class ReceiveStatus(str, Enum):
    """收货状态枚举"""
    NONE = "none"  # 未收货
    PARTIAL = "partial"  # 部分收货
    FULL = "full"  # 全部收货


class InvoiceStatus(str, Enum):
    """开票状态枚举"""
    NONE = "none"  # 未开票
    PARTIAL = "partial"  # 部分开票
    FULL = "full"  # 全部开票


class CostType(str, Enum):
    """成本类型枚举"""
    PRODUCT = "product"  # 商品成本
    SHIPPING = "shipping"  # 运费
    OTHER = "other"  # 其他费用


class AssociatedDocType(str, Enum):
    """关联单据类型枚举"""
    OUTBOUND_ORDER = "outbound_order"  # 出库单
    PURCHASE_ORDER = "purchase_order"  # 采购单


class CostDetail(BaseModel):
    """成本明细"""
    id: Optional[str] = Field(None, description="成本明细ID")
    cost_amount: float = Field(..., ge=0, description="成本金额")
    cost_type: CostType = Field(..., description="成本类型")
    associated_doc_type: Optional[AssociatedDocType] = Field(None, description="关联单据类型")
    associated_doc_no: Optional[str] = Field(None, description="关联单据号")
    associated_doc_id: Optional[str] = Field(None, description="关联单据ID")
    remark: Optional[str] = Field(None, description="备注")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439015",
                "cost_amount": 100.00,
                "cost_type": "shipping",
                "associated_doc_type": "outbound_order",
                "associated_doc_no": "OUT202501010001",
                "associated_doc_id": "507f1f77bcf86cd799439016",
                "remark": "运费"
            }
        }


class DeliverInfo(BaseModel):
    """发货信息"""
    addr: Optional[str] = Field(None, description="详细地址")
    province: Optional[str] = Field(None, description="省")
    city: Optional[str] = Field(None, description="市")
    person_name: Optional[str] = Field(None, description="收货人")
    person_tel: Optional[str] = Field(None, description="联系电话")


class InvoiceInfo(BaseModel):
    """开票信息"""
    invoice_title: Optional[str] = Field(None, description="公司全称")
    invoice_type: Optional[str] = Field(None, description="开票类型")
    tax_number: Optional[str] = Field(None, description="纳税人识别号")
    bank_name: Optional[str] = Field(None, description="开户行")
    bank_account: Optional[str] = Field(None, description="银行账号")


class OrderStatusInfo(BaseModel):
    """订单状态信息"""
    order_status: OrderStatus = Field(OrderStatus.DRAFT, description="订单状态")
    delivery_status: DeliveryStatus = Field(DeliveryStatus.NONE, description="发货状态")
    receive_status: ReceiveStatus = Field(ReceiveStatus.NONE, description="收货状态")
    invoice_status: InvoiceStatus = Field(InvoiceStatus.NONE, description="开票状态")


class StatusFlowRecord(BaseModel):
    """状态流转记录"""
    id: Optional[str] = Field(None, description="记录ID")
    order_no: str = Field(..., description="订单号")
    field: str = Field(..., description="状态字段名")
    old_value: Optional[str] = Field(None, description="旧值")
    new_value: str = Field(..., description="新值")
    operator: str = Field(default="system", description="操作人")
    operate_time: str = Field(..., description="操作时间")
    remark: Optional[str] = Field(None, description="备注")


class OrderStatusUpdate(BaseModel):
    """订单状态更新请求"""
    status: str = Field(..., description="订单状态")


class DeliveryStatusUpdate(BaseModel):
    """发货状态更新请求"""
    delivery_status: str = Field(..., description="发货状态")


class ReceiveStatusUpdate(BaseModel):
    """收货状态更新请求"""
    receive_status: str = Field(..., description="收货状态")


class InvoiceStatusUpdate(BaseModel):
    """开票状态更新请求"""
    invoice_status: str = Field(..., description="开票状态")


class StatusFlowRecordCreate(BaseModel):
    """创建状态流转记录"""
    order_no: str = Field(..., description="订单号")
    field: str = Field(..., description="状态字段名")
    old_value: Optional[str] = Field(None, description="旧值")
    new_value: str = Field(..., description="新值")
    operator: str = Field(default="system", description="操作人")
    remark: Optional[str] = Field(None, description="备注")


class StatusFlowRecordListResponse(BaseModel):
    """流转记录列表响应"""
    total: int = Field(..., description="总记录数")
    items: List[StatusFlowRecord] = Field(..., description="流转记录列表")


class SalesOrderItem(BaseModel):
    """销售订单明细"""
    row_no: int = Field(..., description="行号")
    product_id: str = Field(..., description="商品ID")
    spec_id: Optional[str] = Field(None, description="规格ID")
    brand_id: Optional[str] = Field(None, description="品牌ID")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    qty: int = Field(..., gt=0, description="订购数量")
    price: float = Field(..., ge=0, description="原始单价")
    discount: float = Field(..., ge=0, le=1, description="折扣率")
    discounted_price: Optional[float] = Field(None, ge=0, description="折后单价")
    amt: Optional[float] = Field(None, description="行金额")
    warehouse_id: Optional[str] = Field(None, description="仓库ID")
    shipping_method: ShippingMethod = Field(..., description="发货方式")
    out_qty: int = Field(default=0, description="已发货数量")
    return_qty: int = Field(default=0, description="已退货数量")
    remain_out_qty: Optional[int] = Field(None, description="剩余可发数量")
    pushed: bool = Field(default=False, description="是否已下推采购")

    class Config:
        json_schema_extra = {
            "example": {
                "row_no": 1,
                "product_id": "507f1f77bcf86cd799439012",
                "spec_id": "507f1f77bcf86cd799439013",
                "brand_id": "507f1f77bcf86cd799439014",
                "brand_name": "品牌名称",
                "qty": 2,
                "price": 5000,
                "discount": 0.8,
                "discounted_price": 4000,
                "amt": 8000,
                "warehouse_id": "507f1f77bcf86cd799439020",
                "shipping_method": "直运",
                "out_qty": 0,
                "return_qty": 0,
                "remain_out_qty": 2
            }
        }


class SalesOrderBase(BaseModel):
    """销售订单基础模型"""
    order_no: str = Field(..., description="订单号")
    order_date: str = Field(..., description="订单日期")
    customer_id: str = Field(..., description="客户ID")
    sale_user_id: Optional[str] = Field(None, description="销售人员ID")
    deliver_info: Optional[DeliverInfo] = Field(None, description="发货信息")
    expect_deliver_date: Optional[str] = Field(None, description="期望交货日")
    settle_type: SettleType = Field(..., description="结算方式")
    total_amt: float = Field(..., description="商品总金额（未税）")
    tax_rate: float = Field(..., description="税率")
    tax_amt: float = Field(..., description="税额")
    total_tax_amt: float = Field(..., description="含税总金额")
    total_discount_amt: float = Field(default=0.0, description="整单折扣金额")
    status: OrderStatusInfo = Field(default_factory=OrderStatusInfo, description="订单状态信息")
    invoice_info: Optional[InvoiceInfo] = Field(None, description="开票信息")
    creator_id: str = Field(..., description="创建人ID")
    create_time: str = Field(..., description="创建时间")
    remark: Optional[str] = Field(None, description="备注")
    total_out_qty: int = Field(default=0, description="累计已出库数量")
    total_received_amt: float = Field(default=0.0, description="累计已收款金额")
    total_invoice_amt: float = Field(default=0.0, description="累计已开票金额")
    total_return_qty: int = Field(default=0, description="累计退货数量")
    total_return_amt: float = Field(default=0.0, description="累计退货金额")
    items: List[SalesOrderItem] = Field(..., description="商品明细")
    cost_details: List[CostDetail] = Field(default_factory=list, description="成本明细")


class SalesOrderCreate(BaseModel):
    """创建销售订单 - 独立定义，不继承SalesOrderBase"""
    order_date: str = Field(..., description="订单日期")
    customer_id: str = Field(..., description="客户ID")
    sale_user_id: Optional[str] = Field(None, description="销售人员ID")
    deliver_info: Optional[DeliverInfo] = Field(None, description="发货信息")
    expect_deliver_date: Optional[str] = Field(None, description="期望交货日")
    settle_type: str = Field(..., description="结算方式")
    tax_rate: Optional[float] = Field(0.13, description="税率，默认0.13（13%）")
    invoice_info: Optional[InvoiceInfo] = Field(None, description="开票信息")
    remark: Optional[str] = Field(None, description="备注")
    items: List[SalesOrderItem] = Field(..., description="商品明细")
    cost_details: List[CostDetail] = Field(default_factory=list, description="成本明细")

    # 以下字段由系统自动生成，不需要传入
    id: Optional[str] = Field(None, description="订单ID")

    @model_validator(mode='before')
    @classmethod
    def parse_dates_before(cls, data):
        if isinstance(data, dict):
            for field in ['order_date', 'expect_deliver_date']:
                if field in data and data[field]:
                    data[field] = parse_datetime(data[field])
                    if data[field]:
                        data[field] = data[field].strftime("%Y-%m-%d")
        return data


class SalesOrderUpdate(BaseModel):
    """更新销售订单"""
    order_date: Optional[str] = Field(None, description="订单日期")
    customer_id: Optional[str] = Field(None, description="客户ID")
    sale_user_id: Optional[str] = Field(None, description="销售人员ID")
    deliver_info: Optional[DeliverInfo] = Field(None, description="发货信息")
    expect_deliver_date: Optional[str] = Field(None, description="期望交货日")
    settle_type: Optional[str] = Field(None, description="结算方式")
    tax_rate: Optional[float] = Field(None, description="税率")
    invoice_info: Optional[InvoiceInfo] = Field(None, description="开票信息")
    remark: Optional[str] = Field(None, description="备注")
    items: Optional[List[SalesOrderItem]] = Field(None, description="商品明细")
    cost_details: Optional[List[CostDetail]] = Field(None, description="成本明细")

    @model_validator(mode='before')
    @classmethod
    def parse_dates_before(cls, data):
        if isinstance(data, dict):
            for field in ['order_date', 'expect_deliver_date']:
                if field in data and data[field]:
                    data[field] = parse_datetime(data[field])
                    if data[field]:
                        data[field] = data[field].strftime("%Y-%m-%d")
        return data


class SalesOrder(SalesOrderBase):
    """销售订单完整模型"""
    id: str = Field(..., description="订单ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "order_no": "SO202501010001",
                "order_date": "2025-01-01",
                "customer_id": "507f1f77bcf86cd799439012",
                "sale_user_id": "507f1f77bcf86cd799439013",
                "deliver_info": {
                    "addr": "详细地址",
                    "province": "省",
                    "city": "市",
                    "person_name": "收货人",
                    "person_tel": "联系电话"
                },
                "expect_deliver_date": "2025-01-10",
                "settle_type": "月结",
                "total_amt": 10000.00,
                "tax_rate": 0.13,
                "tax_amt": 1300.00,
                "total_tax_amt": 11300.00,
                "total_discount_amt": 0.00,
                "status": {
                    "order_status": "audited",
                    "delivery_status": "none",
                    "receive_status": "none",
                    "invoice_status": "none"
                },
                "invoice_info": {
                    "invoice_title": "公司全称",
                    "tax_number": "纳税人识别号",
                    "bank_name": "开户行",
                    "bank_account": "银行账号"
                },
                "creator_id": "507f1f77bcf86cd799439014",
                "create_time": "2025-01-01 10:00:00",
                "remark": "急单",
                "total_out_qty": 0,
                "total_received_amt": 0.00,
                "total_invoice_amt": 0.00,
                "total_return_qty": 0,
                "total_return_amt": 0.00,
                "items": [
                    {
                        "row_no": 1,
                        "product_id": "507f1f77bcf86cd799439012",
                        "spec_id": "507f1f77bcf86cd799439013",
                        "qty": 2,
                        "price": 5000,
                        "discount": 0.8,
                        "discounted_price": 4000,
                        "amt": 8000,
                        "warehouse_id": "507f1f77bcf86cd799439020",
                        "shipping_method": "直运",
                        "out_qty": 0,
                        "return_qty": 0,
                        "remain_out_qty": 2
                    }
                ]
            }
        }


class SalesOrderListResponse(BaseModel):
    """销售订单列表响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[SalesOrder] = Field(..., description="订单列表")