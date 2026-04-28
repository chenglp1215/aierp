from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from models.auth import (
    Role, RoleCreate, RoleUpdate, RoleListResponse
)
from services.auth_service import role_service
from .auth import get_current_active_user, require_permission

role_router = APIRouter(prefix="/roles", tags=["角色管理"])


@role_router.get("/", response_model=RoleListResponse)
async def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="角色状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(require_permission("role.view"))
):
    """获取角色列表"""
    return await role_service.list_roles(page, page_size, status, keyword)


@role_router.get("/{role_id}", response_model=Role)
async def get_role(
    role_id: str,
    current_user: dict = Depends(require_permission("role.view"))
):
    """获取角色详情"""
    role = await role_service.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role


@role_router.post("/", response_model=dict)
async def create_role(
    role_data: RoleCreate,
    current_user: dict = Depends(require_permission("role.create"))
):
    """创建角色"""
    try:
        role_data = await role_service.create_role(role_data)
        return {
            "status": "success",
            "message": "角色创建成功",
            "result": {"id": role_data["id"]}
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@role_router.put("/{role_id}", response_model=dict)
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: dict = Depends(require_permission("role.edit"))
):
    """更新角色"""
    role = await role_service.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.get("is_fixed"):
        raise HTTPException(status_code=400, detail="固化角色不允许修改")

    try:
        success = await role_service.update_role(role_id, role_data)
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在或更新失败")
        return {"status": "success", "message": "角色更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@role_router.delete("/{role_id}", response_model=dict)
async def delete_role(
    role_id: str,
    current_user: dict = Depends(require_permission("role.delete"))
):
    """删除角色"""
    role = await role_service.get_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.get("is_fixed"):
        raise HTTPException(status_code=400, detail="固化角色不允许删除")

    success = await role_service.delete(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="角色不存在或删除失败")
    return {"status": "success", "message": "角色删除成功"}


@role_router.patch("/{role_id}/status", response_model=dict)
async def update_role_status(
    role_id: str,
    status: str,
    current_user: dict = Depends(require_permission("role.edit"))
):
    """更新角色状态"""
    success = await role_service.update(role_id, {"status": status})
    if not success:
        raise HTTPException(status_code=404, detail="角色不存在")
    return {"status": "success", "message": "角色状态更新成功"}
