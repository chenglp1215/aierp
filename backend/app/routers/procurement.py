from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.procurement_order import (
    ProcurementOrder,
    ProcurementOrderCreate,
    ProcurementOrderUpdate,
    ProcurementOrderListResponse,
    ProcurementOrderStatus
)
from services.procurement_order_service import procurement_order_service
from .auth import get_current_active_user, require_permission

procurement_router = APIRouter(prefix="/procurement-orders", tags=["采购单管理"])


@procurement_router.post("/", response_model=dict, status_code=201)
async def create_procurement_order(
    order: ProcurementOrderCreate,
    sales_order_id: Optional[str] = Query(None, description="关联销售订单ID"),
    _: dict = Depends(require_permission("procurement.create"))
):
    """创建采购单"""
    order_data = await procurement_order_service.create_procurement_order(
        order, sales_order_id
    )
    return {
        "status": True,
        "message": "采购单创建成功",
        "result": {"id": order_data["id"]}
    }


@procurement_router.get("/", response_model=ProcurementOrderListResponse)
async def list_procurement_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="采购单状态"),
    supplier_id: Optional[str] = Query(None, description="供应商ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("procurement.view"))
):
    """获取采购单列表"""
    result = await procurement_order_service.list_procurement_orders(
        page=page,
        page_size=page_size,
        status=status,
        supplier_id=supplier_id,
        keyword=keyword
    )
    return result


@procurement_router.get("/{order_id}", response_model=ProcurementOrder)
async def get_procurement_order(
    order_id: str,
    _: dict = Depends(require_permission("procurement.view"))
):
    """获取采购单详情"""
    order = await procurement_order_service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="采购单不存在")
    return order


@procurement_router.put("/{order_id}", response_model=dict)
async def update_procurement_order(
    order_id: str,
    order: ProcurementOrderUpdate,
    _: dict = Depends(require_permission("procurement.edit"))
):
    """更新采购单"""
    success = await procurement_order_service.update_procurement_order(order_id, order)
    if not success:
        raise HTTPException(status_code=404, detail="采购单不存在或更新失败")
    return {
        "status": True,
        "message": "采购单更新成功"
    }


@procurement_router.delete("/{order_id}", response_model=dict)
async def delete_procurement_order(
    order_id: str,
    _: dict = Depends(require_permission("procurement.delete"))
):
    """删除采购单"""
    success = await procurement_order_service.delete(order_id)
    if not success:
        raise HTTPException(status_code=404, detail="采购单不存在或删除失败")
    return {
        "status": True,
        "message": "采购单删除成功"
    }


@procurement_router.patch("/{order_id}/status", response_model=dict)
async def update_procurement_order_status(
    order_id: str,
    status: ProcurementOrderStatus,
    _: dict = Depends(require_permission("procurement.edit"))
):
    """更新采购单状态"""
    success = await procurement_order_service.update_status(order_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="采购单不存在或状态更新失败")
    return {
        "status": True,
        "message": "采购单状态更新成功"
    }
