# 用户权限模块 MySQL 迁移实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将用户权限模块从 MongoDB 迁移到 MySQL，使用 Tortoise ORM 实现，保持 API 接口兼容（除 ID 类型外）。

**Architecture:** 采用 Tortoise ORM 定义 User、Role、Permission 模型，通过多对多关联表替代 MongoDB 嵌套数组。服务层使用 Django 风格的异步 API（filter、get、prefetch_related）。路由层遵循现有 product.py 模式。

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL, Aerich, bcrypt, JWT

---

## 文件结构

```
backend/
├── requirements.txt              # 新增: tortoise-orm[aiomysql], aerich
├── config/
│   └── settings.py               # 修改: 添加 MySQL 配置
├── app/
│   ├── database.py               # 修改: 添加 Tortoise 初始化
│   └── routers/
│       └── auth.py               # 重写: 使用 MySQL 服务
├── models_mysql/                 # 新增目录
│   ├── __init__.py
│   └── auth.py                   # 新增: Tortoise ORM 模型
├── services/
│   └── auth_service.py           # 重写: MySQL 版服务层
├── validators/
│   └── auth_validator.py         # 保持不变
├── scripts/
│   └── init_db_mysql.py          # 新增: MySQL 初始化脚本
└── migrations/                   # 新增: Aerich 迁移目录

web/src/
├── components/workspace/
│   ├── UserManagement.vue        # 修改: id 类型改为 number
│   ├── RoleManagement.vue        # 修改: id 类型改为 number
│   └── PermissionManagement.vue  # 修改: id 类型改为 number
└── hooks/
    └── usePermission.ts          # 修改: id 类型改为 number
```

---

## Task 1: 添加依赖和配置

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/config/settings.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: 添加 Tortoise ORM 依赖**

在 `backend/requirements.txt` 末尾添加：

```text
tortoise-orm[aiomysql]>=0.20.0
aerich>=0.7.2
```

- [ ] **Step 2: 添加 MySQL 配置到 settings.py**

在 `backend/config/settings.py` 的 `Settings` 类中，在 `MONGODB_DB_NAME` 后添加：

```python
    # MySQL 配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "aierp"
```

- [ ] **Step 3: 更新 .env.example**

在 `backend/.env.example` 中添加 MySQL 配置示例：

```text
# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=aierp
```

- [ ] **Step 4: 提交配置变更**

```bash
cd backend && git add requirements.txt config/settings.py .env.example && git commit -m "feat: 添加 MySQL 和 Tortoise ORM 配置"
```

---

## Task 2: 创建 Tortoise ORM 模型

**Files:**
- Create: `backend/models_mysql/__init__.py`
- Create: `backend/models_mysql/auth.py`

- [ ] **Step 1: 创建 models_mysql 目录和 __init__.py**

创建 `backend/models_mysql/__init__.py`：

```python
"""
MySQL ORM 模型（Tortoise ORM）
"""
from .auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType

__all__ = [
    "User",
    "Role", 
    "Permission",
    "UserStatus",
    "RoleStatus",
    "PermissionType",
]
```

- [ ] **Step 2: 创建 auth.py - 枚举定义**

创建 `backend/models_mysql/auth.py`，首先添加枚举：

```python
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
```

- [ ] **Step 3: 创建 Permission 模型**

在 `backend/models_mysql/auth.py` 枚举后添加：

```python
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
```

- [ ] **Step 4: 创建 Role 模型**

在 Permission 模型后添加：

```python
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
```

- [ ] **Step 5: 创建 User 模型**

在 Role 模型后添加：

```python
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
```

- [ ] **Step 6: 提交模型文件**

```bash
cd backend && git add models_mysql/ && git commit -m "feat: 添加 Tortoise ORM 用户权限模型"
```

---

## Task 3: 配置数据库连接

**Files:**
- Modify: `backend/app/database.py`

- [ ] **Step 1: 添加 Tortoise 初始化函数**

在 `backend/app/database.py` 文件末尾添加：

```python
from tortoise import Tortoise


async def init_mysql():
    """初始化 MySQL (Tortoise ORM) 连接"""
    from config import settings
    
    await Tortoise.init(
        db_url=f"mysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
        modules={"models": ["models_mysql.auth"]},
        generate_schemas=True,
    )
    print("✅ MySQL (Tortoise ORM) 连接成功")


async def close_mysql():
    """关闭 MySQL 连接"""
    await Tortoise.close_connections()
    print("✅ MySQL 连接已关闭")
```

