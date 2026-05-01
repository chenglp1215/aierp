from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.sales_order import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderListResponse,
    OrderStatus,
    PaymentStatus
)
from models.accounts_receivable import ReceivableCreate
from services.sales_order_service import sales_order_service
from services.accounts_receivable_service import accounts_receivable_service
from .auth import get_current_active_user, require_permission

sales_order_router = APIRouter(prefix="/sales-orders", tags=["销售订单"])


@sales_order_router.post("/", response_model=dict, status_code=201)
async def create_sales_order(
    order: SalesOrderCreate,
    _: dict = Depends(require_permission("order.create"))
):
    """创建销售订单"""
    order_no, db_id = await sales_order_service.create_order(order)

    order_obj = await sales_order_service.get_order_by_no(order_no)
    receivable_data = ReceivableCreate(
        customer_id=order_obj["customer_id"],
        customer_name=order_obj["customer_name"],
        sales_order_id=db_id,
        sales_order_no=order_no,
        total_amount=order_obj["final_amount"]
    )
    await accounts_receivable_service.create_receivable(receivable_data)

    return {
        "status": True,
        "message": "订单创建成功",          
        "result": {"order_no": order_no}
    }


@sales_order_router.get("/", response_model=SalesOrderListResponse)
async def list_sales_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="订单状态"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    warehouse_id: Optional[str] = Query(None, description="仓库ID"),
    product_id: Optional[str] = Query(None, description="商品ID"),
    order_no: Optional[str] = Query(None, description="订单号"),
    _: dict = Depends(require_permission("order.view"))
):
    """获取销售订单列表"""
    result = await sales_order_service.list_orders(
        page=page,
        page_size=page_size,
        status=status,
        customer_id=customer_id,
        warehouse_id=warehouse_id,
        product_id=product_id,
        order_no=order_no
    )
    return result


@sales_order_router.get("/{order_no}", response_model=SalesOrder)
async def get_sales_order(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    """获取销售订单详情"""
    order = await sales_order_service.get_order_by_no(order_no)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


@sales_order_router.put("/{order_no}", response_model=dict)
async def update_sales_order(
    order_no: str,
    order: SalesOrderUpdate,
    _: dict = Depends(require_permission("order.edit"))
):
    """更新销售订单"""
    success = await sales_order_service.update_order(order_no, order)
    if not success:
        raise HTTPException(status_code=404, detail="订单不存在或更新失败")
    return {
        "status": True,
        "message": "订单更新成功"
    }


@sales_order_router.delete("/{order_no}", response_model=dict)
async def delete_sales_order(
    order_no: str,
    _: dict = Depends(require_permission("order.delete"))
):
    """删除销售订单"""
    success = await sales_order_service.delete_by_order_no(order_no)
    if not success:
        raise HTTPException(status_code=404, detail="订单不存在或删除失败")
    return {
        "status": True,
        "message": "订单删除成功"
    }


@sales_order_router.patch("/{order_no}/status", response_model=dict)
async def update_order_status(
    order_no: str,
    status: OrderStatus,
    _: dict = Depends(require_permission("order.edit"))
):
    """更新订单状态"""
    success = await sales_order_service.update_status_by_order_no(order_no, status)
    if not success:
        raise HTTPException(status_code=404, detail="订单不存在或状态更新失败")
    return {
        "status": True,
        "message": "订单状态更新成功"
    }


@sales_order_router.patch("/{order_no}/payment-status", response_model=dict)
async def update_payment_status(
    order_no: str,
    payment_status: PaymentStatus,
    _: dict = Depends(require_permission("order.edit"))
):
    """更新付款状态"""
    success = await sales_order_service.update_payment_status_by_order_no(order_no, payment_status)
    if not success:
        raise HTTPException(status_code=404, detail="订单不存在或付款状态更新失败")
    return {
        "status": True,
        "message": "付款状态更新成功"
    }


@sales_order_router.post("/{order_no}/confirm", response_model=dict)
async def confirm_sales_order(
    order_no: str,
    supplier_id: Optional[str] = Query(None, description="供应商ID（采购直发时必填）"),
    supplier_name: Optional[str] = Query(None, description="供应商名称（采购直发时必填）"),
    _: dict = Depends(require_permission("order.edit"))
):
    """确认销售订单"""
    result = await sales_order_service.confirm_order(order_no, supplier_id, supplier_name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return {
        "status": True,
        "message": result.get("message")
    }
