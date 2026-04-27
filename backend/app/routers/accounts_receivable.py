from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.accounts_receivable import (
    Receivable,
    ReceivableCreate,
    ReceivableUpdate,
    ReceivableRecordCreate,
    ReceivableListResponse,
    ReceivableStatus
)
from services.accounts_receivable_service import accounts_receivable_service
from .auth import get_current_active_user, require_permission

accounts_receivable_router = APIRouter(prefix="/accounts-receivable", tags=["应收款管理"])


@accounts_receivable_router.post("/", response_model=dict, status_code=201)
async def create_receivable(
    receivable: ReceivableCreate,
    _: dict = Depends(require_permission("receivable.create"))
):
    """创建应收单"""
    receivable_id = await accounts_receivable_service.create_receivable(receivable)
    return {
        "status": "success",
        "message": "应收单创建成功",
        "result": {"id": receivable_id}
    }


@accounts_receivable_router.get("/", response_model=ReceivableListResponse)
async def list_receivables(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="收款状态"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("receivable.view"))
):
    """获取应收单列表"""
    result = await accounts_receivable_service.list_receivables(
        page=page,
        page_size=page_size,
        status=status,
        customer_id=customer_id,
        keyword=keyword
    )
    return result


@accounts_receivable_router.get("/{receivable_id}", response_model=Receivable)
async def get_receivable(
    receivable_id: str,
    _: dict = Depends(require_permission("receivable.view"))
):
    """获取应收单详情"""
    receivable = await accounts_receivable_service.get_by_id(receivable_id)
    if not receivable:
        raise HTTPException(status_code=404, detail="应收单不存在")
    return receivable


@accounts_receivable_router.put("/{receivable_id}", response_model=dict)
async def update_receivable(
    receivable_id: str,
    receivable: ReceivableUpdate,
    _: dict = Depends(require_permission("receivable.edit"))
):
    """更新应收单"""
    success = await accounts_receivable_service.update_receivable(receivable_id, receivable)
    if not success:
        raise HTTPException(status_code=404, detail="应收单不存在或更新失败")
    return {
        "status": "success",
        "message": "应收单更新成功"
    }


@accounts_receivable_router.delete("/{receivable_id}", response_model=dict)
async def delete_receivable(
    receivable_id: str,
    _: dict = Depends(require_permission("receivable.delete"))
):
    """删除应收单"""
    success = await accounts_receivable_service.delete(receivable_id)
    if not success:
        raise HTTPException(status_code=404, detail="应收单不存在或删除失败")
    return {
        "status": "success",
        "message": "应收单删除成功"
    }


@accounts_receivable_router.post("/{receivable_id}/record-payment", response_model=dict)
async def record_payment(
    receivable_id: str,
    record: ReceivableRecordCreate,
    _: dict = Depends(require_permission("receivable.edit"))
):
    """记录收款"""
    success = await accounts_receivable_service.record_payment(receivable_id, record)
    if not success:
        raise HTTPException(status_code=404, detail="应收单不存在或收款记录失败")
    return {
        "status": "success",
        "message": "收款记录成功"
    }


@accounts_receivable_router.patch("/{receivable_id}/status", response_model=dict)
async def update_receivable_status(
    receivable_id: str,
    status: ReceivableStatus,
    _: dict = Depends(require_permission("receivable.edit"))
):
    """更新应收单状态"""
    success = await accounts_receivable_service.update_status(receivable_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="应收单不存在或状态更新失败")
    return {
        "status": "success",
        "message": "应收单状态更新成功"
    }
