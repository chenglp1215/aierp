"""
供应商管理 - API路由
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any

from models.supplier import (
    Supplier,
    SupplierCreate,
    SupplierUpdate,
    SupplierListResponse,
)
from services.supplier_service import supplier_service
from validators.supplier_validator import validate_supplier_brands
from .auth import get_current_active_user, require_permission
from app.decorators import handle_result, success_response, error_response

supplier_router = APIRouter(prefix="/suppliers", tags=["供应商管理"])


@supplier_router.post("/", response_model=dict, status_code=201)
async def create_supplier(
    supplier: SupplierCreate,
    _: dict = Depends(require_permission("supplier.create"))
):
    """创建供应商"""
    # 检查名称是否已存在
    existing = await supplier_service.get_supplier_by_name(supplier.name)
    if existing:
        return error_response("供应商名称已存在")

    # 校验供货品牌列表
    is_valid, msg = validate_supplier_brands(supplier.supplied_brands)
    if not is_valid:
        return error_response(msg)

    supplier_data = await supplier_service.create_supplier(supplier)
    return success_response("供应商创建成功", supplier_data)


@supplier_router.get("/", response_model=SupplierListResponse)
async def list_suppliers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    _: dict = Depends(require_permission("supplier.view"))
):
    """获取供应商列表"""
    result = await supplier_service.list_suppliers(
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_active=is_active
    )
    return result


@supplier_router.get("/all", response_model=dict)
async def get_all_suppliers(
    is_active: Optional[bool] = Query(None, description="是否激活"),
    _: dict = Depends(require_permission("supplier.view"))
):
    """获取所有供应商（用于下拉选择等）"""
    items = await supplier_service.get_all_suppliers(is_active=is_active)
    return success_response(result=items)


@supplier_router.get("/{supplier_id}", response_model=dict)
async def get_supplier(
    supplier_id: str,
    _: dict = Depends(require_permission("supplier.view"))
):
    """获取供应商详情"""
    supplier = await supplier_service.get_supplier_by_id(supplier_id)
    if not supplier:
        return error_response("供应商不存在")
    return success_response("获取供应商详情成功", supplier)


@supplier_router.put("/{supplier_id}", response_model=dict)
async def update_supplier(
    supplier_id: str,
    supplier: SupplierUpdate,
    _: dict = Depends(require_permission("supplier.edit"))
):
    """更新供应商"""
    # 检查名称是否已存在
    if supplier.name:
        existing = await supplier_service.get_supplier_by_name(supplier.name)
        if existing and existing["id"] != supplier_id:
            return error_response("供应商名称已存在")

    # 校验供货品牌列表
    if supplier.supplied_brands is not None:
        is_valid, msg = validate_supplier_brands(supplier.supplied_brands)
        if not is_valid:
            return error_response(msg)

    success = await supplier_service.update_supplier(supplier_id, supplier)
    return handle_result(success, "供应商更新成功", "供应商不存在或更新失败")


@supplier_router.delete("/{supplier_id}", response_model=dict)
async def delete_supplier(
    supplier_id: str,
    _: dict = Depends(require_permission("supplier.delete"))
):
    """删除供应商"""
    try:
        success = await supplier_service.delete_supplier(supplier_id)
        return handle_result(success, "供应商删除成功", "供应商不存在或删除失败")
    except ValueError as e:
        return error_response(str(e))


@supplier_router.patch("/{supplier_id}/toggle-active", response_model=dict)
async def toggle_supplier_active(
    supplier_id: str,
    is_active: bool = Query(..., description="是否激活"),
    _: dict = Depends(require_permission("supplier.edit"))
):
    """切换供应商激活状态"""
    success = await supplier_service.toggle_supplier_active(supplier_id, is_active)
    return handle_result(success, f"供应商已{'激活' if is_active else '停用'}", "供应商不存在或更新失败")


@supplier_router.get("/by-brand/{brand_id}", response_model=dict)
async def get_suppliers_by_brand(
    brand_id: str,
    _: dict = Depends(require_permission("supplier.view"))
):
    """根据品牌ID获取供应商列表"""
    suppliers = await supplier_service.get_suppliers_by_brand_id(brand_id)
    return success_response("获取供应商列表成功", suppliers)
