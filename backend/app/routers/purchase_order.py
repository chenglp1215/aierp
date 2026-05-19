"""
采购单管理 - 路由层
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any
from datetime import date

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

    # 获取关联销售单信息
    source_sales_info = await purchase_order_service.get_source_sales_order_info(purchase_no)
    order["source_sales_order"] = source_sales_info

    return order


@purchase_order_router.get("/{purchase_no}/available-suppliers", response_model=dict, description="获取可选供应商列表")
@wrap_response
async def get_available_suppliers(
    purchase_no: str,
    _: dict = Depends(require_permission("purchase.view"))
):
    suppliers = await purchase_order_service.get_available_suppliers(purchase_no)
    return suppliers


@purchase_order_router.put("/{purchase_no}/supplier", response_model=dict, description="选择/修改供应商")
@wrap_response
async def update_supplier(
    purchase_no: str,
    supplier_id: int = Body(..., embed=True),
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.update_supplier(purchase_no, supplier_id, operator)
    return "供应商更新成功"


@purchase_order_router.put("/{purchase_no}/logistics", response_model=dict, description="更新物流信息")
@wrap_response
async def update_logistics(
    purchase_no: str,
    logistics_company: Optional[str] = Body(None, embed=True),
    logistics_no: Optional[str] = Body(None, embed=True),
    source_purchase_order_id: Optional[str] = Body(None, embed=True),
    expect_arrive_date: Optional[date] = Body(None, embed=True),
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.update_logistics(
        purchase_no,
        logistics_company,
        logistics_no,
        source_purchase_order_id,
        expect_arrive_date,
        operator
    )
    return "物流信息更新成功"


@purchase_order_router.post("/{purchase_no}/approve", response_model=dict, description="审核通过采购单")
@wrap_response
async def approve_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.approve_order(purchase_no, operator, current_user)
    return "采购单审核通过"


@purchase_order_router.post("/{purchase_no}/start-purchase", response_model=dict, description="开始采购")
@wrap_response
async def start_purchase(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.start_purchase(purchase_no, operator)
    return "开始采购成功"


@purchase_order_router.post("/{purchase_no}/complete", response_model=dict, description="采购完成")
@wrap_response
async def complete_purchase(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.complete_order(purchase_no, operator)
    return "采购完成"


@purchase_order_router.post("/{purchase_no}/rollback", response_model=dict, description="状态回退")
@wrap_response
async def rollback_purchase(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    operator = current_user.get("username", current_user.get("full_name", "system"))
    await purchase_order_service.rollback_order(purchase_no, operator)
    return "状态回退成功"


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


@purchase_order_router.post("/{purchase_no}/complete-payment", response_model=dict, description="付款完成")
@wrap_response
async def complete_payment(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    result = await purchase_order_service.complete_payment(purchase_no, current_user)
    return result
    return flows