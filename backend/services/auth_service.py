from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import bcrypt
from jose import JWTError, jwt

from config import settings
from models_mysql.auth import User, Role, Permission, UserStatus as MySQLUserStatus, RoleStatus
from tortoise.expressions import Q

logger = logging.getLogger(__name__)


class MySQLUserService:
    """用户服务（MySQL 版）"""

    def _hash_password(self, password: str) -> str:
        """密码加密"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """密码验证"""
        if not hashed_password:
            return False
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    async def get_by_id(self, user_id: int) -> Optional[dict]:
        """根据 ID 获取用户"""
        user = await User.filter(id=user_id).prefetch_related("roles__permissions").first()
        if not user:
            return None
        return await self._format_user(user)

    async def get_by_username(self, username: str) -> Optional[dict]:
        """根据用户名获取用户"""
        user = await User.filter(username=username).prefetch_related("roles__permissions").first()
        if not user:
            return None
        return await self._format_user(user)

    async def _format_user(self, user: User) -> dict:
        """格式化用户数据，包含角色和权限"""
        roles = []
        all_permissions = []

        for role in user.roles:
            role_data = {
                "id": role.id,
                "code": role.code,
                "name": role.name,
                "description": role.description,
                "status": role.status.value if role.status else None,
                "permissions": []
            }
            for perm in role.permissions:
                perm_data = {
                    "id": perm.id,
                    "code": perm.code,
                    "name": perm.name,
                    "type": perm.type.value if perm.type else None,
                    "path": perm.path
                }
                role_data["permissions"].append(perm_data)
                if perm.code not in all_permissions:
                    all_permissions.append(perm.code)
            roles.append(role_data)

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "full_name": user.full_name,
            "avatar": user.avatar,
            "status": user.status.value if user.status else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "roles": roles,
            "permissions": all_permissions
        }

    async def create_user(self, user_data: Dict[str, Any]) -> int:
        """创建用户，返回用户 ID"""
        username = user_data.get("username")
        if not username:
            raise ValueError("用户名不能为空")

        # 校验用户名唯一性
        existing = await User.filter(username=username).first()
        if existing:
            raise ValueError("用户名已存在")

        # 校验邮箱唯一性
        email = user_data.get("email")
        if email:
            existing = await User.filter(email=email).first()
            if existing:
                raise ValueError("邮箱已存在")

        # 校验手机号唯一性
        phone = user_data.get("phone")
        if phone:
            existing = await User.filter(phone=phone).first()
            if existing:
                raise ValueError("手机号已被使用")

        # 校验用户名格式
        if not username.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")

        # 密码加密
        password = user_data.get("password")
        if not password:
            raise ValueError("密码不能为空")
        hashed_password = self._hash_password(password)

        # 创建用户
        user = await User.create(
            username=username,
            password=hashed_password,
            email=email,
            phone=phone,
            full_name=user_data.get("full_name"),
            avatar=user_data.get("avatar"),
            status=MySQLUserStatus.ACTIVE
        )

        # 关联角色
        role_ids = user_data.get("role_ids", [])
        if role_ids:
            roles = await Role.filter(id__in=role_ids, status=RoleStatus.ACTIVE)
            if len(roles) != len(role_ids):
                found_ids = {r.id for r in roles}
                missing_ids = set(role_ids) - found_ids
                raise ValueError(f"角色ID {missing_ids} 不存在或已禁用")
            await user.roles.add(*roles)

        return user.id

    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """更新用户信息"""
        user = await User.filter(id=user_id).first()
        if not user:
            raise ValueError("用户不存在")

        # 校验邮箱唯一性
        email = user_data.get("email")
        if email:
            existing = await User.filter(email=email).exclude(id=user_id).first()
            if existing:
                raise ValueError("邮箱已被其他用户使用")

        # 校验手机号唯一性
        phone = user_data.get("phone")
        if phone:
            existing = await User.filter(phone=phone).exclude(id=user_id).first()
            if existing:
                raise ValueError("手机号已被其他用户使用")

        # 更新密码
        new_password = user_data.get("new_password")
        if new_password:
            user.password = self._hash_password(new_password)

        # 更新基本信息
        update_fields = ["email", "phone", "full_name", "avatar", "status"]
        for field in update_fields:
            if field in user_data:
                setattr(user, field, user_data[field])

        await user.save()

        # 更新角色关联
        role_ids = user_data.get("role_ids")
        if role_ids is not None:
            roles = await Role.filter(id__in=role_ids, status=RoleStatus.ACTIVE)
            if len(roles) != len(role_ids):
                found_ids = {r.id for r in roles}
                missing_ids = set(role_ids) - found_ids
                raise ValueError(f"角色ID {missing_ids} 不存在或已禁用")
            await user.roles.clear()
            await user.roles.add(*roles)

        return True

    async def delete(self, user_id: int) -> bool:
        """删除用户"""
        user = await User.filter(id=user_id).first()
        if not user:
            raise ValueError("用户不存在")

        await user.roles.clear()
        await user.delete()
        return True

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        role: Optional[str] = None
    ) -> dict:
        """获取用户列表"""
        query = User.all()

        # 状态过滤
        if status:
            query = query.filter(status=status)

        # 关键字搜索
        if keyword:
            query = query.filter(
                Q(username__icontains=keyword) |
                Q(full_name__icontains=keyword) |
                Q(email__icontains=keyword)
            )

        # 角色过滤
        if role:
            query = query.filter(roles__code=role)

        # 统计总数
        total = await query.count()

        # 分页查询
        offset = (page - 1) * page_size
        users = await query.prefetch_related("roles__permissions").offset(offset).limit(page_size).order_by("-created_at")

        # 格式化结果
        items = []
        for user in users:
            user_dict = await self._format_user(user)
            items.append(user_dict)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """用户认证，返回用户信息和 JWT Token"""
        user = await User.filter(username=username).prefetch_related("roles__permissions").first()
        if not user:
            return None
        if not self._verify_password(password, user.password):
            return None

        # 更新最后登录时间
        user.last_login = datetime.now()
        await user.save()

        user_dict = await self._format_user(user)

        # 生成 JWT Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self._create_access_token(
            data={
                "sub": str(user.id),
                "username": user.username,
                "roles": [role.code for role in user.roles],
                "permissions": user_dict.get("permissions", [])
            },
            expires_delta=access_token_expires
        )

        return {
            "user": user_dict,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = await User.filter(id=user_id).first()
        if not user:
            raise ValueError("用户不存在")

        if not self._verify_password(old_password, user.password):
            raise ValueError("旧密码错误")

        user.password = self._hash_password(new_password)
        await user.save()
        return True

    async def reset_password(self, user_id: int, new_password: str) -> bool:
        """重置密码"""
        user = await User.filter(id=user_id).first()
        if not user:
            raise ValueError("用户不存在")

        user.password = self._hash_password(new_password)
        await user.save()
        return True

    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """生成 JWT Token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt


