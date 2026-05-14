from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Callable, Dict, Any
from jose import JWTError, jwt

from config import settings
from app.middleware import TokenPayload
from services.auth_service import mysql_user_service, mysql_role_service, mysql_permission_service
from app.decorators import wrap_response
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
auth_router = APIRouter(prefix="/auth", tags=["认证"])

MOCK_ADMIN_USER = {
    "id": 1,
    "username": "admin",
    "full_name": "管理员",
    "status": "active",
    "roles": [{"id": 1, "code": "super_admin", "name": "超级管理员", "permissions": []}],
    "permissions": [],
    "created_at": None,
    "updated_at": None,
}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if settings.LOCAL_DEBUG:
        user = await mysql_user_service.get_by_username("admin")
        if user:
            return user
        return MOCK_ADMIN_USER

    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        user = await mysql_user_service.get_by_id(int(token_data.sub))
        if user is None:
            raise HTTPException(status_code=401, detail="无效的令牌")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("status") != "active":
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def require_permission(*permissions: str) -> Callable:
    def dependency(current_user: dict = Depends(get_current_active_user)) -> dict:
        user_roles = current_user.get("roles", [])
        role_codes = [
            role.get("code") if isinstance(role, dict) else role
            for role in user_roles
        ]
        user_perms = set()
        for each_role in user_roles:
            user_perms.update(set([each_perm.get("code") for each_perm in each_role.get("permissions", [])]))

        if "super_admin" in role_codes or "admin" in role_codes:
            return current_user

        logger.info(f"用户名： {current_user.get('username')} , 用户权限: {user_perms}")
        perm_codes = [
            perm.get("code") if isinstance(perm, dict) else perm
            for perm in user_perms
        ]
        if not any(perm in perm_codes for perm in permissions):
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要以下权限之一: {', '.join(permissions)}"
            )
        return current_user
    return dependency


@auth_router.post("/login")
@wrap_response
async def login(login_data: Dict[str, Any]):
    username = login_data.get("username")
    password = login_data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    result = await mysql_user_service.authenticate_user(username, password)
    if not result:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return result


@auth_router.post("/register")
@wrap_response
async def register(user_data: Dict[str, Any]):
    user_id = await mysql_user_service.create_user(user_data)
    return {"id": user_id}


@auth_router.get("/me")
@wrap_response
async def get_me(current_user: dict = Depends(get_current_active_user)):
    return current_user


@auth_router.put("/me/password")
@wrap_response
async def change_password(
    password_data: Dict[str, Any],
    current_user: dict = Depends(get_current_active_user)
):
    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")
    if not old_password or not new_password:
        raise ValueError("旧密码和新密码都不能为空")
    await mysql_user_service.change_password(
        current_user["id"],
        old_password,
        new_password
    )
    return "密码修改成功"


@auth_router.get("/users/")
@wrap_response
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="用户状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色"),
    current_user: dict = Depends(require_permission("user.view"))
):
    return await mysql_user_service.list_users(page, page_size, status, keyword, role)


@auth_router.get("/users/{user_id}/")
@wrap_response
async def get_user(
    user_id: int,
    current_user: dict = Depends(require_permission("user.view"))
):
    user = await mysql_user_service.get_by_id(user_id)
    if not user:
        raise ValueError("用户不存在")
    return user


@auth_router.post("/users/")
@wrap_response
async def create_user(
    user_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("user.create"))
):
    user_id = await mysql_user_service.create_user(user_data)
    return {"id": user_id}


@auth_router.put("/users/{user_id}/")
@wrap_response
async def update_user(
    user_id: int,
    user_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("user.edit"))
):
    success = await mysql_user_service.update_user(user_id, user_data)
    if not success:
        raise ValueError("用户不存在或更新失败")
    return "用户更新成功"


@auth_router.delete("/users/{user_id}/")
@wrap_response
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_permission("user.delete"))
):
    success = await mysql_user_service.delete(user_id)
    if not success:
        raise ValueError("用户不存在或删除失败")
    return "用户删除成功"


@auth_router.patch("/users/{user_id}/password")
@wrap_response
async def reset_password(
    user_id: int,
    password_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("user.reset-password"))
):
    new_password = password_data.get("new_password")
    if not new_password:
        raise ValueError("新密码不能为空")
    success = await mysql_user_service.reset_password(user_id, new_password)
    if not success:
        raise ValueError("用户不存在")
    return "密码重置成功"


@auth_router.patch("/users/{user_id}/status")
@wrap_response
async def update_user_status(
    user_id: int,
    status: str = Query(..., description="用户状态"),
    current_user: dict = Depends(require_permission("user.edit"))
):
    success = await mysql_user_service.update_user(user_id, {"status": status})
    if not success:
        raise ValueError("用户不存在")
    return "用户状态更新成功"


@auth_router.get("/roles/")
@wrap_response
async def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="角色状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(require_permission("role.view"))
):
    return await mysql_role_service.list_roles(page, page_size, status, keyword)


@auth_router.get("/roles/{role_id}/")
@wrap_response
async def get_role(
    role_id: int,
    current_user: dict = Depends(require_permission("role.view"))
):
    role = await mysql_role_service.get_by_id(role_id)
    if not role:
        raise ValueError("角色不存在")
    return role


@auth_router.post("/roles/")
@wrap_response
async def create_role(
    role_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("role.create"))
):
    role = await mysql_role_service.create_role(role_data)
    return {"id": role["id"]}


@auth_router.put("/roles/{role_id}/")
@wrap_response
async def update_role(
    role_id: int,
    role_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("role.edit"))
):
    role = await mysql_role_service.get_by_id(role_id)
    if not role:
        raise ValueError("角色不存在")

    if role.get("is_fixed"):
        raise ValueError("固化角色不允许修改")

    success = await mysql_role_service.update_role(role_id, role_data)
    if not success:
        raise ValueError("角色不存在或更新失败")
    return "角色更新成功"


@auth_router.delete("/roles/{role_id}/")
@wrap_response
async def delete_role(
    role_id: int,
    current_user: dict = Depends(require_permission("role.delete"))
):
    role = await mysql_role_service.get_by_id(role_id)
    if not role:
        raise ValueError("角色不存在")

    if role.get("is_fixed"):
        raise ValueError("固化角色不允许删除")

    success = await mysql_role_service.delete(role_id)
    if not success:
        raise ValueError("角色不存在或删除失败")
    return "角色删除成功"


@auth_router.patch("/roles/{role_id}/status")
@wrap_response
async def update_role_status(
    role_id: int,
    status: str = Query(..., description="角色状态"),
    current_user: dict = Depends(require_permission("role.edit"))
):
    success = await mysql_role_service.update_role(role_id, {"status": status})
    if not success:
        raise ValueError("角色不存在")
    return "角色状态更新成功"


@auth_router.get("/permissions/")
@wrap_response
async def list_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(require_permission("permission.view"))
):
    return await mysql_permission_service.list_permissions(page, page_size, keyword)


@auth_router.get("/permissions/tree")
@wrap_response
async def get_permission_tree(
    current_user: dict = Depends(require_permission("permission.view"))
):
    return await mysql_permission_service.get_permission_tree()


@auth_router.get("/permissions/{permission_id}/")
@wrap_response
async def get_permission(
    permission_id: int,
    current_user: dict = Depends(require_permission("permission.view"))
):
    permission = await mysql_permission_service.get_by_id(permission_id)
    if not permission:
        raise ValueError("权限不存在")
    return permission
