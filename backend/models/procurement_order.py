from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProcurementOrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PURCHASED = "purchased"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ProcurementOrderItem(BaseModel):
    product_id: str = Field(..., description="商品ID")
    product_name: str = Field(..., description="商品名称")
    product_code: Optional[str] = Field(None, description="商品编码")
    quantity: float = Field(..., gt=0, description="采购数量")
    unit_price: float = Field(..., ge=0, description="采购单价")
    subtotal: float = Field(..., description="小计金额")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "507f1f77bcf86cd799439012",
                "product_name": "戴尔OptiPlex 7090商用台式机",
                "product_code": "DELL-OPT-7090",
                "quantity": 10,
                "unit_price": 11500.0,
                "subtotal": 115000.0
            }
        }


class ProcurementOrderBase(BaseModel):
    supplier_id: str = Field(..., description="供应商ID")
    supplier_name: str = Field(..., description="供应商名称")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    delivery_address: Optional[str] = Field(None, description="交货地址")
    expected_delivery_date: Optional[datetime] = Field(None, description="预计交货日期")
    remarks: Optional[str] = Field(None, description="备注")


class ProcurementOrderCreate(ProcurementOrderBase):
    items: List[ProcurementOrderItem] = Field(..., description="采购明细")


class ProcurementOrderUpdate(BaseModel):
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    contact_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    remarks: Optional[str] = None
    status: Optional[ProcurementOrderStatus] = None


class ProcurementOrder(ProcurementOrderBase):
    id: str = Field(..., description="采购单ID")
    procurement_no: str = Field(..., description="采购单编号")
    items: List[ProcurementOrderItem] = Field(default=[], description="采购明细")
    total_amount: float = Field(..., description="采购总金额")
    status: ProcurementOrderStatus = Field(default=ProcurementOrderStatus.DRAFT, description="采购单状态")
    sales_order_id: Optional[str] = Field(None, description="关联销售订单ID")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439031",
                "procurement_no": "PO20260420001",
                "supplier_id": "507f1f77bcf86cd799439032",
                "supplier_name": "深圳市 Dell 总代理",
                "contact_phone": "13900139000",
                "delivery_address": "深圳市宝安区福永街道128号",
                "items": [],
                "total_amount": 115000.0,
                "status": "pending",
                "sales_order_id": "507f1f77bcf86cd799439011",
                "created_at": "2026-04-20T10:00:00"
            }
        }


class ProcurementOrderListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[ProcurementOrder] = Field(..., description="采购单列表")