- [ ] **Step 2: 更新 init_db 和 close_db 函数**

修改 `backend/app/database.py` 中的 `init_db` 和 `close_db` 函数：

```python
async def init_db():
    """初始化数据库"""
    await db.init_db()
    await init_mysql()


async def close_db():
    """关闭数据库连接"""
    await db.close_db()
    await close_mysql()
```

- [ ] **Step 3: 提交数据库连接变更**

```bash
cd backend && git add app/database.py && git commit -m "feat: 添加 Tortoise ORM 数据库连接初始化"
```

---

## Task 4: 实现用户服务层

**Files:**
- Modify: `backend/services/auth_service.py`

- [ ] **Step 1: 添加导入和新服务类框架**

在 `backend/services/auth_service.py` 文件开头添加导入：

```python
from models_mysql.auth import User, Role, Permission, UserStatus, RoleStatus
from tortoise.expressions import Q
```

在文件末尾添加新的服务类（保留原有的 MongoDB 服务类，稍后删除）：

```python
# ============ MySQL 版服务（Tortoise ORM）============

class MySQLUserService:
    """用户服务（MySQL 版）"""
```

- [ ] **Step 2: 实现密码加密方法**

在 `MySQLUserService` 类中添加：

```python
    def _hash_password(self, password: str) -> str:
        """加密密码"""
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        import bcrypt
        if not hashed_password:
            return False
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
```

- [ ] **Step 3: 实现 get_by_id 和 get_by_username 方法**

```python
    async def get_by_id(self, user_id: int) -> Optional[dict]:
        """根据 ID 获取用户"""
        user = await User.get_or_none(id=user_id).prefetch_related("roles", "roles__permissions")
        if not user:
            return None
        return await self._format_user(user)

    async def get_by_username(self, username: str) -> Optional[dict]:
        """根据用户名获取用户"""
        user = await User.get_or_none(username=username).prefetch_related("roles", "roles__permissions")
        if not user:
            return None
        return await self._format_user(user)
```

- [ ] **Step 4: 实现 _format_user 方法**

```python
    async def _format_user(self, user: User) -> dict:
        """格式化用户数据"""
        roles = await user.roles.all().prefetch_related("permissions")
        all_permissions = set()
        role_list = []
        
        for role in roles:
            perms = await role.permissions.all()
            role_data = {
                "id": role.id,
                "code": role.code,
                "name": role.name,
                "permissions": [{"id": p.id, "code": p.code, "name": p.name} for p in perms]
            }
            role_list.append(role_data)
            all_permissions.update(p.code for p in perms)
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "full_name": user.full_name,
            "avatar": user.avatar,
            "status": user.status.value,
            "roles": role_list,
            "permissions": list(all_permissions),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
```

- [ ] **Step 5: 实现 create_user 方法**

```python
    async def create_user(self, data: Dict[str, Any]) -> dict:
        """创建用户"""
        username = data.get("username")
        if await User.filter(username=username).exists():
            raise ValueError("用户名已存在")
        
        email = data.get("email")
        if email and await User.filter(email=email).exists():
            raise ValueError("邮箱已存在")
        
        phone = data.get("phone")
        if phone and await User.filter(phone=phone).exists():
            raise ValueError("手机号已被使用")
        
        user = await User.create(
            username=username,
            password=self._hash_password(data.get("password", "")),
            email=email,
            phone=phone,
            full_name=data.get("full_name"),
        )
        
        # 关联角色
        role_ids = data.get("role_ids", [])
        if role_ids:
            roles = await Role.filter(id__in=role_ids)
            await user.roles.add(*roles)
        
        return await self._format_user(user)
```

- [ ] **Step 6: 实现 update_user 方法**

```python
    async def update_user(self, user_id: int, data: Dict[str, Any]) -> bool:
        """更新用户"""
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 检查邮箱唯一性
        email = data.get("email")
        if email:
            existing = await User.filter(email=email, id__not=user_id).exists()
            if existing:
                raise ValueError("邮箱已被其他用户使用")
        
        # 检查手机号唯一性
        phone = data.get("phone")
        if phone:
            existing = await User.filter(phone=phone, id__not=user_id).exists()
            if existing:
                raise ValueError("手机号已被其他用户使用")
        
        # 更新密码
        new_password = data.get("new_password")
        if new_password:
            user.password = self._hash_password(new_password)
        
        # 更新其他字段
        for key in ["email", "phone", "full_name", "avatar", "status"]:
            if key in data:
                setattr(user, key, data[key])
        
        await user.save()
        
        # 更新角色
        if "role_ids" in data:
            await user.roles.clear()
            if data["role_ids"]:
                roles = await Role.filter(id__in=data["role_ids"])
                await user.roles.add(*roles)
        
        return True
```