class MySQLRoleService:
    """角色服务（MySQL 版）"""

    async def get_by_id(self, role_id: int) -> Optional[dict]:
        """根据 ID 获取角色"""
        role = await Role.filter(id=role_id).prefetch_related("permissions").first()
        if not role:
            return None
        return await self._format_role(role)

    async def get_by_code(self, code: str) -> Optional[dict]:
        """根据编码获取角色"""
        role = await Role.filter(code=code).prefetch_related("permissions").first()
        if not role:
            return None
        return await self._format_role(role)

    async def _format_role(self, role: Role) -> dict:
        """格式化角色数据"""
        # 直接使用已预加载的 permissions，无需再次查询
        return {
            "id": role.id,
            "code": role.code,
            "name": role.name,
            "description": role.description,
            "is_fixed": role.is_fixed,
            "status": role.status.value if role.status else None,
            "permissions": [{"id": p.id, "code": p.code, "name": p.name} for p in role.permissions],
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        }

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
            if len(permissions) != len(permission_ids):
                found_ids = {p.id for p in permissions}
                missing_ids = set(permission_ids) - found_ids
                raise ValueError(f"权限ID {missing_ids} 不存在")
            await role.permissions.add(*permissions)

        return await self._format_role(role)

    async def update_role(self, role_id: int, data: Dict[str, Any]) -> bool:
        """更新角色"""
        role = await Role.filter(id=role_id).first()
        if not role:
            raise ValueError("角色不存在")

        if role.is_fixed:
            raise ValueError("固化角色不允许修改")

        for key in ["name", "description", "status"]:
            if key in data:
                setattr(role, key, data[key])

        await role.save()

        if "permission_ids" in data:
            await role.permissions.clear()
            if data["permission_ids"]:
                permissions = await Permission.filter(id__in=data["permission_ids"])
                if len(permissions) != len(data["permission_ids"]):
                    found_ids = {p.id for p in permissions}
                    missing_ids = set(data["permission_ids"]) - found_ids
                    raise ValueError(f"权限ID {missing_ids} 不存在")
                await role.permissions.add(*permissions)

        return True

    async def delete(self, role_id: int) -> bool:
        """删除角色"""
        role = await Role.filter(id=role_id).first()
        if not role:
            raise ValueError("角色不存在")

        if role.is_fixed:
            raise ValueError("固化角色不允许删除")

        await role.permissions.clear()
        await role.delete()
        return True

    async def list_roles(
        self, page: int = 1, page_size: int = 20,
        status: Optional[str] = None, keyword: Optional[str] = None
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
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
            "items": items
        }


class MySQLPermissionService:
    """权限服务（MySQL 版）"""

    async def get_by_id(self, permission_id: int) -> Optional[dict]:
        """根据 ID 获取权限"""
        perm = await Permission.filter(id=permission_id).first()
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

    async def list_permissions(
        self, page: int = 1, page_size: int = 20, keyword: Optional[str] = None
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
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
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


# MySQL 版服务实例
mysql_user_service = MySQLUserService()
mysql_role_service = MySQLRoleService()
mysql_permission_service = MySQLPermissionService()