"""
供应商管理 - API路由
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional, Dict, Any, List

from services.supplier_service_mysql import supplier_service
from .auth import require_permission
from app.decorators import wrap_response

supplier_router = APIRouter(prefix="/suppliers", tags=["供应商管理"])


@supplier_router.post("/", response_model=dict)
@wrap_response
async def create_supplier(
    supplier_data: Dict[str, Any],
    _: dict = Depends(require_permission("supplier.create"))
):
    """创建供应商"""
    existing = await supplier_service.get_supplier_by_name(supplier_data.get("name"))
    if existing:
        raise ValueError("供应商名称已存在")
    return await supplier_service.create_supplier(supplier_data)


@supplier_router.get("/", response_model=dict)
@wrap_response
async def list_suppliers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    brand_ids: Optional[List[int]] = Query(None, description="品牌ID列表"),
    _: dict = Depends(require_permission("supplier.view"))
):
    """获取供应商列表"""
    return await supplier_service.list_suppliers(
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_active=is_active,
        brand_ids=brand_ids
    )


@supplier_router.get("/all", response_model=dict)
@wrap_response
async def get_all_suppliers(
    is_active: Optional[bool] = Query(None, description="是否激活"),
    _: dict = Depends(require_permission("supplier.view"))
):
    """获取所有供应商（用于下拉选择等）"""
    return await supplier_service.get_all_suppliers(is_active=is_active)


@supplier_router.get("/{supplier_id}", response_model=dict)
@wrap_response
async def get_supplier(
    supplier_id: int,
    _: dict = Depends(require_permission("supplier.view"))
):
    """获取供应商详情"""
    return await supplier_service.get_supplier_by_id(supplier_id)


@supplier_router.put("/{supplier_id}", response_model=dict)
@wrap_response
async def update_supplier(
    supplier_id: int,
    supplier_data: Dict[str, Any],
    _: dict = Depends(require_permission("supplier.edit"))
):
    """更新供应商"""
    if supplier_data.get("name"):
        existing = await supplier_service.get_supplier_by_name(supplier_data["name"])
        if existing and existing["id"] != supplier_id:
            raise ValueError("供应商名称已存在")
    await supplier_service.update_supplier(supplier_id, supplier_data)
    return "供应商更新成功"


@supplier_router.delete("/{supplier_id}", response_model=dict)
@wrap_response
async def delete_supplier(
    supplier_id: int,
    _: dict = Depends(require_permission("supplier.delete"))
):
    """删除供应商"""
    await supplier_service.delete_supplier(supplier_id)
    return "供应商删除成功"


@supplier_router.patch("/{supplier_id}/toggle-active", response_model=dict)
@wrap_response
async def toggle_supplier_active(
    supplier_id: int,
    is_active: bool = Query(..., description="是否激活"),
    _: dict = Depends(require_permission("supplier.edit"))
):
    """切换供应商激活状态"""
    await supplier_service.toggle_supplier_active(supplier_id, is_active)
    return f"供应商已{'激活' if is_active else '停用'}"


@supplier_router.get("/by-brand/{brand_id}", response_model=dict)
@wrap_response
async def get_suppliers_by_brand(
    brand_id: int,
    _: dict = Depends(require_permission("supplier.view"))
):
    """根据品牌ID获取供应商列表"""
    return await supplier_service.get_suppliers_by_brand_id(brand_id)