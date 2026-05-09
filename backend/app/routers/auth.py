from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Callable
from jose import JWTError, jwt

from config import settings
from models.auth import (
    User, UserCreate, UserUpdate, UserChangePassword, UserResetPassword,
    UserListResponse, LoginRequest, LoginResponse, TokenPayload
)
from services.auth_service import auth_service
import logging
logger = logging.getLogger('')

security = HTTPBearer(auto_error=False)
auth_router = APIRouter(prefix="/auth", tags=["认证"])

MOCK_ADMIN_USER = {
    "id": "000000000000000000000001",
    "username": "admin",
    "full_name": "管理员",
    "status": "active",
    "roles": [{"code": "super_admin", "name": "超级管理员", "permissions": []}],
    "permissions": [],
    "created_at": None,
    "updated_at": None,
}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """获取当前用户，LOCAL_DEBUG 模式下跳过认证"""
    if settings.LOCAL_DEBUG:
        return MOCK_ADMIN_USER

    if credentials is None:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        user = await auth_service.get_user_by_id(token_data.sub)
        if user is None:
            raise HTTPException(status_code=401, detail="无效的令牌")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """获取当前活跃用户"""
    if current_user.get("status") != "active":
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def require_permission(*permissions: str) -> Callable:
    """权限检查装饰器

    使用方式:
        @require_permission("user.create", "user.edit")
        async def create_user(...): ...

    超级管理员(admin角色)拥有所有权限，直接放行
    """
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


@auth_router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """用户登录"""
    user = await auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    user = await auth_service.get_user_by_username(login_data.username)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={
            "sub": user["id"],
            "username": user["username"],
            "roles": [role["code"] for role in user.get("roles", [])],
            "permissions": user.get("permissions", [])
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds()),
        "user": user
    }


@auth_router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """用户注册"""
    try:
        user_id = await auth_service.create_user(user_data)
        return {
            "status": True,
            "message": "注册成功",
            "result": {"id": user_id}
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return current_user


@auth_router.put("/me/password", response_model=dict)
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_active_user)
):
    """修改密码"""
    try:
        success = await auth_service.change_password(
            current_user["id"],
            password_data.old_password,
            password_data.new_password
        )
        if not success:
            raise HTTPException(status_code=400, detail="修改密码失败")
        return {"status": True, "message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.get("/users/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="用户状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    role: Optional[str] = Query(None, description="角色"),
    current_user: User = Depends(require_permission("user.view"))
):
    """获取用户列表"""
    return await auth_service.list_users(page, page_size, status, keyword, role)


@auth_router.get("/users/{user_id}/", response_model=User)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_permission("user.view"))
):
    """获取用户详情"""
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@auth_router.post("/users/", response_model=dict)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("user.create"))
):
    """创建用户"""
    try:
        user_id = await auth_service.create_user(user_data)
        return {
            "status": True,
            "message": "用户创建成功",
            "result": {"id": user_id}
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.put("/users/{user_id}/", response_model=dict)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_permission("user.edit"))
):
    """更新用户信息"""
    success = await auth_service.update_user(user_id, user_data)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在或更新失败")
    return {"status": True, "message": "用户更新成功"}


@auth_router.delete("/users/{user_id}/", response_model=dict)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission("user.delete"))
):
    """删除用户"""
    success = await auth_service.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在或删除失败")
    return {"status": True, "message": "用户删除成功"}


@auth_router.patch("/users/{user_id}/password", response_model=dict)
async def reset_password(
    user_id: str,
    password_data: UserResetPassword,
    current_user: User = Depends(require_permission("user.reset-password"))
):
    """重置用户密码"""
    try:
        success = await auth_service.reset_password(user_id, password_data.new_password)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"status": True, "message": "密码重置成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.patch("/users/{user_id}/status", response_model=dict)
async def update_user_status(
    user_id: str,
    status: str,
    current_user: User = Depends(require_permission("user.edit"))
):
    """更新用户状态"""
    success = await auth_service.update(user_id, {"status": status})
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"status": True, "message": "用户状态更新成功"}