- [ ] **Step 7: 实现 delete 和 list_users 方法**

```python
    async def delete(self, user_id: int) -> bool:
        """删除用户"""
        user = await User.get_or_none(id=user_id)
        if not user:
            return False
        await user.roles.clear()
        await user.delete()
        return True

    async def list_users(
        self, page: int = 1, page_size: int = 20,
        status: str = None, keyword: str = None, role: str = None
    ) -> dict:
        """获取用户列表"""
        query = User.all()
        
        if status:
            query = query.filter(status=status)
        if keyword:
            query = query.filter(
                Q(username__icontains=keyword) |
                Q(full_name__icontains=keyword) |
                Q(email__icontains=keyword)
            )
        
        total = await query.count()
        users = await query.offset((page - 1) * page_size).limit(page_size).prefetch_related("roles")
        
        items = []
        for user in users:
            user_dict = await self._format_user(user)
            items.append(user_dict)
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
```

- [ ] **Step 8: 实现 authenticate_user 方法**

```python
    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """认证用户"""
        user = await User.get_or_none(username=username)
        if not user:
            return None
        if not self._verify_password(password, user.password):
            return None
        return await self._format_user(user)
```

- [ ] **Step 9: 实现 change_password 和 reset_password 方法**

```python
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        if not self._verify_password(old_password, user.password):
            raise ValueError("旧密码错误")
        user.password = self._hash_password(new_password)
        await user.save()
        return True

    async def reset_password(self, user_id: int, new_password: str) -> bool:
        """重置密码"""
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        user.password = self._hash_password(new_password)
        await user.save()
        return True
```

- [ ] **Step 10: 提交用户服务层**

```bash
cd backend && git add services/auth_service.py && git commit -m "feat: 实现 MySQL 版用户服务层"
```

---

## Task 5: 实现角色和权限服务层

**Files:**
- Modify: `backend/services/auth_service.py`

- [ ] **Step 1: 实现 MySQLRoleService 类**

在 `MySQLUserService` 类后添加：

```python
class MySQLRoleService:
    """角色服务（MySQL 版）"""

    async def get_by_id(self, role_id: int) -> Optional[dict]:
        """根据 ID 获取角色"""
        role = await Role.get_or_none(id=role_id).prefetch_related("permissions")
        if not role:
            return None
        return await self._format_role(role)

    async def get_by_code(self, code: str) -> Optional[dict]:
        """根据编码获取角色"""
        role = await Role.get_or_none(code=code).prefetch_related("permissions")
        if not role:
            return None
        return await self._format_role(role)

    async def _format_role(self, role: Role) -> dict:
        """格式化角色数据"""
        permissions = await role.permissions.all()
        return {
            "id": role.id,
            "code": role.code,
            "name": role.name,
            "description": role.description,
            "is_fixed": role.is_fixed,
            "status": role.status.value,
            "permissions": [{"id": p.id, "code": p.code, "name": p.name} for p in permissions],
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        }
```

- [ ] **Step 2: 实现 create_role 和 update_role 方法**

```python
    async def create_role(self, data: Dict[str, Any]) -> dict:
        """创建角色"""
        code = data.get("code")
        if await Role.filter(code=code).exists():
            raise ValueError("角色编码已存在")
        
        role = await Role.create(
            code=code,
            name=data.get("name"),
            description=data.get("description"),
            is_fixed=data.get("is_fixed", False),
        )
        
        permission_ids = data.get("permission_ids", [])
        if permission_ids:
            permissions = await Permission.filter(id__in=permission_ids)
            await role.permissions.add(*permissions)
        
        return await self._format_role(role)

    async def update_role(self, role_id: int, data: Dict[str, Any]) -> bool:
        """更新角色"""
        role = await Role.get_or_none(id=role_id)
        if not role:
            raise ValueError("角色不存在")
        
        for key in ["name", "description", "status"]:
            if key in data:
                setattr(role, key, data[key])
        
        await role.save()
        
        if "permission_ids" in data:
            await role.permissions.clear()
            if data["permission_ids"]:
                permissions = await Permission.filter(id__in=data["permission_ids"])
                await role.permissions.add(*permissions)
        
        return True
```

- [ ] **Step 3: 实现 delete 和 list_roles 方法**

