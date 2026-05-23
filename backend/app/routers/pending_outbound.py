"""
待出库单管理 - API路由
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any

from services.pending_outbound_service import pending_outbound_service
from .auth import require_permission
from app.decorators import wrap_response

pending_outbound_router = APIRouter(prefix="/pending-outbounds", tags=["出库管理"])


@pending_outbound_router.get("/", response_model=dict, description="获取待出库单列表")
@wrap_response
async def list_pending_outbounds(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    warehouse_id: Optional[int] = Query(None, description="仓库ID"),
    sales_order_no: Optional[str] = Query(None, description="销售订单号"),
    status: Optional[str] = Query(None, description="状态"),
    _: dict = Depends(require_permission("warehouse.view"))
):
    """查询待出库单列表"""
    items, total = await pending_outbound_service.list_pending_outbounds(
        page=page, page_size=page_size,
        warehouse_id=warehouse_id, sales_order_no=sales_order_no, status=status
    )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@pending_outbound_router.get("/{pending_id}", response_model=dict, description="获取待出库单详情")
@wrap_response
async def get_pending_outbound_detail(
    pending_id: int,
    _: dict = Depends(require_permission("warehouse.view"))
):
    """获取待出库单详情"""
    from models_mysql.pending_outbound import PendingOutboundOrder
    pending = await PendingOutboundOrder.filter(id=pending_id).first()
    if not pending:
        raise ValueError("待出库单不存在")
    return pending.to_dict()


@pending_outbound_router.get("/{pending_id}/available-batches", response_model=dict, description="获取可用入库批次")
@wrap_response
async def get_available_batches(
    pending_id: int,
    _: dict = Depends(require_permission("warehouse.view"))
):
    """获取待出库单可用的入库批次（先进先出）"""
    batches = await pending_outbound_service.get_available_batches(pending_id)
    return batches


@pending_outbound_router.post("/{pending_id}/execute", response_model=dict, description="执行出库")
@wrap_response
async def execute_outbound(
    pending_id: int,
    out_qty: int = Body(..., embed=True, description="出库数量"),
    batch_items: Optional[List[Dict[str, Any]]] = Body(None, embed=True, description="批次明细列表 [{inbound_batch_id, quantity}]"),
    current_user: dict = Depends(require_permission("warehouse.edit"))
):
    """执行出库操作"""
    operator = current_user.get("username", current_user.get("full_name", "system"))
    result = await pending_outbound_service.execute_outbound(
        pending_id, out_qty, operator, batch_items=batch_items
    )
    return result


@pending_outbound_router.post("/batch-execute", response_model=dict, description="批量执行出库")
@wrap_response
async def batch_execute_outbound(
    items: List[Dict[str, Any]] = Body(..., description="出库明细列表 [{pending_id, out_qty, batch_items}]"),
    current_user: dict = Depends(require_permission("warehouse.edit"))
):
    """批量执行出库操作"""
    operator = current_user.get("username", current_user.get("full_name", "system"))
    results = []
    for item in items:
        pending_id = item.get("pending_id")
        out_qty = item.get("out_qty")
        batch_items = item.get("batch_items")
        if pending_id and out_qty:
            result = await pending_outbound_service.execute_outbound(
                pending_id, out_qty, operator, batch_items=batch_items
            )
            results.append(result)
    return {"total": len(results), "items": results}


@pending_outbound_router.post("/{pending_id}/ship", response_model=dict, description="发货")
@wrap_response
async def ship_outbound(
    pending_id: int,
    shipping_company: Optional[str] = Body(None, embed=True, description="物流公司"),
    tracking_no: Optional[str] = Body(None, embed=True, description="物流单号"),
    current_user: dict = Depends(require_permission("warehouse.edit"))
):
    """发货操作"""
    operator = current_user.get("username", current_user.get("full_name", "system"))
    result = await pending_outbound_service.ship_outbound(
        pending_id, operator,
        shipping_company=shipping_company,
        tracking_no=tracking_no
    )
    return result


@pending_outbound_router.post("/{pending_id}/revoke", response_model=dict, description="撤销出库")
@wrap_response
async def revoke_outbound(
    pending_id: int,
    current_user: dict = Depends(require_permission("warehouse.edit"))
):
    """撤销出库操作"""
    operator = current_user.get("username", current_user.get("full_name", "system"))
    result = await pending_outbound_service.revoke_outbound(
        pending_id, operator
    )
    return result


@pending_outbound_router.get("/by-order/{sales_order_no}", response_model=dict, description="按销售订单查询待出库单")
@wrap_response
async def get_pending_outbounds_by_order(
    sales_order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    """根据销售订单号查询待出库单"""
    items = await pending_outbound_service.get_by_sales_order(sales_order_no)
    return items