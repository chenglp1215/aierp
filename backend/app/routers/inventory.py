from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.inventory import (
    Warehouse, WarehouseCreate, WarehouseUpdate, WarehouseListResponse,
    Stock, StockCreate, StockUpdate, StockListResponse
)
from services.inventory_service import warehouse_service, stock_service
from .auth import get_current_active_user, require_permission

warehouse_router = APIRouter(prefix="/warehouses", tags=["仓库管理"])
stock_router = APIRouter(prefix="/stocks", tags=["库存管理"])


@warehouse_router.post("/", response_model=dict, status_code=201)
async def create_warehouse(
    warehouse: WarehouseCreate,
    _: dict = Depends(require_permission("warehouse.create"))
):
    warehouse_code = await warehouse_service.create_warehouse(warehouse)
    return {"status": "success", "message": "仓库创建成功", "result": {"code": warehouse_code}}


@warehouse_router.get("/", response_model=WarehouseListResponse)
async def list_warehouses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    _: dict = Depends(require_permission("warehouse.view"))
):
    return await warehouse_service.list_warehouses(page, page_size, status, keyword)


@warehouse_router.get("/search", response_model=dict)
async def search_warehouses(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(require_permission("warehouse.view"))
):
    items = await warehouse_service.search_warehouses(keyword, limit)
    return {"status": "success", "result": items}


@warehouse_router.get("/{warehouse_code}", response_model=Warehouse)
async def get_warehouse(
    warehouse_code: str,
    _: dict = Depends(require_permission("warehouse.view"))
):
    warehouse = await warehouse_service.get_warehouse_by_code(warehouse_code)
    if not warehouse:
        raise HTTPException(status_code=404, detail="仓库不存在")
    return warehouse


@warehouse_router.put("/{warehouse_code}", response_model=dict)
async def update_warehouse(
    warehouse_code: str,
    warehouse: WarehouseUpdate,
    _: dict = Depends(require_permission("warehouse.edit"))
):
    success = await warehouse_service.update_warehouse(warehouse_code, warehouse)
    if not success:
        raise HTTPException(status_code=404, detail="仓库不存在或更新失败")
    return {"status": "success", "message": "仓库更新成功"}


@warehouse_router.delete("/{warehouse_code}", response_model=dict)
async def delete_warehouse(
    warehouse_code: str,
    _: dict = Depends(require_permission("warehouse.delete"))
):
    success = await warehouse_service.delete_warehouse(warehouse_code)
    if not success:
        raise HTTPException(status_code=404, detail="仓库不存在或删除失败")
    return {"status": "success", "message": "仓库删除成功"}


@warehouse_router.patch("/{warehouse_code}/status", response_model=dict)
async def update_warehouse_status(
    warehouse_code: str,
    status: str,
    _: dict = Depends(require_permission("warehouse.edit"))
):
    from models.inventory import WarehouseStatus
    try:
        status_enum = WarehouseStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的仓库状态")
    success = await warehouse_service.update_status(warehouse_code, status_enum)
    if not success:
        raise HTTPException(status_code=404, detail="仓库不存在或状态更新失败")
    return {"status": "success", "message": "仓库状态更新成功"}


@stock_router.post("/", response_model=dict, status_code=201)
async def create_stock(
    stock: StockCreate,
    _: dict = Depends(require_permission("stock.create"))
):
    stock_id = await stock_service.create_stock(stock)
    return {"status": "success", "message": "库存创建成功", "result": {"id": stock_id}}


@stock_router.get("/", response_model=StockListResponse)
async def list_stocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    warehouse_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    _: dict = Depends(require_permission("stock.view"))
):
    return await stock_service.list_stocks(
        page, page_size, warehouse_id, product_id, status, keyword
    )


@stock_router.get("/stats", response_model=dict)
async def get_stock_stats(_: dict = Depends(require_permission("stock.view"))):
    stats = await stock_service.get_stock_stats()
    return {"status": "success", "result": stats}


@stock_router.get("/search", response_model=dict)
async def search_stocks(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(require_permission("stock.view"))
):
    items = await stock_service.search_stocks(keyword, limit)
    return {"status": "success", "result": items}


@stock_router.get("/{stock_id}", response_model=Stock)
async def get_stock(
    stock_id: str,
    _: dict = Depends(require_permission("stock.view"))
):
    stock = await stock_service.get_stock_by_id(stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="库存不存在")
    return stock


@stock_router.put("/{stock_id}", response_model=dict)
async def update_stock(
    stock_id: str,
    stock: StockUpdate,
    _: dict = Depends(require_permission("stock.edit"))
):
    success = await stock_service.update_stock(stock_id, stock)
    if not success:
        raise HTTPException(status_code=404, detail="库存不存在或更新失败")
    return {"status": "success", "message": "库存更新成功"}


@stock_router.delete("/{stock_id}", response_model=dict)
async def delete_stock(
    stock_id: str,
    _: dict = Depends(require_permission("stock.delete"))
):
    success = await stock_service.delete(stock_id)
    if not success:
        raise HTTPException(status_code=404, detail="库存不存在或删除失败")
    return {"status": "success", "message": "库存删除成功"}


@stock_router.post("/{stock_id}/adjust", response_model=dict)
async def adjust_stock(
    stock_id: str,
    quantity_change: float = Query(..., description="库存变化量，正数增加，负数减少"),
    is_add: bool = Query(True, description="是否为增加操作"),
    _: dict = Depends(require_permission("stock.edit"))
):
    result = await stock_service.adjust_stock_by_id(stock_id, quantity_change, is_add)
    if not result:
        raise HTTPException(status_code=404, detail="库存不存在或调整失败")
    return {"status": "success", "message": "库存调整成功", "result": result}
