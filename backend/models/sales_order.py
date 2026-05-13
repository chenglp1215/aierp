from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from models.common import SettleType, ShippingMethod  # noqa: F401 - 供外部导入


class OrderStatus(str, Enum):
    """订单状态枚举"""
    DRAFT = "draft"
    AUDITED = "audited"
    PARTIALLY_PUSHED_TO_PURCHASE = "partially_pushed_to_purchase"
    PUSHED_TO_PURCHASE = "pushed_to_purchase"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    """发货状态枚举"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class ReceiveStatus(str, Enum):
    """收货状态枚举"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class InvoiceStatus(str, Enum):
    """开票状态枚举"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class CostType(str, Enum):
    """成本类型枚举"""
    PRODUCT = "product"
    SHIPPING = "shipping"
    OTHER = "other"


class AssociatedDocType(str, Enum):
    """关联单据类型枚举"""
    OUTBOUND_ORDER = "outbound_order"
    PURCHASE_ORDER = "purchase_order"


# ============ 嵌套子模型 ============

class CostDetail(BaseModel):
    """成本明细"""
    id: Optional[str] = Field(None, description="成本明细ID")
    cost_amount: float = Field(..., ge=0, description="成本金额")
    cost_type: CostType = Field(..., description="成本类型")
    associated_doc_type: Optional[AssociatedDocType] = Field(None, description="关联单据类型")
    associated_doc_no: Optional[str] = Field(None, description="关联单据号")
    associated_doc_id: Optional[str] = Field(None, description="关联单据ID")
    remark: Optional[str] = Field(None, description="备注")


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


# ============ 数据库集合模型 ============

class SalesOrderItem(BaseModel):
    """销售订单明细"""
    row_no: int = Field(..., description="行号")
    product_code: Optional[str] = Field(None, description="商品编码")
    product_name: Optional[str] = Field(None, description="商品名称")
    brand_id: Optional[str] = Field(None, description="品牌ID")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    spec_code: Optional[str] = Field(None, description="规格编码")
    qty: int = Field(..., gt=0, description="订购数量")
    price: float = Field(..., ge=0, description="原始单价")
    discount: float = Field(..., ge=0, le=1, description="折扣率")
    discounted_price: Optional[float] = Field(None, ge=0, description="折后单价")
    amt: Optional[float] = Field(None, description="行金额")
    warehouse_id: Optional[str] = Field(None, description="仓库ID")
    warehouse_name: Optional[str] = Field(None, description="仓库名称")
    shipping_method: ShippingMethod = Field(..., description="发货方式")
    out_qty: int = Field(default=0, description="已发货数量")
    return_qty: int = Field(default=0, description="已退货数量")
    remain_out_qty: Optional[int] = Field(None, description="剩余可发数量")
    pushed: bool = Field(default=False, description="是否已下推采购")


class SalesOrderBase(BaseModel):
    """销售订单基础模型"""
    order_no: str = Field(..., description="订单号")
    order_date: str = Field(..., description="订单日期")
    customer_id: str = Field(..., description="客户ID")
    customer_name: Optional[str] = Field(None, description="客户名称")
    sale_user_id: Optional[str] = Field(None, description="销售人员ID")
    sale_user_name: Optional[str] = Field(None, description="销售人员名称")
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


class SalesOrder(SalesOrderBase):
    """销售订单完整模型（含数据库ID）"""
    id: str = Field(..., description="订单ID")


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


# ============ 请求参数模型（保留供 AI Agent 工具使用） ============

class SalesOrderCreate(BaseModel):
    """创建销售订单 - 供 AI Agent 工具使用，路由层使用 Dict[str, Any]"""
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
    id: Optional[str] = Field(None, description="订单ID")


class SalesOrderUpdate(BaseModel):
    """更新销售订单 - 供 AI Agent 工具使用，路由层使用 Dict[str, Any]"""
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