```python
    async def delete(self, role_id: int) -> bool:
        """删除角色"""
        role = await Role.get_or_none(id=role_id)
        if not role:
            return False
        await role.permissions.clear()
        await role.delete()
        return True

    async def list_roles(
        self, page: int = 1, page_size: int = 20,
        status: str = None, keyword: str = None
    ) -> dict:
        """获取角色列表"""
        query = Role.all()
        
        if status:
            query = query.filter(status=status)
        if keyword:
            query = query.filter(
                Q(code__icontains=keyword) | Q(name__icontains=keyword)
            )
        
        total = await query.count()
        roles = await query.offset((page - 1) * page_size).limit(page_size).prefetch_related("permissions")
        
        items = [await self._format_role(role) for role in roles]
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }
```

- [ ] **Step 4: 实现 MySQLPermissionService 类**

在 `MySQLRoleService` 类后添加：

```python
class MySQLPermissionService:
    """权限服务（MySQL 版）"""

    async def get_by_id(self, permission_id: int) -> Optional[dict]:
        """根据 ID 获取权限"""
        perm = await Permission.get_or_none(id=permission_id)
        if not perm:
            return None
        return await self._format_permission(perm)

    async def _format_permission(self, perm: Permission) -> dict:
        """格式化权限数据"""
        return {
            "id": perm.id,
            "code": perm.code,
            "name": perm.name,
            "type": perm.type.value,
            "path": perm.path,
            "parent_id": perm.parent_id,
            "description": perm.description,
            "sort_order": perm.sort_order,
            "created_at": perm.created_at.isoformat() if perm.created_at else None,
            "updated_at": perm.updated_at.isoformat() if perm.updated_at else None,
        }
```

- [ ] **Step 5: 实现 list_permissions 和 get_permission_tree 方法**

```python
    async def list_permissions(
        self, page: int = 1, page_size: int = 20, keyword: str = None
    ) -> dict:
        """获取权限列表"""
        query = Permission.all()
        
        if keyword:
            query = query.filter(
                Q(code__icontains=keyword) | Q(name__icontains=keyword)
            )
        
        total = await query.count()
        permissions = await query.offset((page - 1) * page_size).limit(page_size)
        
        items = [await self._format_permission(p) for p in permissions]
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }

    async def get_permission_tree(self) -> List[dict]:
        """获取权限树"""
        permissions = await Permission.all().order_by("sort_order")
        
        # 构建映射
        perm_map = {p.id: await self._format_permission(p) for p in permissions}
        
        # 初始化 children
        for perm_data in perm_map.values():
            perm_data["children"] = []
        
        # 构建树
        roots = []
        for perm in permissions:
            perm_data = perm_map[perm.id]
            if perm.parent_id and perm.parent_id in perm_map:
                perm_map[perm.parent_id]["children"].append(perm_data)
            else:
                roots.append(perm_data)
        
        return roots
```

- [ ] **Step 6: 添加服务实例**

在文件末尾添加：

```python
# MySQL 版服务实例
mysql_user_service = MySQLUserService()
mysql_role_service = MySQLRoleService()
mysql_permission_service = MySQLPermissionService()
```

- [ ] **Step 7: 提交服务层变更**

```bash
cd backend && git add services/auth_service.py && git commit -m "feat: 实现 MySQL 版角色和权限服务层"
```

---

## Task 6: 重写认证路由

**Files:**
- Modify: `backend/app/routers/auth.py`

- [ ] **Step 1: 更新导入**

修改 `backend/app/routers/auth.py` 开头的导入：

```python
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Callable, Dict, Any
from jose import JWTError, jwt

from config import settings
from models.auth import TokenPayload
from services.auth_service import mysql_user_service, mysql_role_service, mysql_permission_service
from app.decorators import wrap_response
import logging

logger = logging.getLogger(__name__)
```

- [ ] **Step 2: 更新 MOCK_ADMIN_USER**

修改 `MOCK_ADMIN_USER` 的 id 为整数：

```python
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
```

- [ ] **Step 3: 更新 get_current_user 函数**

修改 `get_current_user` 函数中的服务调用：

```python
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
```

- [ ] **Step 4: 更新 login 路由**

修改 `login` 函数：

```python
@auth_router.post("/login")
@wrap_response
async def login(login_data: Dict[str, Any]):
    username = login_data.get("username")
    password = login_data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")

    user = await mysql_user_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = mysql_user_service._create_access_token(
        data={
            "sub": str(user["id"]),
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
```

- [ ] **Step 5: 添加 JWT 生成方法到 MySQLUserService**

在 `MySQLUserService` 类中添加：

