"""
库存管理 - API路由
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional

from models.inventory import (
    Warehouse, WarehouseCreate, WarehouseUpdate,
    Stock, StockCreate, StockUpdate
)
from services.inventory_service import (
    warehouse_service, stock_service,
    inbound_batch_service, outbound_batch_service
)
from .auth import require_permission
from app.decorators import handle_result, success_response, error_response

warehouse_router = APIRouter(prefix="/warehouses", tags=["仓库管理"])
stock_router = APIRouter(prefix="/stocks", tags=["库存管理"])
inbound_router = APIRouter(prefix="/inbound-batches", tags=["入库批次管理"])
outbound_router = APIRouter(prefix="/outbound-batches", tags=["出库批次管理"])


@warehouse_router.post("/", response_model=dict, status_code=201)
async def create_warehouse(
    warehouse: WarehouseCreate,
    _: dict = Depends(require_permission("warehouse.create"))
):
    """创建仓库"""
    warehouse_data = await warehouse_service.create_warehouse(warehouse)
    return success_response("仓库创建成功", {"code": warehouse_data["warehouse_code"]})


@warehouse_router.get("/", response_model=dict)
async def list_warehouses(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="仓库状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("warehouse.view"))
):
    """获取仓库列表"""
    result = await warehouse_service.list_warehouses(page, page_size, status, keyword)
    return success_response(result=result)


@warehouse_router.get("/search", response_model=dict)
async def search_warehouses(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("warehouse.view"))
):
    """搜索仓库（用于下拉选择等）"""
    items = await warehouse_service.search_warehouses(keyword, limit)
    return success_response(result=items)


@warehouse_router.get("/manager-candidates", response_model=dict)
async def get_warehouse_manager_candidates(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("warehouse.view"))
):
    """获取仓库管理员候选人列表"""
    from services.auth_service import auth_service, role_service

    warehouse_admin_role = await role_service.find_one({"code": "warehouse_admin"})
    if not warehouse_admin_role:
        return success_response(result=[])

    warehouse_admin_role_id = str(warehouse_admin_role["id"])

    users = await auth_service.collection.find({
        "status": "active",
        "role_ids": warehouse_admin_role_id
    }).to_list(length=100)

    candidates = []
    for user in users:
        user_id = str(user.get("_id"))
        full_name = user.get("full_name", "")
        username = user.get("username", "")

        if keyword:
            if keyword.lower() not in (full_name or "").lower() and keyword.lower() not in username.lower():
                continue

        candidates.append({
            "id": user_id,
            "username": username,
            "full_name": full_name or username
        })

    return success_response(result=candidates)


@warehouse_router.get("/{warehouse_code}", response_model=dict)
async def get_warehouse(
    warehouse_code: str,
    _: dict = Depends(require_permission("warehouse.view"))
):
    """获取仓库详情"""
    warehouse = await warehouse_service.get_warehouse_by_code(warehouse_code)
    if not warehouse:
        return error_response("仓库不存在")
    return success_response(result=warehouse)


@warehouse_router.put("/{warehouse_code}", response_model=dict)
async def update_warehouse(
    warehouse_code: str,
    warehouse: WarehouseUpdate,
    _: dict = Depends(require_permission("warehouse.edit"))
):
    """更新仓库信息"""
    success = await warehouse_service.update_warehouse(warehouse_code, warehouse)
    return handle_result(success, "仓库更新成功", "仓库不存在或更新失败")


@warehouse_router.delete("/{warehouse_code}", response_model=dict)
async def delete_warehouse(
    warehouse_code: str,
    _: dict = Depends(require_permission("warehouse.delete"))
):
    """删除仓库"""
    success = await warehouse_service.delete_warehouse(warehouse_code)
    return handle_result(success, "仓库删除成功", "仓库不存在或删除失败")


@warehouse_router.patch("/{warehouse_code}/status", response_model=dict)
async def update_warehouse_status(
    warehouse_code: str,
    status: str,
    _: dict = Depends(require_permission("warehouse.edit"))
):
    """更新仓库状态"""
    from models.inventory import WarehouseStatus
    try:
        status_enum = WarehouseStatus(status)
    except ValueError:
        return error_response("无效的仓库状态")
    success = await warehouse_service.update_status(warehouse_code, status_enum)
    return handle_result(success, "仓库状态更新成功", "仓库不存在或状态更新失败")


@stock_router.post("/", response_model=dict, status_code=201)
async def create_stock(
    stock: StockCreate,
    _: dict = Depends(require_permission("stock.create"))
):
    """创建库存"""
    try:
        stock_data = await stock_service.create_stock(stock)
        return success_response("库存创建成功", {"id": stock_data["id"]})
    except ValueError as e:
        if str(e).startswith("DUPLICATE_STOCK:"):
            existing_id = str(e).split(":")[1]
            return success_response("该仓库中已存在此规格的库存记录", {"existing_id": existing_id}, status="duplicate")
        raise


@stock_router.get("/", response_model=dict)
async def list_stocks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    warehouse_id: Optional[str] = Query(None, description="仓库ID"),
    product_id: Optional[str] = Query(None, description="商品ID"),
    spec_id: Optional[str] = Query(None, description="规格ID"),
    status: Optional[str] = Query(None, description="库存状态"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    _: dict = Depends(require_permission("stock.view"))
):
    """获取库存列表"""
    result = await stock_service.list_stocks(
        page, page_size, warehouse_id, product_id, spec_id, status, keyword
    )
    return success_response(result=result)


@stock_router.get("/stats", response_model=dict)
async def get_stock_stats(_: dict = Depends(require_permission("stock.view"))):
    """获取库存统计信息"""
    stats = await stock_service.get_stock_stats()
    return success_response(result=stats)


@stock_router.get("/search", response_model=dict)
async def search_stocks(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("stock.view"))
):
    """搜索库存（用于下拉选择等）"""
    items = await stock_service.search_stocks(keyword, limit)
    return success_response(result=items)


@stock_router.get("/{stock_id}", response_model=dict)
async def get_stock(
    stock_id: str,
    _: dict = Depends(require_permission("stock.view"))
):
    """获取库存详情"""
    stock = await stock_service.get_stock_by_id(stock_id)
    if not stock:
        return error_response("库存不存在")
    return success_response(result=stock)


@stock_router.get("/{stock_id}/detail", response_model=dict)
async def get_stock_detail(
    stock_id: str,
    _: dict = Depends(require_permission("stock.view"))
):
    """获取库存详细信息（含出入库记录）"""
    detail = await stock_service.get_stock_detail(stock_id)
    if not detail:
        return error_response("库存不存在")
    return success_response(result=detail)


@stock_router.put("/{stock_id}", response_model=dict)
async def update_stock(
    stock_id: str,
    stock: StockUpdate,
    _: dict = Depends(require_permission("stock.edit"))
):
    """更新库存信息"""
    success = await stock_service.update_stock(stock_id, stock)
    return handle_result(success, "库存更新成功", "库存不存在或更新失败")


@stock_router.delete("/{stock_id}", response_model=dict)
async def delete_stock(
    stock_id: str,
    _: dict = Depends(require_permission("stock.delete"))
):
    """删除库存"""
    success = await stock_service.delete(stock_id)
    return handle_result(success, "库存删除成功", "库存不存在或删除失败")


@stock_router.post("/{stock_id}/inbound", response_model=dict)
async def inbound_stock(
    stock_id: str,
    quantity: float = Query(..., gt=0, description="入库数量"),
    remarks: Optional[str] = Query(None, description="备注"),
    current_user: dict = Depends(require_permission("stock.edit"))
):
    """入库操作"""
    try:
        operator_id = current_user.get("id")
        operator_name = current_user.get("full_name") or current_user.get("username")
        result = await stock_service.inbound(stock_id, quantity, remarks, operator_id, operator_name)
        if not result:
            return error_response("库存不存在")
        return success_response("入库成功", result)
    except ValueError as e:
        return error_response(str(e))


@stock_router.post("/{stock_id}/outbound", response_model=dict)
async def outbound_stock(
    stock_id: str,
    quantity: float = Query(..., gt=0, description="出库数量"),
    remarks: Optional[str] = Query(None, description="备注"),
    current_user: dict = Depends(require_permission("stock.edit"))
):
    """出库操作"""
    try:
        operator_id = current_user.get("id")
        operator_name = current_user.get("full_name") or current_user.get("username")
        result = await stock_service.outbound(stock_id, quantity, remarks, operator_id, operator_name)
        if not result:
            return error_response("库存不存在")
        return success_response("出库成功", result)
    except ValueError as e:
        return error_response(str(e))


@inbound_router.get("/by-stock/{stock_id}", response_model=dict)
async def get_inbound_batches_by_stock(
    stock_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    _: dict = Depends(require_permission("stock.view"))
):
    """获取入库批次列表"""
    result = await inbound_batch_service.get_inbound_batches_by_inventory(stock_id, page, page_size)
    return success_response(result=result)


@outbound_router.get("/by-stock/{stock_id}", response_model=dict)
async def get_outbound_batches_by_stock(
    stock_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    _: dict = Depends(require_permission("stock.view"))
):
    """获取出库批次列表"""
    result = await outbound_batch_service.get_outbound_batches_by_inventory(stock_id, page, page_size)
    return success_response(result=result)
