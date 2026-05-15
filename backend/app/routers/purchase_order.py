"""
采购单管理 - 路由层
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any

from models_mysql.purchase_order import PurchaseStatus, InStatus, PayStatus
from services.purchase_order_service_mysql import purchase_order_service_mysql as purchase_order_service
from services.order_status_flow_service import order_status_flow_service
from app.decorators import wrap_response
from .auth import require_permission

purchase_order_router = APIRouter(prefix="/purchase-orders", tags=["采购单管理"])


@purchase_order_router.get("/", response_model=dict, description="获取采购单列表")
@wrap_response
async def list_purchase_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    purchase_status: Optional[str] = Query(None, description="采购状态"),
    brand_id: Optional[int] = Query(None, description="品牌ID"),
    source_sale_order_no: Optional[str] = Query(None, description="来源销售单号"),
    _: dict = Depends(require_permission("purchase.view"))
):
    orders, total = await purchase_order_service.list_orders(
        page=page,
        page_size=page_size,
        purchase_status=purchase_status,
        brand_id=brand_id,
        source_sale_order_no=source_sale_order_no,
    )
    return {"total": total, "page": page, "page_size": page_size, "items": orders}


@purchase_order_router.get("/{purchase_no}", response_model=dict, description="获取采购单详情")
@wrap_response
async def get_purchase_order(
    purchase_no: str,
    _: dict = Depends(require_permission("purchase.view"))
):
    order = await purchase_order_service.get_order_by_no(purchase_no)
    if not order:
        raise ValueError("采购单不存在")
    return order


@purchase_order_router.post("/{purchase_no}/approve", response_model=dict, description="审核通过采购单")
@wrap_response
async def approve_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.approve_order(purchase_no, operator)
    return "采购单审核通过"


@purchase_order_router.post("/{purchase_no}/recall", response_model=dict, description="撤销采购单")
@wrap_response
async def recall_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.recall_order(purchase_no, operator)
    return "采购单已撤销"


@purchase_order_router.get("/{purchase_no}/status-flows", response_model=dict, description="获取采购单状态流转记录")
@wrap_response
async def get_purchase_status_flows(
    purchase_no: str,
    _: dict = Depends(require_permission("purchase.view"))
):
    flows = await order_status_flow_service.get_flows_by_order_no(purchase_no)
    return flows