```python
    def _create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """生成 JWT Token"""
        from jose import jwt
        from datetime import datetime, timedelta
        from config import settings
        
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
```

- [ ] **Step 6: 更新用户相关路由**

修改用户相关路由，将 `user_id: str` 改为 `user_id: int`：

```python
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
```

- [ ] **Step 7: 更新角色相关路由**

修改角色相关路由：

```python
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
```

- [ ] **Step 8: 更新权限相关路由**

修改权限相关路由：

```python
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
```

- [ ] **Step 9: 更新 list_users 和 create_user 路由**

```python
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


@auth_router.post("/users/")
@wrap_response
async def create_user(
    user_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("user.create"))
):
    user = await mysql_user_service.create_user(user_data)
    return {"id": user["id"]}
```

- [ ] **Step 10: 更新 list_roles 和 create_role 路由**

```python
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


@auth_router.post("/roles/")
@wrap_response
async def create_role(
    role_data: Dict[str, Any],
    current_user: dict = Depends(require_permission("role.create"))
):
    role = await mysql_role_service.create_role(role_data)
    return {"id": role["id"]}
```

- [ ] **Step 11: 更新 list_permissions 路由**

```python
@auth_router.get("/permissions/")
@wrap_response
async def list_permissions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(require_permission("permission.view"))
):
    return await mysql_permission_service.list_permissions(page, page_size, keyword)
```

- [ ] **Step 12: 提交路由变更**

```bash
cd backend && git add app/routers/auth.py && git commit -m "feat: 重写认证路由使用 MySQL 服务"
```

---

## Task 7: 创建 MySQL 初始化脚本

**Files:**
- Create: `backend/scripts/init_db_mysql.py`

- [ ] **Step 1: 创建初始化脚本框架**

创建 `backend/scripts/init_db_mysql.py`：

```python
"""
MySQL 数据库初始化脚本
在服务启动前单独运行一次，初始化默认数据

使用方法：
    cd backend
    python scripts/init_db_mysql.py
"""
import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from app.database import init_mysql, close_mysql
from models_mysql.auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType
from tortoise.expressions import Q
import bcrypt


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
```

- [ ] **Step 2: 实现 init_default_permissions 函数**

