"""
销售订单管理 - API路由
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any

from services.sales_order_service import sales_order_service
from services.order_status_flow_service import order_status_flow_service
from .auth import require_permission
from app.decorators import wrap_response

sales_order_router = APIRouter(prefix="/sales-orders", tags=["销售订单管理"])


@sales_order_router.post("/", response_model=dict, description="创建销售订单")
@wrap_response
async def create_sales_order(
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.create"))
):
    result = await sales_order_service.create_sales_order(data, current_user)
    return result


@sales_order_router.post("/create-and-submit", response_model=dict, description="创建并提交销售订单（直接审核通过）")
@wrap_response
async def create_and_submit_sales_order(
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.create"))
):
    result = await sales_order_service.create_sales_order(data, current_user, submit=True)
    return result


@sales_order_router.get("/", response_model=dict, description="获取销售订单列表")
@wrap_response
async def list_sales_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="订单状态"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    order_no: Optional[str] = Query(None, description="订单号模糊搜索"),
    keyword: Optional[str] = Query(None, description="订单号、客户名称、商品名、规格编号模糊搜索"),
    _: dict = Depends(require_permission("order.view"))
):
    orders, total = await sales_order_service.list_sales_orders(
        page=page, page_size=page_size,
        order_status=status, customer_id=customer_id, order_no=order_no, keyword=keyword
    )
    return {"total": total, "page": page, "page_size": page_size, "items": orders}


@sales_order_router.patch("/{order_no}/{status_key}", response_model=dict, description="更新订单状态")
@wrap_response
async def update_order_status(
    order_no: str,
    status_key: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    success = await sales_order_service.update_status_by_no(
        order_no=order_no, status_key=status_key, new_status=data["status"], operator=operator
    )
    if not success:
        raise ValueError("订单不存在或状态更新失败")
    return "订单状态更新成功"

@sales_order_router.post("/{order_no}/push-to-purchase", response_model=dict, description="下推采购：根据选中的商品生成采购单")
@wrap_response
async def push_to_purchase(
    order_no: str,
    items: List[Dict[str, Any]] = Body(..., embed=True),
    current_user: dict = Depends(require_permission("order.edit"))
):
    selected_row_nos = [item["row_no"] for item in items]
    purchase_orders = await sales_order_service.push_to_purchase_by_no(
        order_no, selected_row_nos, current_user
    )
    return {"purchase_orders": purchase_orders}


@sales_order_router.get("/{order_no}/status-flows", response_model=dict, description="获取订单状态流转记录")
@wrap_response
async def get_order_status_flows(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    order = await sales_order_service.get_sales_order_by_no(order_no)
    if not order:
        raise ValueError("订单不存在")
    flows = await order_status_flow_service.get_flows_by_order_no(order_no)
    return flows


@sales_order_router.get("/{order_no}", response_model=dict, description="获取销售订单详情")
@wrap_response
async def get_sales_order(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    order = await sales_order_service.detail_by_no(order_no)
    return order


@sales_order_router.put("/{order_no}", response_model=dict, description="更新销售订单")
@wrap_response
async def update_sales_order(
    order_no: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.edit"))
):
    await sales_order_service.update_sales_order(order_no, data, current_user)
    return "订单更新成功"


@sales_order_router.delete("/{order_no}", response_model=dict, description="删除销售订单")
@wrap_response
async def delete_sales_order(
    order_no: str,
    _: dict = Depends(require_permission("order.delete"))
):
    deleted = await sales_order_service.delete_sales_order_by_no(order_no)
    return "订单删除成功"
