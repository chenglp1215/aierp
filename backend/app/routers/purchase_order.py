"""
采购单管理 - 路由层
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional

from models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderListResponse,
    PurchaseStatus,
    InStatus,
    PayStatus,
    PurchaseStatusUpdate,
    InStatusUpdate,
    PayStatusUpdate,
)
from services.purchase_order_service_mysql import purchase_order_service_mysql as purchase_order_service
from services.order_status_flow_service import order_status_flow_service
from app.decorators import success_response, error_response, validation_error
from .auth import get_current_active_user, require_permission

purchase_order_router = APIRouter(prefix="/purchase-orders", tags=["采购单管理"])


@purchase_order_router.post("/", response_model=dict, status_code=200)
async def create_purchase_order(
    order: PurchaseOrderCreate,
    current_user: dict = Depends(require_permission("purchase.create"))
):
    """创建采购单"""
    try:
        # 验证数据
        is_valid, errors = purchase_order_service.validate_purchase_order_create(order.model_dump())
        if not is_valid:
            return validation_error(errors, "采购单数据验证失败")

        purchase_no, db_id = await purchase_order_service.create_purchase_order(order, current_user)
        return success_response("采购单创建成功", {"purchase_no": purchase_no, "id": db_id})
    except Exception as e:
        return error_response(f"采购单创建失败: {str(e)}")


@purchase_order_router.get("/", response_model=dict)
async def list_purchase_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="采购状态"),
    purchase_type: Optional[str] = Query(None, description="采购类型"),
    brand_id: Optional[str] = Query(None, description="品牌ID"),
    supplier_id: Optional[str] = Query(None, description="供应商ID"),
    purchase_no: Optional[str] = Query(None, description="采购单号"),
    source_sale_order_no: Optional[str] = Query(None, description="来源销售单号"),
    _: dict = Depends(require_permission("purchase.view"))
):
    """获取采购单列表"""
    try:
        result = await purchase_order_service.list_purchase_orders(
            page=page,
            page_size=page_size,
            status=status,
            purchase_type=purchase_type,
            brand_id=brand_id,
            supplier_id=supplier_id,
            purchase_no=purchase_no,
            source_sale_order_no=source_sale_order_no,
        )
        return success_response("获取采购单列表成功", result)
    except Exception as e:
        return error_response(f"获取采购单列表失败: {str(e)}")


@purchase_order_router.get("/search", response_model=dict)
async def search_purchase_orders(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    _: dict = Depends(require_permission("purchase.view"))
):
    """快速搜索采购单"""
    try:
        items = await purchase_order_service.search_purchase_orders(keyword, limit)
        return success_response("搜索成功", items)
    except Exception as e:
        return error_response(f"搜索失败: {str(e)}")


@purchase_order_router.get("/{purchase_no}", response_model=dict)
async def get_purchase_order(
    purchase_no: str,
    _: dict = Depends(require_permission("purchase.view"))
):
    """获取采购单详情"""
    try:
        order = await purchase_order_service.get_purchase_order_by_no(purchase_no)
        if not order:
            return error_response("采购单不存在")
        return success_response("获取采购单详情成功", order)
    except Exception as e:
        return error_response(f"获取采购单详情失败: {str(e)}")


@purchase_order_router.put("/{purchase_no}", response_model=dict)
async def update_purchase_order(
    purchase_no: str,
    order: PurchaseOrderUpdate,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """更新采购单"""
    try:
        # 验证数据
        is_valid, errors = purchase_order_service.validate_purchase_order_update(order.model_dump(exclude_unset=True))
        if not is_valid:
            return validation_error(errors, "采购单数据验证失败")

        success = await purchase_order_service.update_purchase_order(purchase_no, order, current_user)
        if not success:
            return error_response("采购单不存在或更新失败")
        return success_response("采购单更新成功")
    except Exception as e:
        return error_response(f"采购单更新失败: {str(e)}")


@purchase_order_router.delete("/{purchase_no}", response_model=dict)
async def delete_purchase_order(
    purchase_no: str,
    _: dict = Depends(require_permission("purchase.delete"))
):
    """删除采购单"""
    try:
        success = await purchase_order_service.delete_purchase_order_by_no(purchase_no)
        if not success:
            return error_response("采购单不存在或删除失败")
        return success_response("采购单删除成功")
    except Exception as e:
        return error_response(f"采购单删除失败: {str(e)}")


@purchase_order_router.patch("/{purchase_no}/purchase-status", response_model=dict)
async def update_purchase_status(
    purchase_no: str,
    status_update: PurchaseStatusUpdate,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """更新采购状态"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        status = PurchaseStatus(status_update.status)
        success = await purchase_order_service.update_purchase_status_by_no(purchase_no, status, operator)
        if not success:
            return error_response("采购单不存在或状态更新失败")
        return success_response("采购状态更新成功")
    except ValueError:
        return error_response("无效的采购状态值")
    except Exception as e:
        return error_response(f"采购状态更新失败: {str(e)}")