```python
async def init_default_permissions():
    """初始化默认权限集（幂等：已存在则跳过）"""
    existing_count = await Permission.all().count()
    if existing_count > 0:
        logger.info(f"权限已存在（共 {existing_count} 条），跳过初始化")
        return {}

    menu_permissions = [
        {"code": "dashboard.view", "name": "工作台查看", "type": PermissionType.MENU, "sort_order": 1, "parent_id": None},
        {"code": "chat.view", "name": "智能助手查看", "type": PermissionType.MENU, "sort_order": 2, "parent_id": None},
        {"code": "customer.menu", "name": "客户管理菜单", "type": PermissionType.MENU, "sort_order": 10, "parent_id": None},
        {"code": "product.menu", "name": "商品管理菜单", "type": PermissionType.MENU, "sort_order": 15, "parent_id": None},
        {"code": "category.menu", "name": "分类管理菜单", "type": PermissionType.MENU, "sort_order": 16, "parent_id": None},
        {"code": "order.menu", "name": "订单管理菜单", "type": PermissionType.MENU, "sort_order": 20, "parent_id": None},
        {"code": "procurement.menu", "name": "采购管理菜单", "type": PermissionType.MENU, "sort_order": 30, "parent_id": None},
        {"code": "receivable.menu", "name": "应收款管理菜单", "type": PermissionType.MENU, "sort_order": 40, "parent_id": None},
        {"code": "inventory.menu", "name": "库存管理菜单", "type": PermissionType.MENU, "sort_order": 50, "parent_id": None},
        {"code": "warehouse.menu", "name": "仓库管理菜单", "type": PermissionType.MENU, "sort_order": 60, "parent_id": None},
        {"code": "knowledge.view", "name": "知识库查看", "type": PermissionType.MENU, "sort_order": 70, "parent_id": None},
        {"code": "finance.menu", "name": "财务管理菜单", "type": PermissionType.MENU, "sort_order": 80, "parent_id": None},
        {"code": "user.menu", "name": "用户管理菜单", "type": PermissionType.MENU, "sort_order": 90, "parent_id": None},
        {"code": "role.menu", "name": "角色管理菜单", "type": PermissionType.MENU, "sort_order": 100, "parent_id": None},
        {"code": "permission.menu", "name": "权限管理菜单", "type": PermissionType.MENU, "sort_order": 110, "parent_id": None},
        {"code": "intelligent.settings.view", "name": "智能设置查看", "type": PermissionType.MENU, "sort_order": 120, "parent_id": None},
    ]

    button_permissions = [
        {"code": "customer.view", "name": "客户查看", "type": PermissionType.MENU, "sort_order": 11},
        {"code": "customer.create", "name": "客户创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 12},
        {"code": "customer.edit", "name": "客户编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 13},
        {"code": "customer.delete", "name": "客户删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 14},
        {"code": "product.view", "name": "商品查看", "type": PermissionType.MENU, "sort_order": 16},
        {"code": "product.create", "name": "商品创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 17},
        {"code": "product.edit", "name": "商品编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 18},
        {"code": "product.delete", "name": "商品删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 19},
        {"code": "category.view", "name": "分类查看", "type": PermissionType.MENU, "sort_order": 20},
        {"code": "category.create", "name": "分类创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 21},
        {"code": "category.edit", "name": "分类编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 22},
        {"code": "category.delete", "name": "分类删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 23},
        {"code": "order.view", "name": "订单查看", "type": PermissionType.MENU, "sort_order": 25},
        {"code": "order.create", "name": "订单创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 26},
        {"code": "order.edit", "name": "订单编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 27},
        {"code": "order.delete", "name": "订单删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 28},
        {"code": "order.confirm", "name": "订单确认", "type": PermissionType.BUTTON_TOOLS, "sort_order": 29},
        {"code": "procurement.view", "name": "采购单查看", "type": PermissionType.MENU, "sort_order": 35},
        {"code": "procurement.create", "name": "采购单创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 36},
        {"code": "procurement.edit", "name": "采购单编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 37},
        {"code": "procurement.delete", "name": "采购单删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 38},
        {"code": "receivable.view", "name": "应收单查看", "type": PermissionType.MENU, "sort_order": 45},
        {"code": "receivable.create", "name": "应收单创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 46},
        {"code": "receivable.edit", "name": "应收单编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 47},
        {"code": "receivable.delete", "name": "应收单删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 48},
        {"code": "receivable.record", "name": "收款记录", "type": PermissionType.BUTTON_TOOLS, "sort_order": 49},
        {"code": "inventory.stock.view", "name": "库存查看", "type": PermissionType.MENU, "sort_order": 55},
        {"code": "inventory.stock.edit", "name": "库存编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 56},
        {"code": "inventory.check.view", "name": "盘点查看", "type": PermissionType.MENU, "sort_order": 57},
        {"code": "inventory.check.edit", "name": "盘点编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 58},
        {"code": "warehouse.view", "name": "仓库查看", "type": PermissionType.MENU, "sort_order": 65},
        {"code": "warehouse.create", "name": "仓库创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 66},
        {"code": "warehouse.edit", "name": "仓库编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 67},
        {"code": "warehouse.delete", "name": "仓库删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 68},
        {"code": "finance.invoice.view", "name": "发票查看", "type": PermissionType.MENU, "sort_order": 85},
        {"code": "finance.payment.view", "name": "付款查看", "type": PermissionType.MENU, "sort_order": 86},
        {"code": "finance.report.view", "name": "报表查看", "type": PermissionType.MENU, "sort_order": 87},
        {"code": "user.view", "name": "用户查看", "type": PermissionType.MENU, "sort_order": 95},
        {"code": "user.create", "name": "用户创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 96},
        {"code": "user.edit", "name": "用户编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 97},
        {"code": "user.delete", "name": "用户删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 98},
        {"code": "user.reset-password", "name": "密码重置", "type": PermissionType.BUTTON_TOOLS, "sort_order": 99},
        {"code": "role.view", "name": "角色查看", "type": PermissionType.MENU, "sort_order": 105},
        {"code": "role.create", "name": "角色创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 106},
        {"code": "role.edit", "name": "角色编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 107},
        {"code": "role.delete", "name": "角色删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 108},
        {"code": "permission.view", "name": "权限查看", "type": PermissionType.MENU, "sort_order": 115},
        {"code": "intelligent.settings.edit", "name": "智能设置编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 125},
    ]

    # 创建菜单权限
    menu_id_map = {}
    for perm in menu_permissions:
        p = await Permission.create(**perm)
        menu_id_map[perm["code"]] = p.id

    # 创建按钮权限并关联父菜单
    code_prefix_map = {
        "customer": "customer.menu",
        "product": "product.menu",
        "category": "category.menu",
        "order": "order.menu",
        "procurement": "procurement.menu",
        "receivable": "receivable.menu",
        "inventory": "inventory.menu",
        "warehouse": "warehouse.menu",
        "finance": "finance.menu",
        "user": "user.menu",
        "role": "role.menu",
        "permission": "permission.menu",
    }

    for perm in button_permissions:
        prefix = perm["code"].split(".")[0]
        parent_code = code_prefix_map.get(prefix)
        if parent_code and parent_code in menu_id_map:
            perm["parent_id"] = menu_id_map[parent_code]
        else:
            perm["parent_id"] = None
        await Permission.create(**perm)

    logger.info(f"初始化默认权限成功")
    return menu_id_map
```

