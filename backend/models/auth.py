from pydantic import BaseModel, Field
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
    id: Optional[str] = Field(None, description="权限ID（创建时不需要，由系统自动生成）")
    code: str = Field(..., description="权限编码")
    name: str = Field(..., description="权限名称")
    type: str = Field(..., description="权限类型: menu/button/button,tools/tools/api")
    path: Optional[str] = Field(None, description="路径/路由")
    parent_id: Optional[str] = Field(None, description="父权限ID")
    description: Optional[str] = Field(None, description="描述")
    sort_order: int = Field(default=0, description="排序")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "code": "user.view",
                "name": "用户查看",
                "type": "menu",
                "path": "/users",
                "parent_id": None,
                "description": "查看用户列表",
                "sort_order": 1,
            }
        }


class Role(BaseModel):
    id: Optional[str] = Field(None, description="角色ID（创建时不需要，由系统自动生成）")
    code: str = Field(..., description="角色编码")
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="描述")
    is_fixed: bool = Field(default=False, description="是否固化角色（固化角色不允许删除和修改）")
    status: str = Field(default="active", description="角色状态")
    permission_ids: List[str] = Field(default=[], description="权限ID列表")
    permissions: List[Permission] = Field(default=[], description="角色权限列表")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "code": "admin",
                "name": "管理员",
                "description": "系统管理员",
                "is_fixed": True,
                "status": "active",
                "permission_ids": ["507f1f77bcf86cd799439011"],
                "permissions": [],
            }
        }


class User(BaseModel):
    id: Optional[str] = Field(None, description="用户ID（创建时不需要，由系统自动生成）")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    full_name: Optional[str] = Field(None, description="全名")
    avatar: Optional[str] = Field(None, description="头像URL")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="用户状态")
    role_ids: List[str] = Field(default=[], description="角色ID列表")
    roles: List[Role] = Field(default=[], description="用户角色列表")
    permissions: List[str] = Field(default=[], description="用户权限编码列表")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439013",
                "username": "admin",
                "password": "******",
                "email": "admin@example.com",
                "phone": "13800138000",
                "full_name": "管理员",
                "status": "active",
                "role_ids": ["507f1f77bcf86cd799439012"],
                "roles": [],
                "permissions": [],
            }
        }


class TokenPayload(BaseModel):
    sub: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    roles: List[str] = Field(default=[], description="角色列表")
    permissions: List[str] = Field(default=[], description="权限列表")
    exp: int = Field(..., description="过期时间戳")
