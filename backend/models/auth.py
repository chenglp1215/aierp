from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class RoleStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PermissionType(str, Enum):
    MENU = "menu"
    BUTTON = "button"
    BUTTON_TOOLS = "button,tools"
    TOOLS = "tools"
    API = "api"


class Permission(BaseModel):
    id: str = Field(..., description="权限ID")
    code: str = Field(..., description="权限编码")
    name: str = Field(..., description="权限名称")
    type: str = Field(..., description="权限类型: menu/button/button,tools/tools/api")
    path: Optional[str] = Field(None, description="路径/路由")
    parent_id: Optional[str] = Field(None, description="父权限ID")
    description: Optional[str] = Field(None, description="描述")
    sort_order: int = Field(default=0, description="排序")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class PermissionCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="权限编码")
    name: str = Field(..., min_length=1, max_length=100, description="权限名称")
    type: str = Field(..., description="权限类型: menu/button/button,tools/tools/api")
    path: Optional[str] = Field(None, max_length=200, description="路径/路由")
    parent_id: Optional[str] = Field(None, description="父权限ID")
    description: Optional[str] = Field(None, description="描述")
    sort_order: int = Field(default=0, description="排序")


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = None
    path: Optional[str] = Field(None, max_length=200)
    parent_id: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class Role(BaseModel):
    id: str = Field(..., description="角色ID")
    code: str = Field(..., description="角色编码")
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="描述")
    is_fixed: bool = Field(default=False, description="是否固化角色（固化角色不允许删除和修改）")
    permissions: List[Permission] = Field(default=[], description="角色权限列表")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class RoleCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="描述")
    permission_ids: List[str] = Field(default=[], description="权限ID列表")


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


class User(BaseModel):
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名", json_schema_extra={"unique": True})
    email: Optional[str] = Field(None, description="邮箱", json_schema_extra={"unique": True})
    phone: Optional[str] = Field(None, description="手机号", json_schema_extra={"unique": True})
    full_name: Optional[str] = Field(None, description="全名")
    avatar: Optional[str] = Field(None, description="头像URL")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    roles: List[Role] = Field(default=[], description="用户角色列表")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    role_ids: List[str] = Field(default=[], description="角色ID列表")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    avatar: Optional[str] = None
    role_ids: Optional[List[str]] = None
    new_password: Optional[str] = Field(None, min_length=6, max_length=100, description="新密码(仅更新时生效)")


class UserChangePassword(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class UserResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user: User = Field(..., description="用户信息")


class TokenPayload(BaseModel):
    sub: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    roles: List[str] = Field(default=[], description="角色列表")
    permissions: List[str] = Field(default=[], description="权限列表")
    exp: int = Field(..., description="过期时间戳")


class UserListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[User] = Field(..., description="用户列表")


class RoleListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Role] = Field(..., description="角色列表")


class PermissionListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Permission] = Field(..., description="权限列表")