- [ ] **Step 3: 实现 init_super_admin_group 函数**

```python
async def init_super_admin_group(menu_id_map: dict):
    """初始化超级管理员角色"""
    existing = await Role.filter(code="super_admin").first()
    all_perms = await Permission.all()
    all_perm_ids = [p.id for p in all_perms]

    if existing:
        if not await existing.permissions.all():
            await existing.permissions.add(*all_perms)
            logger.info("更新超级管理员角色权限成功")
        else:
            logger.info("固化超级管理员角色已存在且已有权限，跳过初始化")
        return

    role = await Role.create(
        code="super_admin",
        name="超级管理员",
        description="系统超级管理员，拥有所有权限",
        is_fixed=True,
        status=RoleStatus.ACTIVE,
    )
    await role.permissions.add(*all_perms)
    logger.info("创建超级管理员角色成功")
```

- [ ] **Step 4: 实现 init_warehouse_admin_group 函数**

```python
async def init_warehouse_admin_group():
    """初始化仓库管理员角色"""
    existing = await Role.filter(code="warehouse_admin").first()
    if existing:
        logger.info("固化仓库管理员角色已存在，跳过初始化")
        return

    warehouse_perms = await Permission.filter(
        code__in=[
            "warehouse.view", "warehouse.create", "warehouse.edit", "warehouse.delete",
            "inventory.stock.view", "inventory.stock.edit",
            "inventory.check.view", "inventory.check.edit",
        ]
    ).all()

    role = await Role.create(
        code="warehouse_admin",
        name="仓库管理员",
        description="仓库管理员，负责仓库日常管理",
        is_fixed=True,
        status=RoleStatus.ACTIVE,
    )
    await role.permissions.add(*warehouse_perms)
    logger.info(f"创建仓库管理员角色成功")
```

- [ ] **Step 5: 实现 init_purchaser_group 函数**

```python
async def init_purchaser_group():
    """初始化采购组角色"""
    existing = await Role.filter(code="purchaser_group").first()
    if existing:
        logger.info("固化采购组角色已存在，跳过初始化")
        return

    purchaser_perms = await Permission.filter(
        code__in=[
            "procurement.view", "procurement.create", "procurement.edit",
            "order.view",
        ]
    ).all()

    role = await Role.create(
        code="purchaser_group",
        name="采购组",
        description="采购组成员，负责品牌商品采购",
        is_fixed=True,
        status=RoleStatus.ACTIVE,
    )
    await role.permissions.add(*purchaser_perms)
    logger.info("创建采购组角色成功")
```

- [ ] **Step 6: 实现 init_admin_user 函数**

```python
async def init_admin_user():
    """初始化管理员账号"""
    existing = await User.filter(username="admin").first()
    if existing:
        logger.info("管理员账号已存在，跳过")
        return

    super_admin_role = await Role.filter(code="super_admin").first()
    if not super_admin_role:
        logger.error("超级管理员角色不存在，请先初始化固化角色")
        return

    user = await User.create(
        username="admin",
        password=get_password_hash("admin123"),
        email="admin@example.com",
        full_name="系统管理员",
        status=UserStatus.ACTIVE,
    )
    await user.roles.add(super_admin_role)
    logger.info("创建管理员账号成功，绑定超级管理员角色")
```

- [ ] **Step 7: 实现 main 函数**

