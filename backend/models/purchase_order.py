"""
采购单 - 数据模型
销售订单审核后自动拆解生成采购单，支持直运采购和仓库采购
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from models.common import parse_datetime, SettleType, ShippingMethod  # noqa: F401 - 供外部导入


class PurchaseType(str, Enum):
    """采购类型"""
    DIRECT = "direct"  # 直运采购
    WAREHOUSE = "warehouse"  # 仓库采购


class PurchaseStatus(str, Enum):
    """采购单主流程状态"""
    DRAFT = "draft"  # 草稿
    AUDITED = "audited"  # 已审核
    CLOSED = "closed"  # 已结案
    CANCELLED = "cancelled"  # 已作废


class InStatus(str, Enum):
    """入库/履约状态"""
    NONE = "none"  # 未入库
    PARTIAL = "partial"  # 部分入库
    FULL = "full"  # 全部入库


class PayStatus(str, Enum):
    """付款状态"""
    NONE = "none"  # 未付款
    PARTIAL = "partial"  # 部分付款
    FULL = "full"  # 全部结清


class ReceiveInfo(BaseModel):
    """收货信息"""
    type: Optional[str] = Field(None, description="收货类型：customer=直运发给客户 / warehouse=入库到仓库")
    warehouse_id: Optional[str] = Field(None, description="目标仓库ID")
    warehouse_name: Optional[str] = Field(None, description="仓库名称")
    customer_addr: Optional[str] = Field(None, description="客户详细地址")
    province: Optional[str] = Field(None, description="省")
    city: Optional[str] = Field(None, description="市")
    contact_person: Optional[str] = Field(None, description="收货人")
    contact_tel: Optional[str] = Field(None, description="联系电话")


class PurchaseStatusInfo(BaseModel):
    """采购单状态信息"""
    purchase_status: PurchaseStatus = Field(PurchaseStatus.DRAFT, description="采购单主流程状态")
    in_status: InStatus = Field(InStatus.NONE, description="入库/履约状态")
    pay_status: PayStatus = Field(PayStatus.NONE, description="付款状态")


class PurchaseOrderItem(BaseModel):
    """采购单明细"""
    row_no: int = Field(..., description="行号")
    product_id: str = Field(..., description="商品ID")
    spec_id: Optional[str] = Field(None, description="规格ID")
    brand_id: Optional[str] = Field(None, description="品牌ID")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    purchase_qty: int = Field(..., gt=0, description="采购数量")
    in_qty: int = Field(default=0, description="已入库/已履约数量")
    return_qty: int = Field(default=0, description="已退货数量")
    purchase_price: float = Field(..., ge=0, description="采购单价")
    discount: float = Field(default=1.0, ge=0, le=1, description="折扣系数")
    amt: Optional[float] = Field(None, description="本行金额")
    shipping_method: Optional[str] = Field(None, description="发货方式")
    source_sale_row_no: Optional[int] = Field(None, description="关联源销售单明细行号")
    warehouse_id: Optional[str] = Field(None, description="本行对应仓库ID")

    class Config:
        json_schema_extra = {
            "example": {
                "row_no": 1,
                "product_id": "507f1f77bcf86cd799439012",
                "spec_id": "507f1f77bcf86cd799439013",
                "brand_id": "507f1f77bcf86cd799439014",
                "brand_name": "品牌名称",
                "purchase_qty": 2,
                "in_qty": 0,
                "return_qty": 0,
                "purchase_price": 4000,
                "discount": 1.0,
                "amt": 8000,
                "shipping_method": "直运",
                "source_sale_row_no": 1,
                "warehouse_id": "507f1f77bcf86cd799439020"
            }
        }


class PurchaseOrderBase(BaseModel):
    """采购单基础模型"""
    purchase_no: str = Field(..., description="采购单单号")
    purchase_type: PurchaseType = Field(..., description="采购类型")
    source_sale_order_no: Optional[str] = Field(None, description="关联源销售订单号")
    source_sale_order_id: Optional[str] = Field(None, description="关联源销售订单主键ID")
    brand_id: Optional[str] = Field(None, description="品牌ID")
    brand_name: Optional[str] = Field(None, description="品牌名称")
    supplier_id: str = Field(..., description="供应商ID")
    supplier_name: Optional[str] = Field(None, description="供应商名称")
    purchase_user_id: Optional[str] = Field(None, description="采购员用户ID")
    receive_info: Optional[ReceiveInfo] = Field(None, description="收货信息")
    expect_arrive_date: Optional[str] = Field(None, description="预计到货日期")
    settle_type: str = Field(..., description="结算方式")
    total_amt: float = Field(..., description="物料不含税总金额")
    freight_amt: float = Field(default=0.0, description="运费总金额")
    status: PurchaseStatusInfo = Field(default_factory=PurchaseStatusInfo, description="状态信息")
    creator_id: Optional[str] = Field(None, description="创建人ID")
    create_time: Optional[str] = Field(None, description="创建时间")
    remark: Optional[str] = Field(None, description="备注")
    items: List[PurchaseOrderItem] = Field(..., description="商品明细")


class PurchaseOrderCreate(BaseModel):
    """创建采购单 - 仅用户输入字段"""
    purchase_type: str = Field(..., description="采购类型：direct/warehouse")
    source_sale_order_no: Optional[str] = Field(None, description="关联源销售订单号")
    source_sale_order_id: Optional[str] = Field(None, description="关联源销售订单主键ID")
    brand_id: Optional[str] = Field(None, description="品牌ID")
    expect_arrive_date: Optional[str] = Field(None, description="预计到货日期")
    settle_type: str = Field(..., description="结算方式")
    freight_amt: float = Field(default=0.0, description="运费总金额")
    remark: Optional[str] = Field(None, description="备注")
    items: List[PurchaseOrderItem] = Field(..., description="商品明细")

    @model_validator(mode='before')
    @classmethod
    def parse_dates_before(cls, data):
        if isinstance(data, dict):
            if 'expect_arrive_date' in data and data['expect_arrive_date']:
                data['expect_arrive_date'] = parse_datetime(data['expect_arrive_date'])
                if data['expect_arrive_date']:
                    data['expect_arrive_date'] = data['expect_arrive_date'].strftime("%Y-%m-%d")
        return data


class PurchaseOrderUpdate(BaseModel):
    """更新采购单"""
    purchase_type: Optional[str] = Field(None, description="采购类型")
    brand_id: Optional[str] = Field(None, description="品牌ID")
    supplier_id: Optional[str] = Field(None, description="供应商ID")
    purchase_user_id: Optional[str] = Field(None, description="采购员用户ID")
    receive_info: Optional[ReceiveInfo] = Field(None, description="收货信息")
    expect_arrive_date: Optional[str] = Field(None, description="预计到货日期")
    settle_type: Optional[str] = Field(None, description="结算方式")
    freight_amt: Optional[float] = Field(None, description="运费总金额")
    remark: Optional[str] = Field(None, description="备注")
    items: Optional[List[PurchaseOrderItem]] = Field(None, description="商品明细")

    @model_validator(mode='before')
    @classmethod
    def parse_dates_before(cls, data):
        if isinstance(data, dict):
            if 'expect_arrive_date' in data and data['expect_arrive_date']:
                data['expect_arrive_date'] = parse_datetime(data['expect_arrive_date'])
                if data['expect_arrive_date']:
                    data['expect_arrive_date'] = data['expect_arrive_date'].strftime("%Y-%m-%d")
        return data


class PurchaseOrder(PurchaseOrderBase):
    """采购单完整模型"""
    id: str = Field(..., description="采购单ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439031",
                "purchase_no": "PO202504200001",
                "purchase_type": "direct",
                "source_sale_order_no": "SO202501010001",
                "source_sale_order_id": "507f1f77bcf86cd799439011",
                "brand_id": "507f1f77bcf86cd799439014",
                "brand_name": "品牌名称",
                "supplier_id": "507f1f77bcf86cd799439032",
                "supplier_name": "供应商名称",
                "purchase_user_id": "507f1f77bcf86cd799439033",
                "receive_info": {
                    "type": "customer",
                    "warehouse_id": None,
                    "warehouse_name": None,
                    "customer_addr": "详细收货地址",
                    "province": "省份",
                    "city": "城市",
                    "contact_person": "收货人",
                    "contact_tel": "联系电话"
                },
                "expect_arrive_date": "2025-04-30",
                "settle_type": "月结",
                "total_amt": 8000.00,
                "tax_rate": 0.13,
                "tax_amt": 1040.00,
                "total_tax_amt": 9040.00,
                "status": {
                    "purchase_status": "audited",
                    "in_status": "none",
                    "pay_status": "none"
                },
                "creator_id": "507f1f77bcf86cd799439014",
                "create_time": "2025-04-20 15:00:00",
                "remark": "由销售单SO202501010001自动生成-直运采购",
                "total_in_qty": 0,
                "total_paid_amt": 0.00,
                "total_return_qty": 0,
                "total_return_amt": 0.00,
                "items": [
                    {
                        "row_no": 1,
                        "product_id": "507f1f77bcf86cd799439012",
                        "spec_id": "507f1f77bcf86cd799439013",
                        "brand_id": "507f1f77bcf86cd799439014",
                        "brand_name": "品牌名称",
                        "purchase_qty": 2,
                        "in_qty": 0,
                        "return_qty": 0,
                        "purchase_price": 4000,
                        "discount": 1.0,
                        "amt": 8000,
                        "shipping_method": "直运",
                        "source_sale_row_no": 1,
                        "warehouse_id": "507f1f77bcf86cd799439020"
                    }
                ]
            }
        }


class PurchaseOrderListResponse(BaseModel):
    """采购单列表响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[PurchaseOrder] = Field(..., description="采购单列表")


class PurchaseStatusUpdate(BaseModel):
    """采购状态更新请求"""
    status: str = Field(..., description="采购状态")


class InStatusUpdate(BaseModel):
    """入库状态更新请求"""
    in_status: str = Field(..., description="入库状态")


class PayStatusUpdate(BaseModel):
    """付款状态更新请求"""
    pay_status: str = Field(..., description="付款状态")
