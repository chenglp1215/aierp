from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ReceivableStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    WECHAT = "wechat"
    ALIPAY = "alipay"
    OTHER = "other"


class ReceivableRecord(BaseModel):
    amount: float = Field(..., ge=0, description="收款金额")
    payment_method: Optional[PaymentMethod] = Field(None, description="付款方式")
    payment_date: Optional[datetime] = Field(None, description="付款日期")
    remarks: Optional[str] = Field(None, description="备注")


class ReceivableRecordCreate(BaseModel):
    amount: float = Field(..., gt=0, description="收款金额")
    payment_method: Optional[PaymentMethod] = Field(None, description="付款方式")
    remarks: Optional[str] = Field(None, description="备注")


class ReceivableBase(BaseModel):
    customer_id: str = Field(..., description="客户ID")
    customer_name: str = Field(..., description="客户名称")
    sales_order_id: str = Field(..., description="关联销售订单ID")
    sales_order_no: str = Field(..., description="关联销售订单编号")
    total_amount: float = Field(..., description="应收总金额")
    paid_amount: float = Field(default=0, ge=0, description="已收金额")
    remarks: Optional[str] = Field(None, description="备注")


class ReceivableCreate(ReceivableBase):
    pass


class ReceivableUpdate(BaseModel):
    remarks: Optional[str] = None
    status: Optional[ReceivableStatus] = None


class Receivable(ReceivableBase):
    id: str = Field(..., description="应收单ID")
    receivable_no: str = Field(..., description="应收单编号")
    status: ReceivableStatus = Field(default=ReceivableStatus.UNPAID, description="收款状态")
    records: List[ReceivableRecord] = Field(default_factory=list, description="收款记录")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439041",
                "receivable_no": "AR20260420001",
                "customer_id": "507f1f77bcf86cd799439012",
                "customer_name": "深圳市腾达科技有限公司",
                "sales_order_id": "507f1f77bcf86cd799439011",
                "sales_order_no": "SO20260416001",
                "total_amount": 121600.0,
                "paid_amount": 50000.0,
                "status": "partial",
                "records": [
                    {
                        "amount": 50000.0,
                        "payment_method": "bank_transfer",
                        "payment_date": "2026-04-18T10:00:00",
                        "remarks": "首付款"
                    }
                ],
                "created_at": "2026-04-16T10:00:00"
            }
        }


class ReceivableListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Receivable] = Field(..., description="应收单列表")