```python
async def main():
    """执行所有初始化"""
    logger.info("开始初始化 MySQL 数据库...")

    try:
        await init_mysql()
        menu_id_map = await init_default_permissions()
        await init_super_admin_group(menu_id_map)
        await init_warehouse_admin_group()
        await init_purchaser_group()
        await init_admin_user()
        logger.info("MySQL 数据库初始化完成")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
    finally:
        await close_mysql()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 8: 提交初始化脚本**

```bash
cd backend && git add scripts/init_db_mysql.py && git commit -m "feat: 添加 MySQL 数据库初始化脚本"
```

---

## Task 8: 前端 ID 类型适配

**Files:**
- Modify: `web/src/components/workspace/UserManagement.vue`
- Modify: `web/src/components/workspace/RoleManagement.vue`
- Modify: `web/src/components/workspace/PermissionManagement.vue`
- Modify: `web/src/hooks/usePermission.ts`

- [ ] **Step 1: 更新 UserManagement.vue 的 User 接口**

修改 `web/src/components/workspace/UserManagement.vue` 中的 interface：

```typescript
interface User {
  id: number
  username: string
  email: string
  phone?: string
  full_name?: string
  role_ids?: number[]
  role_names?: string[]
  status: string
  created_at?: string
}

interface Role {
  id: number
  name: string
  code: string
}
```

- [ ] **Step 2: 更新 UserManagement.vue 的 ref 类型**

修改相关的 ref 类型：

```typescript
const deleteTargetId = ref<number | null>(null)
const resetPwdTarget = ref<{ id: number; username: string } | null>(null)
```

- [ ] **Step 3: 更新 RoleManagement.vue 的接口**

修改 `web/src/components/workspace/RoleManagement.vue` 中的 interface：

```typescript
interface Role {
  id: number
  code: string
  name: string
  description?: string
  is_fixed?: boolean
  status: string
  permissions?: Permission[]
}

interface Permission {
  id: number
  code: string
  name: string
}
```

- [ ] **Step 4: 更新 PermissionManagement.vue 的接口**

修改 `web/src/components/workspace/PermissionManagement.vue` 中的 interface：

```typescript
interface Permission {
  id: number
  code: string
  name: string
  type: string
  path?: string
  parent_id?: number | null
  children?: Permission[]
}
```

- [ ] **Step 5: 更新 usePermission.ts 的接口**

修改 `web/src/hooks/usePermission.ts` 中的 interface：

```typescript
interface Permission {
  id: number
  code: string
  name: string
  type: 'menu' | 'button' | 'api'
  path?: string
  parent_id?: number | null
  children?: Permission[]
}
```

- [ ] **Step 6: 提交前端变更**

```bash
cd web && git add src/components/workspace/UserManagement.vue src/components/workspace/RoleManagement.vue src/components/workspace/PermissionManagement.vue src/hooks/usePermission.ts && git commit -m "feat: 更新用户权限相关组件的 ID 类型为 number"
```

---

## Task 9: 测试与验证

**Files:**
- Test: 手动测试

- [ ] **Step 1: 安装依赖**

```bash
cd backend && pip install -r requirements.txt
```

- [ ] **Step 2: 配置 MySQL 连接**

确保 MySQL 数据库已创建，并在 `.env` 中配置正确的连接参数。

- [ ] **Step 3: 运行初始化脚本**

```bash
cd backend && python scripts/init_db_mysql.py
```

Expected: 输出 "MySQL 数据库初始化完成"

- [ ] **Step 4: 启动后端服务**

```bash
cd backend && python main.py
```

Expected: 服务正常启动，MySQL 和 MongoDB 连接成功

- [ ] **Step 5: 测试登录接口**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Expected: 返回 access_token 和 user 信息，user.id 为整数

- [ ] **Step 6: 测试用户列表接口**

使用返回的 token：

```bash
curl http://localhost:8000/api/v1/auth/users/ \
  -H "Authorization: Bearer <token>"
```

Expected: 返回用户列表，id 为整数

- [ ] **Step 7: 前端测试**

启动前端开发服务器，登录并测试用户管理、角色管理、权限管理页面。

Expected: 所有功能正常，无类型错误

---

## 自检清单

**1. Spec 覆盖检查：**

| 需求 | 任务 |
|------|------|
| MySQL 数据库连接 | Task 3 |
| User 模型 | Task 2 |
| Role 模型 | Task 2 |
| Permission 模型 | Task 2 |
| UserService | Task 4 |
| RoleService | Task 5 |
| PermissionService | Task 5 |
| API 路由 | Task 6 |
| 初始化脚本 | Task 7 |
| 前端 ID 类型适配 | Task 8 |
| 数据库迁移工具 | 未实现（Tortoise ORM 自动生成 schema）|

**2. 占位符检查：** 无 TBD、TODO、implement later 等占位符

**3. 类型一致性检查：**
- User.id: int → 前端 number ✓
- Role.id: int → 前端 number ✓
- Permission.id: int → 前端 number ✓
- Permission.parent_id: int → 前端 number ✓