@purchase_order_router.patch("/{purchase_no}/in-status", response_model=dict)
async def update_in_status(
    purchase_no: str,
    status_update: InStatusUpdate,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """更新入库状态"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        in_status = InStatus(status_update.in_status)
        success = await purchase_order_service.update_in_status_by_no(purchase_no, in_status, operator)
        if not success:
            return error_response("采购单不存在或入库状态更新失败")
        return success_response("入库状态更新成功")
    except ValueError:
        return error_response("无效的入库状态值")
    except Exception as e:
        return error_response(f"入库状态更新失败: {str(e)}")


@purchase_order_router.patch("/{purchase_no}/pay-status", response_model=dict)
async def update_pay_status(
    purchase_no: str,
    status_update: PayStatusUpdate,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """更新付款状态"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        pay_status = PayStatus(status_update.pay_status)
        success = await purchase_order_service.update_pay_status_by_no(purchase_no, pay_status, operator)
        if not success:
            return error_response("采购单不存在或付款状态更新失败")
        return success_response("付款状态更新成功")
    except ValueError:
        return error_response("无效的付款状态值")
    except Exception as e:
        return error_response(f"付款状态更新失败: {str(e)}")


@purchase_order_router.post("/{purchase_no}/recall", response_model=dict)
async def recall_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """撤回采购单（删除采购单，更新销售单状态）"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        success = await purchase_order_service.recall_purchase_order(purchase_no, operator)
        if not success:
            return error_response("采购单不存在或无法撤回（仅草稿和已审核状态可撤回）")
        return success_response("采购单撤回成功")
    except Exception as e:
        return error_response(f"采购单撤回失败: {str(e)}")


@purchase_order_router.post("/{purchase_no}/approve", response_model=dict)
async def approve_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """审核通过采购单（草稿 -> 已审核）"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        success = await purchase_order_service.approve_purchase_order(purchase_no, operator)
        if not success:
            return error_response("采购单不存在或无法审核（仅草稿状态可审核）")
        return success_response("采购单审核通过")
    except Exception as e:
        return error_response(f"采购单审核失败: {str(e)}")


@purchase_order_router.post("/{purchase_no}/close", response_model=dict)
async def close_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """结案采购单（已审核 -> 已结案）"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        success = await purchase_order_service.close_purchase_order(purchase_no, operator)
        if not success:
            return error_response("采购单不存在或无法结案（仅已审核状态可结案）")
        return success_response("采购单结案成功")
    except Exception as e:
        return error_response(f"采购单结案失败: {str(e)}")


@purchase_order_router.post("/{purchase_no}/reaudit", response_model=dict)
async def reaudit_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """重审采购单（已审核 -> 草稿）"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        success = await purchase_order_service.reaudit_purchase_order(purchase_no, operator)
        if not success:
            return error_response("采购单不存在或无法重审（仅已审核状态可重审）")
        return success_response("采购单重审成功（已撤回到草稿）")
    except Exception as e:
        return error_response(f"采购单重审失败: {str(e)}")


@purchase_order_router.post("/{purchase_no}/void", response_model=dict)
async def void_purchase_order(
    purchase_no: str,
    current_user: dict = Depends(require_permission("purchase.edit"))
):
    """作废采购单（已审核 -> 已作废）"""
    try:
        operator = current_user.get("username", current_user.get("full_name", "system"))
        success = await purchase_order_service.void_purchase_order(purchase_no, operator)
        if not success:
            return error_response("采购单不存在或无法作废（仅已审核状态可作废）")
        return success_response("采购单作废成功")
    except Exception as e:
        return error_response(f"采购单作废失败: {str(e)}")


@purchase_order_router.get("/{purchase_no}/status-flows", response_model=dict)
async def get_purchase_status_flows(
    purchase_no: str,
    _: dict = Depends(require_permission("purchase.view"))
):
    """获取采购单状态流转记录"""
    try:
        flows = await order_status_flow_service.get_flows_by_order_no(purchase_no)
        return success_response("获取状态流转记录成功", flows)
    except Exception as e:
        return error_response(f"获取状态流转记录失败: {str(e)}")
