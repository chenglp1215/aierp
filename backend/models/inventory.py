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


class Warehouse(BaseModel):
    """
    仓库模型
    """
    id: str = Field(..., description="仓库ID")
    warehouse_code: str = Field(..., description="仓库编码")
    name: str = Field(..., min_length=1, max_length=100, description="仓库名称")
    address: str = Field(..., min_length=1, max_length=500, description="仓库地址")
    manager_id: Optional[str] = Field(None, description="仓库管理员用户ID（关联users表）")
    manager_name: Optional[str] = Field(None, description="仓库管理员姓名（冗余字段，便于显示）")
    status: WarehouseStatus = Field(default=WarehouseStatus.ACTIVE, description="仓库状态")
    description: Optional[str] = Field(None, description="仓库描述")
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
                "description": "深圳地区主仓库",
                "created_at": "2026-04-28T10:00:00",
                "updated_at": "2026-04-28T10:00:00"
            }
        }


class WarehouseListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Warehouse] = Field(..., description="仓库列表")

# 库存数据库模型
class Stock(BaseModel):
    """
    库存数据库模型
    """
    id: str = Field(..., description="库存ID")
    warehouse_id: str = Field(..., description="仓库ID")
    product_id: str = Field(..., description="商品ID")
    product_code: str = Field(..., description="商品编号")
    product_name: str = Field(..., description="商品名称")

    spec_id: str = Field(..., description="规格ID")
    spec_code: str = Field(..., description="规格编号")

    quantity: float = Field(..., ge=0, description="当前库存数量")
    min_stock: float = Field(default=0, ge=0, description="最小库存警告阈值")
    max_stock: float = Field(default=0, ge=0, description="最大库存警告阈值")
    status: StockStatus = Field(default=StockStatus.NORMAL, description="库存状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439040",
                "warehouse_id": "507f1f77bcf86cd799439020",
                "product_id": "507f1f77bcf86cd799439010",
                "product_code": "P2026010001",
                "product_name": "一次性医用口罩",
                "spec_id": "507f1f77bcf86cd799439030",
                "spec_code": "SP001-A",
                "quantity": 100,
                "min_stock": 10,
                "max_stock": 500,
                "status": "normal",
                "created_at": "2026-04-20T10:00:00",
                "updated_at": "2026-04-28T15:30:00"
            }
        }

class StockListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Stock] = Field(..., description="库存列表")

class InboundBatch(BaseModel):
    """
    入库批次模型
    """
    id: str = Field(..., description="入库批次ID")
    warehouse_id: str = Field(..., description="仓库ID")
    product_id: str = Field(..., description="商品ID")
    product_code: str = Field(..., description="商品编号")
    product_name: str = Field(..., description="商品名称")
    spec_id: str = Field(..., description="规格ID")
    spec_code: str = Field(..., description="规格编号")
    stock_id: str = Field(..., description="库存ID")
    quantity: float = Field(..., ge=0, description="入库数量")
    user_id: str = Field(..., description="操作用户ID")
    user_name: str = Field(..., description="操作用户名")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class OutboundBatch(BaseModel):
    """
    出库批次模型
    """
    id: str = Field(..., description="出库批次ID")
    warehouse_id: str = Field(..., description="仓库ID")
    product_id: str = Field(..., description="商品ID")
    product_code: str = Field(..., description="商品编号")
    product_name: str = Field(..., description="商品名称")
    spec_id: str = Field(..., description="规格ID")
    spec_code: str = Field(..., description="规格编号")
    stock_id: str = Field(..., description="库存ID")
    quantity: float = Field(..., ge=0, description="出库数量")
    user_id: str = Field(..., description="操作用户ID")
    user_name: str = Field(..., description="操作用户名")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")