"""
销售订单管理 - API路由
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any

from services.sales_order_service_mysql import sales_order_service_mysql as sales_order_service
from services.purchase_order_service_mysql import purchase_order_service_mysql as purchase_order_service
from services.order_status_flow_service import order_status_flow_service
from models_mysql.sales_order import SalesOrder, SalesOrderItem
from .auth import require_permission
from app.decorators import wrap_response

sales_order_router = APIRouter(prefix="/sales-orders", tags=["销售订单管理"])


@sales_order_router.post("/", response_model=dict, description="创建销售订单")
@wrap_response
async def create_sales_order(
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.create"))
):
    result = await sales_order_service.create_order(data, current_user)
    return result


@sales_order_router.post("/create-and-submit", response_model=dict, description="创建并提交销售订单（直接审核通过）")
@wrap_response
async def create_and_submit_sales_order(
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.create"))
):
    result = await sales_order_service.create_order(data, current_user, auto_approve=True)
    return result


@sales_order_router.post("/{order_no}/submit", response_model=dict, description="提交审核")
@wrap_response
async def submit_order(
    order_no: str,
    current_user: dict = Depends(require_permission("order.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await sales_order_service.submit_order(order_no, operator)
    return "订单提交审核成功，已直接审核通过"


@sales_order_router.post("/{order_no}/approve", response_model=dict, description="审核通过")
@wrap_response
async def approve_order(
    order_no: str,
    current_user: dict = Depends(require_permission("order.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await sales_order_service.approve_order(order_no, operator)
    return "订单审核通过"


@sales_order_router.post("/{order_no}/reject", response_model=dict, description="驳回订单")
@wrap_response
async def reject_order(
    order_no: str,
    current_user: dict = Depends(require_permission("order.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await sales_order_service.reject_order(order_no, operator)
    return "订单已驳回"


@sales_order_router.get("/", response_model=dict, description="获取销售订单列表")
@wrap_response
async def list_sales_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="订单状态"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    order_no: Optional[str] = Query(None, description="订单号模糊搜索"),
    keyword: Optional[str] = Query(None, description="订单号、客户名称模糊搜索"),
    _: dict = Depends(require_permission("order.view"))
):
    orders, total = await sales_order_service.list_orders(
        page=page, page_size=page_size,
        order_status=status, customer_id=customer_id, order_no=order_no, keyword=keyword
    )
    return {"total": total, "page": page, "page_size": page_size, "items": orders}


@sales_order_router.post("/{order_no}/cancel", response_model=dict, description="取消订单")
@wrap_response
async def cancel_order(
    order_no: str,
    current_user: dict = Depends(require_permission("order.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await sales_order_service.cancel_order(order_no, operator)
    return "订单已取消"


@sales_order_router.get("/{order_no}/status-flows", response_model=dict, description="获取订单状态流转记录")
@wrap_response
async def get_order_status_flows(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    order = await sales_order_service.get_order_by_no(order_no)
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
    order = await sales_order_service.get_order_by_no(order_no)
    if not order:
        raise ValueError("订单不存在")
    return order


@sales_order_router.put("/{order_no}", response_model=dict, description="更新销售订单")
@wrap_response
async def update_sales_order(
    order_no: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.edit"))
):
    await sales_order_service.update_order(order_no, data, current_user)
    return "订单更新成功"


@sales_order_router.delete("/{order_no}", response_model=dict, description="删除销售订单")
@wrap_response
async def delete_sales_order(
    order_no: str,
    _: dict = Depends(require_permission("order.delete"))
):
    await sales_order_service.delete_order(order_no)
    return "订单删除成功"


@sales_order_router.post("/{order_no}/push-to-purchase", response_model=dict, description="下推采购")
@wrap_response
async def push_to_purchase(
    order_no: str,
    data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(require_permission("order.edit"))
):
    """下推采购：将选中的销售订单明细生成采购单"""
    # 获取销售订单
    order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
    if not order:
        raise ValueError(f"销售订单不存在: {order_no}")

    # 获取选中的明细行号
    items_data = data.get("items", [])
    selected_row_nos = [item.get("row_no") for item in items_data if item.get("row_no")]

    # 筛选选中的明细
    selected_items = [item for item in order.items if item.row_no in selected_row_nos]

    # 预加载选中明细的关联数据
    if selected_items:
        item_ids = [item.id for item in selected_items]
        selected_items = list(await SalesOrderItem.filter(id__in=item_ids).select_related(
            "spec__product__brand",
            "warehouse"
        ).all())

    if not selected_items:
        raise ValueError("请选择要下推采购的商品明细")

    # 调用采购单服务创建采购单
    operator = current_user.get("username", current_user.get("full_name", "system"))
    generated_orders = await purchase_order_service.create_from_sales_order(
        order, selected_items, current_user
    )

    # 更新销售订单的下推状态
    await sales_order_service.update_push_status(
        order_no, selected_row_nos, operator
    )

    return generated_orders


# ============ 成本明细管理 ============

@sales_order_router.get("/{order_no}/cost-items", response_model=dict, description="获取成本明细列表")
@wrap_response
async def list_cost_items(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    items = await sales_order_service.list_cost_items(order_no)
    return items


@sales_order_router.post("/{order_no}/cost-items", response_model=dict, description="手动添加成本明细")
@wrap_response
async def create_cost_item(
    order_no: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.edit"))
):
    result = await sales_order_service.create_cost_item(order_no, data, current_user)
    return result


@sales_order_router.delete("/{order_no}/cost-items/{item_id}", response_model=dict, description="删除成本明细")
@wrap_response
async def delete_cost_item(
    order_no: str,
    item_id: int,
    current_user: dict = Depends(require_permission("order.edit"))
):
    await sales_order_service.delete_cost_item(order_no, item_id)
    return "成本明细删除成功"


@sales_order_router.put("/{order_no}/finance-status", response_model=dict, description="更新财务状态")
@wrap_response
async def update_finance_status(
    order_no: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.edit"))
):
    finance_status = data.get("finance_status")
    if not finance_status:
        raise ValueError("请提供财务状态")
    await sales_order_service.update_finance_status(order_no, finance_status)
    return "财务状态更新成功"