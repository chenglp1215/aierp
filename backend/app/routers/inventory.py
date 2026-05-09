"""
库存管理 - API路由
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional, Dict, Any
from services.inventory_service import warehouse_service, stock_service, inbound_batch_service, outbound_batch_service
from .auth import require_permission
from app.decorators import wrap_response

warehouse_router = APIRouter(prefix="/warehouses", tags=["仓库管理"])
stock_router = APIRouter(prefix="/stocks", tags=["库存管理"])
inbound_router = APIRouter(prefix="/inbound-batches", tags=["入库批次管理"])
outbound_router = APIRouter(prefix="/outbound-batches", tags=["出库批次管理"])


# ============ 仓库管理路由 ============

@warehouse_router.get("/", response_model=dict)
@wrap_response
async def list_warehouses(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="仓库状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("warehouse.view"))
):
    """获取仓库列表"""
    warehouses, total = await warehouse_service.list_warehouses(
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": warehouses
    }


@warehouse_router.post("/", response_model=dict)
@wrap_response
async def create_warehouse(
    warehouse: Dict[str, Any],
    _: dict = Depends(require_permission("warehouse.create"))
):
    """创建仓库"""
    warehouse_data = await warehouse_service.create_warehouse(warehouse)
    return warehouse_data


@warehouse_router.get("/{warehouse_id}", response_model=dict)
@wrap_response
async def get_warehouse(
    warehouse_id: str,
    _: dict = Depends(require_permission("warehouse.view"))
):
    """获取仓库详情"""
    warehouse = await warehouse_service.get_warehouse_by_id(warehouse_id, is_formatted=True)
    if not warehouse:
        raise ValueError("仓库不存在")
    return warehouse


@warehouse_router.put("/{warehouse_id}", response_model=dict)
@wrap_response
async def update_warehouse(
    warehouse_id: str,
    warehouse: Dict[str, Any],
    _: dict = Depends(require_permission("warehouse.edit"))
):
    """更新仓库信息"""
    await warehouse_service.update_warehouse(warehouse_id, warehouse)
    return "仓库更新成功"


# ============ 库存管理路由 ============

@stock_router.get("/", response_model=dict)
@wrap_response
async def list_stocks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    warehouse_id: Optional[str] = Query(None, description="仓库ID"),
    product_id: Optional[str] = Query(None, description="商品ID"),
    spec_id: Optional[str] = Query(None, description="规格ID"),
    status: Optional[str] = Query(None, description="库存状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("stock.view"))
):
    """获取库存列表"""
    stocks, total = await stock_service.list_stocks(
        page=page,
        page_size=page_size,
        warehouse_id=warehouse_id,
        product_id=product_id,
        spec_id=spec_id,
        status=status,
        keyword=keyword
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": stocks
    }


@stock_router.get("/{stock_id}", response_model=dict)
@wrap_response
async def get_stock(
    stock_id: str,
    _: dict = Depends(require_permission("stock.view"))
):
    """获取库存详情"""
    stock = await stock_service.get_stock_by_id(stock_id, is_formatted=True)
    if not stock:
        raise ValueError("库存不存在")
    return stock


@stock_router.put("/{stock_id}", response_model=dict)
@wrap_response
async def update_stock(
    stock_id: str,
    stock: Dict[str, Any],
    _: dict = Depends(require_permission("stock.edit"))
):
    """更新库存信息（手动盘库）"""
    await stock_service.update_stock(stock_id, stock)
    return "库存更新成功"


# ============ 入库批次管理路由 ============

@inbound_router.get("/", response_model=dict)
@wrap_response
async def list_inbound_batches(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    stock_id: Optional[str] = Query(None, description="库存ID"),
    _: dict = Depends(require_permission("inbound.view"))
):
    """获取入库批次列表"""
    batches, total = await inbound_batch_service.get_inbounds_by_stock_id(
        stock_id=stock_id,
        page=page,
        page_size=page_size
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": batches
    }


@inbound_router.post("/", response_model=dict)
@wrap_response
async def create_inbound_batch(
    inbound: Dict[str, Any],
    _: dict = Depends(require_permission("inbound.create"))
):
    """创建入库批次"""
    inbound_data = await inbound_batch_service.create_inbound(inbound)
    return inbound_data


@inbound_router.get("/{batch_id}", response_model=dict)
@wrap_response
async def get_inbound_batch(
    batch_id: str,
    _: dict = Depends(require_permission("inbound.view"))
):
    """获取入库批次详情"""
    batch = await inbound_batch_service.get_by_id(batch_id)
    if not batch:
        raise ValueError("入库批次不存在")
    return batch


@inbound_router.put("/{batch_id}", response_model=dict)
@wrap_response
async def update_inbound_batch(
    batch_id: str,
    inbound: Dict[str, Any],
    _: dict = Depends(require_permission("inbound.edit"))
):
    """更新入库批次"""
    await inbound_batch_service.update_inbound(batch_id, inbound)
    return "入库批次更新成功"


# ============ 出库批次管理路由 ============

@outbound_router.get("/", response_model=dict)
@wrap_response
async def list_outbound_batches(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    stock_id: Optional[str] = Query(None, description="库存ID"),
    _: dict = Depends(require_permission("outbound.view"))
):
    """获取出库批次列表"""
    batches, total = await outbound_batch_service.get_outbounds_by_stock_id(
        stock_id=stock_id,
        page=page,
        page_size=page_size
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": batches
    }


@outbound_router.post("/", response_model=dict)
@wrap_response
async def create_outbound_batch(
    outbound: Dict[str, Any],
    _: dict = Depends(require_permission("outbound.create"))
):
    """创建出库批次"""
    outbound_data = await outbound_batch_service.create_outbound(outbound)
    return outbound_data


@outbound_router.get("/{batch_id}", response_model=dict)
@wrap_response
async def get_outbound_batch(
    batch_id: str,
    _: dict = Depends(require_permission("outbound.view"))
):
    """获取出库批次详情"""
    batch = await outbound_batch_service.get_by_id(batch_id)
    if not batch:
        raise ValueError("出库批次不存在")
    return batch


@outbound_router.put("/{batch_id}", response_model=dict)
@wrap_response
async def update_outbound_batch(
    batch_id: str,
    outbound: Dict[str, Any],
    _: dict = Depends(require_permission("outbound.edit"))
):
    """更新出库批次"""
    await outbound_batch_service.update_outbound(batch_id, outbound)
    return "出库批次更新成功"