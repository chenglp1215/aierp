from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class WarehouseStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class StockStatus(str, Enum):
    NORMAL = "normal"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCK = "overstock"


class WarehouseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="仓库名称")
    address: str = Field(..., min_length=1, max_length=500, description="仓库地址")
    manager_id: Optional[str] = Field(None, description="仓库管理员用户ID（关联users表）")
    manager_name: Optional[str] = Field(None, description="仓库管理员姓名（冗余字段，便于显示）")
    status: WarehouseStatus = Field(default=WarehouseStatus.ACTIVE, description="仓库状态")
    description: Optional[str] = Field(None, description="仓库描述")


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    manager_id: Optional[str] = Field(None, description="仓库管理员用户ID")
    manager_name: Optional[str] = Field(None, max_length=100)
    status: Optional[WarehouseStatus] = None
    description: Optional[str] = None


class Warehouse(WarehouseBase):
    id: str = Field(..., description="仓库ID")
    warehouse_code: str = Field(..., description="仓库编码")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439020",
                "warehouse_code": "WH20260420001",
                "name": "深圳中心仓",
                "address": "深圳市宝安区福永街道128号",
                "manager_id": "507f1f77bcf86cd799439011",
                "manager_name": "李明",
                "manager_phone": "13800138001",
                "status": "active",
                "description": "深圳地区主仓库"
            }
        }


class WarehouseListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Warehouse] = Field(..., description="仓库列表")


class InboundBatchBase(BaseModel):
    quantity: float = Field(..., gt=0, description="入库数量")
    remarks: Optional[str] = Field(None, max_length=500, description="备注")


class InboundBatchCreate(InboundBatchBase):
    pass


class InboundBatch(InboundBatchBase):
    id: str = Field(..., description="入库批次ID")
    inventory_id: str = Field(..., description="库存ID")
    operator_id: Optional[str] = Field(None, description="操作人ID")
    operator_name: Optional[str] = Field(None, description="操作人姓名")
    created_at: datetime = Field(default_factory=datetime.now, description="入库时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439030",
                "inventory_id": "507f1f77bcf86cd799439021",
                "quantity": 100,
                "operator_id": "507f1f77bcf86cd799439011",
                "operator_name": "张三",
                "remarks": "采购入库",
                "created_at": "2026-04-28T10:00:00"
            }
        }


class InboundBatchListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[InboundBatch] = Field(..., description="入库批次列表")


class OutboundBatchBase(BaseModel):
    quantity: float = Field(..., gt=0, description="出库数量")
    remarks: Optional[str] = Field(None, max_length=500, description="备注")


class OutboundBatchCreate(OutboundBatchBase):
    pass


class OutboundBatch(OutboundBatchBase):
    id: str = Field(..., description="出库批次ID")
    inventory_id: str = Field(..., description="库存ID")
    operator_id: Optional[str] = Field(None, description="操作人ID")
    operator_name: Optional[str] = Field(None, description="操作人姓名")
    created_at: datetime = Field(default_factory=datetime.now, description="出库时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439031",
                "inventory_id": "507f1f77bcf86cd799439021",
                "quantity": 50,
                "operator_id": "507f1f77bcf86cd799439011",
                "operator_name": "李四",
                "remarks": "销售出库",
                "created_at": "2026-04-28T14:00:00"
            }
        }


class OutboundBatchListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[OutboundBatch] = Field(..., description="出库批次列表")


class InboundOutboundSummary(BaseModel):
    total_inbound: float = Field(0, description="总入库数量")
    total_outbound: float = Field(0, description="总出库数量")
    inbound_count: int = Field(0, description="入库批次数量")
    outbound_count: int = Field(0, description="出库批次数量")


class StockDB(BaseModel):
    id: str = Field(..., description="库存ID")
    spec_id: str = Field(..., description="规格ID")
    warehouse_id: str = Field(..., description="仓库ID")
    quantity: float = Field(..., ge=0, description="当前库存数量")
    min_stock: float = Field(default=0, ge=0, description="最小库存警告阈值")
    max_stock: float = Field(default=0, ge=0, description="最大库存警告阈值")
    status: StockStatus = Field(default=StockStatus.NORMAL, description="库存状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class StockSpecInfo(BaseModel):
    spec_id: str = Field(..., description="规格ID")
    spec_code: str = Field(..., description="规格编号")
    packaging: Optional[str] = Field(None, description="包装规格")
    sales_spec: Optional[str] = Field(None, description="销售规格")
    price: Optional[float] = Field(None, description="价格")


class StockProductInfo(BaseModel):
    product_id: str = Field(..., description="商品ID")
    product_code: str = Field(..., description="商品编号")
    product_name: str = Field(..., description="商品名称")
    category: Optional[str] = Field(None, description="商品分类")


class StockWarehouseInfo(BaseModel):
    warehouse_id: str = Field(..., description="仓库ID")
    warehouse_code: str = Field(..., description="仓库编码")
    warehouse_name: str = Field(..., description="仓库名称")


class StockCreate(BaseModel):
    spec_id: str = Field(..., description="规格ID")
    warehouse_id: str = Field(..., description="仓库ID")
    quantity: float = Field(default=0, ge=0, description="初始库存数量")
    min_stock: float = Field(default=0, ge=0, description="最小库存警告阈值")
    max_stock: float = Field(default=0, ge=0, description="最大库存警告阈值")


class StockUpdate(BaseModel):
    quantity: Optional[float] = Field(None, ge=0)
    min_stock: Optional[float] = Field(None, ge=0)
    max_stock: Optional[float] = Field(None, ge=0)
    status: Optional[StockStatus] = None


class Stock(StockDB):
    spec: Optional[StockSpecInfo] = Field(None, description="规格信息")
    product: Optional[StockProductInfo] = Field(None, description="商品信息")
    warehouse: Optional[StockWarehouseInfo] = Field(None, description="仓库信息")
    inbound_outbound_summary: Optional[InboundOutboundSummary] = Field(None, description="出入库汇总")


class StockListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Stock] = Field(..., description="库存列表")


class StockDetailResponse(BaseModel):
    stock: Stock = Field(..., description="库存详情")
    inbound_batches: List[InboundBatch] = Field(default_factory=list, description="入库批次列表")
    outbound_batches: List[OutboundBatch] = Field(default_factory=list, description="出库批次列表")
