from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List

from models.auth import Permission, PermissionListResponse
from services.auth_service import permission_service
from .auth import get_current_active_user, require_permission

permission_router = APIRouter(prefix="/permissions", tags=["权限管理"])


@permission_router.get("/", response_model=PermissionListResponse)
async def list_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(require_permission("permission.view"))
):
    """获取权限列表"""
    return await permission_service.list_permissions(page, page_size, keyword)


@permission_router.get("/tree", response_model=List[dict])
async def get_permission_tree(
    current_user: dict = Depends(require_permission("permission.view"))
):
    """获取权限树形结构"""
    return await permission_service.get_permission_tree()


@permission_router.get("/{permission_id}/", response_model=Permission)
async def get_permission(
    permission_id: str,
    current_user: dict = Depends(require_permission("permission.view"))
):
    """获取权限详情"""
    permission = await permission_service.get_by_id(permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="权限不存在")
    return permission
