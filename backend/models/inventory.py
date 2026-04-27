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
    manager_name: str = Field(..., min_length=1, max_length=100, description="仓库管理员")
    manager_phone: str = Field(..., min_length=1, max_length=20, description="仓库管理员电话")
    status: WarehouseStatus = Field(default=WarehouseStatus.ACTIVE, description="仓库状态")
    description: Optional[str] = Field(None, description="仓库描述")


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    manager_name: Optional[str] = Field(None, min_length=1, max_length=100)
    manager_phone: Optional[str] = Field(None, min_length=1, max_length=20)
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


class StockBase(BaseModel):
    product_id: str = Field(..., description="商品ID")
    warehouse_id: str = Field(..., description="仓库ID")
    quantity: float = Field(..., ge=0, description="库存数量")
    min_stock: float = Field(default=0, ge=0, description="最小库存警告阈值")
    max_stock: float = Field(default=0, ge=0, description="最大库存警告阈值")
    status: StockStatus = Field(default=StockStatus.NORMAL, description="库存状态")


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    quantity: Optional[float] = Field(None, ge=0)
    min_stock: Optional[float] = Field(None, ge=0)
    max_stock: Optional[float] = Field(None, ge=0)
    status: Optional[StockStatus] = None


class Stock(StockBase):
    id: str = Field(..., description="库存ID")
    product_code: Optional[str] = Field(None, description="商品编号")
    product_name: Optional[str] = Field(None, description="商品名称")
    warehouse_code: Optional[str] = Field(None, description="仓库编码")
    warehouse_name: Optional[str] = Field(None, description="仓库名称")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439021",
                "product_id": "507f1f77bcf86cd799439012",
                "product_code": "PROD20260420001",
                "product_name": "有机红茶",
                "warehouse_id": "507f1f77bcf86cd799439020",
                "warehouse_code": "WH20260420001",
                "warehouse_name": "深圳中心仓",
                "quantity": 500,
                "min_stock": 50,
                "max_stock": 5000,
                "status": "normal"
            }
        }


class StockListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Stock] = Field(..., description="库存列表")
