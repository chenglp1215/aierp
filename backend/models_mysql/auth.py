"""
用户权限模块 - Tortoise ORM 模型
"""
from enum import Enum
from tortoise import fields
from tortoise.models import Model


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class RoleStatus(str, Enum):
    """角色状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class PermissionType(str, Enum):
    """权限类型枚举"""
    MENU = "menu"
    BUTTON = "button"
    BUTTON_TOOLS = "button,tools"
    TOOLS = "tools"
    API = "api"


class Permission(Model):
    """权限模型"""
    id = fields.IntField(pk=True, description="权限ID")
    code = fields.CharField(max_length=100, unique=True, description="权限编码")
    name = fields.CharField(max_length=100, description="权限名称")
    type = fields.CharEnumField(PermissionType, description="权限类型")
    path = fields.CharField(max_length=200, null=True, description="路径/路由")
    parent: fields.ForeignKeyNullableRelation["Permission"] = fields.ForeignKeyField(
        "models.Permission", null=True, related_name="children", description="父权限"
    )
    description = fields.CharField(max_length=500, null=True, description="描述")
    sort_order = fields.IntField(default=0, description="排序")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "permissions"
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.code}: {self.name}"


class Role(Model):
    """角色模型"""
    id = fields.IntField(pk=True, description="角色ID")
    code = fields.CharField(max_length=50, unique=True, description="角色编码")
    name = fields.CharField(max_length=100, description="角色名称")
    description = fields.CharField(max_length=500, null=True, description="描述")
    is_fixed = fields.BooleanField(default=False, description="是否固化角色")
    status = fields.CharEnumField(RoleStatus, default=RoleStatus.ACTIVE, description="角色状态")
    permissions: fields.ManyToManyRelation[Permission] = fields.ManyToManyField(
        "models.Permission", related_name="roles", through="role_permissions"
    )
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "roles"

    def __str__(self):
        return f"{self.code}: {self.name}"


class User(Model):
    """用户模型"""
    id = fields.IntField(pk=True, description="用户ID")
    username = fields.CharField(max_length=50, unique=True, description="用户名")
    password = fields.CharField(max_length=255, description="密码(bcrypt hash)")
    email = fields.CharField(max_length=100, unique=True, null=True, description="邮箱")
    phone = fields.CharField(max_length=20, unique=True, null=True, description="手机号")
    full_name = fields.CharField(max_length=100, null=True, description="全名")
    avatar = fields.CharField(max_length=500, null=True, description="头像URL")
    status = fields.CharEnumField(UserStatus, default=UserStatus.ACTIVE, description="用户状态")
    roles: fields.ManyToManyRelation[Role] = fields.ManyToManyField(
        "models.Role", related_name="users", through="user_roles"
    )
    last_login = fields.DatetimeField(null=True, description="最后登录时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "users"

    def __str__(self):
        return self.username
