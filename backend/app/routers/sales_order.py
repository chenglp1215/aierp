"""
销售订单管理 - API路由
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any

from models.sales_order import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderListResponse,
    OrderStatus,
    DeliveryStatus,
    ReceiveStatus,
    InvoiceStatus,
    StatusFlowRecord,
    StatusFlowRecordListResponse,
    OrderStatusUpdate,
    DeliveryStatusUpdate,
    ReceiveStatusUpdate,
    InvoiceStatusUpdate
)
from services.sales_order_service import sales_order_service
from services.order_status_flow_service import order_status_flow_service
from .auth import get_current_active_user, require_permission
from app.decorators import handle_result, validation_error, success_response, error_response

sales_order_router = APIRouter(prefix="/sales-orders", tags=["销售订单"])


@sales_order_router.post("/", response_model=dict, status_code=201)
async def create_sales_order(
    order: SalesOrderCreate,
    current_user: dict = Depends(require_permission("order.create"))
):
    """创建销售订单"""
    # 数据验证
    is_valid, errors = sales_order_service.validate_sales_order_create(order.model_dump())
    if not is_valid:
        return validation_error(errors, "销售订单创建参数验证失败")

    order_no, db_id = await sales_order_service.create_sales_order(order, current_user)
    return success_response("订单创建成功", {"order_no": order_no, "id": db_id})


@sales_order_router.post("/create-and-submit", response_model=dict, status_code=201)
async def create_and_submit_sales_order(
    order: SalesOrderCreate,
    current_user: dict = Depends(require_permission("order.create"))
):
    """创建并提交销售订单（直接审核通过）"""
    # 数据验证
    is_valid, errors = sales_order_service.validate_sales_order_create(order.model_dump())
    if not is_valid:
        return validation_error(errors, "销售订单创建参数验证失败")

    order_no, db_id = await sales_order_service.create_and_submit_order(order, current_user)
    return success_response("订单创建并提交成功", {"order_no": order_no, "id": db_id})


@sales_order_router.get("/", response_model=dict)
async def list_sales_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="订单状态"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    order_no: Optional[str] = Query(None, description="订单号"),
    _: dict = Depends(require_permission("order.view"))
):
    """获取销售订单列表"""
    result = await sales_order_service.list_sales_orders(
        page=page,
        page_size=page_size,
        status=status,
        customer_id=customer_id,
        order_no=order_no
    )
    return success_response("获取订单列表成功", result)


@sales_order_router.get("/{order_no}", response_model=dict)
async def get_sales_order(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    """获取销售订单详情"""
    order = await sales_order_service.get_sales_order_by_no(order_no)
    if not order:
        return error_response("订单不存在")
    return success_response("获取订单详情成功", order)


@sales_order_router.put("/{order_no}", response_model=dict)
async def update_sales_order(
    order_no: str,
    order: SalesOrderUpdate,
    current_user: dict = Depends(require_permission("order.edit"))
):
    """更新销售订单"""
    # 数据验证
    is_valid, errors = sales_order_service.validate_sales_order_update(order.model_dump())
    if not is_valid:
        return validation_error(errors, "销售订单更新参数验证失败")
    
    success = await sales_order_service.update_sales_order(order_no, order, current_user)
    if not success:
        return error_response("订单不存在或更新失败")
    return success_response("订单更新成功")


@sales_order_router.delete("/{order_no}", response_model=dict)
async def delete_sales_order(
    order_no: str,
    _: dict = Depends(require_permission("order.delete"))
):
    """删除销售订单"""
    success = await sales_order_service.delete_sales_order_by_no(order_no)
    if not success:
        return error_response("订单不存在或删除失败")
    return success_response("订单删除成功")


@sales_order_router.patch("/{order_no}/order-status", response_model=dict)
async def update_order_status(
    order_no: str,
    body: OrderStatusUpdate,
    current_user: dict = Depends(require_permission("order.edit"))
):
    """更新订单状态"""
    try:
        status = OrderStatus(body.status)
    except ValueError:
        return validation_error({"status": [f"无效的订单状态: {body.status}"]}, "状态值无效")
    operator = current_user.get("username", current_user.get("full_name", "system"))
    success = await sales_order_service.update_order_status_by_no(order_no, status, operator=operator)
    if not success:
        return error_response("订单不存在或状态更新失败")
    return success_response("订单状态更新成功")


@sales_order_router.patch("/{order_no}/delivery-status", response_model=dict)
async def update_delivery_status(
    order_no: str,
    body: DeliveryStatusUpdate,
    current_user: dict = Depends(require_permission("order.edit"))
):
    """更新发货状态"""
    try:
        delivery_status = DeliveryStatus(body.delivery_status)
    except ValueError:
        return validation_error({"delivery_status": [f"无效的发货状态: {body.delivery_status}"]}, "状态值无效")
    operator = current_user.get("username", current_user.get("full_name", "system"))
    success = await sales_order_service.update_delivery_status_by_no(order_no, delivery_status, operator=operator)
    if not success:
        return error_response("订单不存在或发货状态更新失败")
    return success_response("发货状态更新成功")


@sales_order_router.patch("/{order_no}/receive-status", response_model=dict)
async def update_receive_status(
    order_no: str,
    body: ReceiveStatusUpdate,
    current_user: dict = Depends(require_permission("order.edit"))
):
    """更新收货状态"""
    try:
        receive_status = ReceiveStatus(body.receive_status)
    except ValueError:
        return validation_error({"receive_status": [f"无效的收货状态: {body.receive_status}"]}, "状态值无效")
    operator = current_user.get("username", current_user.get("full_name", "system"))
    success = await sales_order_service.update_receive_status_by_no(order_no, receive_status, operator=operator)
    if not success:
        return error_response("订单不存在或收货状态更新失败")
    return success_response("收货状态更新成功")


@sales_order_router.patch("/{order_no}/invoice-status", response_model=dict)
async def update_invoice_status(
    order_no: str,
    body: InvoiceStatusUpdate,
    current_user: dict = Depends(require_permission("order.edit"))
):
    """更新开票状态"""
    try:
        invoice_status = InvoiceStatus(body.invoice_status)
    except ValueError:
        return validation_error({"invoice_status": [f"无效的开票状态: {body.invoice_status}"]}, "状态值无效")
    operator = current_user.get("username", current_user.get("full_name", "system"))
    success = await sales_order_service.update_invoice_status_by_no(order_no, invoice_status, operator=operator)
    if not success:
        return error_response("订单不存在或开票状态更新失败")
    return success_response("开票状态更新成功")



@sales_order_router.post("/{order_no}/push-to-purchase", response_model=dict)
async def push_to_purchase(
    order_no: str,
    items: List[Dict[str, Any]] = Body(..., embed=True),
    current_user: dict = Depends(require_permission("order.edit"))
):
    """下推采购：根据选中的商品生成采购单"""
    try:
        selected_row_nos = [item["row_no"] for item in items]
        purchase_orders = await sales_order_service.push_to_purchase_by_no(
            order_no, selected_row_nos, current_user
        )
        return success_response(
            f"下推采购成功，共生成{len(purchase_orders)}张采购单",
            {"purchase_orders": purchase_orders}
        )
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(f"下推采购失败: {str(e)}")


@sales_order_router.get("/{order_no}/status-flows", response_model=dict)
async def get_order_status_flows(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    """获取订单状态流转记录"""
    # 先检查订单是否存在
    order = await sales_order_service.get_sales_order_by_no(order_no)
    if not order:
        return error_response("订单不存在")

    flows = await order_status_flow_service.get_flows_by_order_no(order_no)
    return success_response("获取流转记录成功", flows)