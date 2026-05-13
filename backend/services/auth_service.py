from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
import bcrypt
from bson import ObjectId
from jose import JWTError, jwt

from config import settings
from models.auth import UserStatus
from models_mysql.auth import User, Role, Permission, UserStatus as MySQLUserStatus, RoleStatus
from tortoise.expressions import Q
from .base_service import BaseService
from validators.auth_validator import (
    USER_CREATE_CONFIG,
    USER_UPDATE_CONFIG,
    ROLE_CREATE_CONFIG,
    ROLE_UPDATE_CONFIG,
    PASSWORD_CHANGE_CONFIG,
    PASSWORD_RESET_CONFIG,
)

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    def __init__(self):
        super().__init__("users")

    @property
    def roles_collection(self):
        return self.db["roles"]

    @property
    def permissions_collection(self):
        return self.db["permissions"]

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def get_password_hash(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        user = await self.find_one({"username": username})
        if not user:
            return None
        if not self.verify_password(password, user.get("password", "")):
            return None
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        user = await self.get_by_id(user_id)
        if user:
            roles, all_permissions = await self._get_user_roles_optimized(user["role_ids"])
            user["roles"] = roles
            user["permissions"] = all_permissions
        return user

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        user = await self.find_one({"username": username})
        if user:
            roles, all_permissions = await self._get_user_roles_optimized(user["role_ids"])
            user["roles"] = roles
            user["permissions"] = all_permissions
        return user

    async def _get_user_roles_optimized(self, role_ids: List[str]) -> tuple[List[dict], List[str]]:
        if not role_ids:
            return [], []

        roles = []
        all_permissions = []
        all_permission_ids = []

        try:
            cursor = self.roles_collection.find({
                "_id": {"$in": [ObjectId(rid) for rid in role_ids]}
            })
            async for role in cursor:
                role["id"] = str(role.pop("_id"))
                if role.get("permission_ids"):
                    all_permission_ids.extend(role["permission_ids"])
                roles.append(role)
        except Exception:
            pass

        if all_permission_ids:
            try:
                unique_perm_ids = list(set(all_permission_ids))
                perm_cursor = self.permissions_collection.find({
                    "_id": {"$in": [ObjectId(pid) for pid in unique_perm_ids]}
                })
                perm_map = {}
                async for perm in perm_cursor:
                    perm_id = str(perm.pop("_id"))
                    perm["id"] = perm_id
                    perm_map[perm_id] = perm
                    all_permissions.append(perm["code"])

                for role in roles:
                    role_perms = []
                    for pid in role.get("permission_ids", []):
                        if pid in perm_map:
                            role_perms.append(perm_map[pid])
                    role["permissions"] = role_perms
            except Exception:
                pass

        return roles, all_permissions

    def validate_user_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(data, USER_CREATE_CONFIG)

    def validate_user_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(data, USER_UPDATE_CONFIG)

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        valid, errors = self.validate_user_create(user_data)
        if not valid:
            raise ValueError(errors)

        username = user_data.get("username")
        existing_user = await self.find_one({"username": username})
        if existing_user:
            raise ValueError("用户名已存在")

        email = user_data.get("email")
        if email:
            existing_email = await self.find_one({"email": email})
            if existing_email:
                raise ValueError("邮箱已存在")

        phone = user_data.get("phone")
        if phone:
            existing_phone = await self.find_one({"phone": phone})
            if existing_phone:
                raise ValueError("手机号已被使用")

        if not username.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")

        password = user_data.get("password")

        data = dict(user_data)
        data["password"] = self.get_password_hash(password)
        data["status"] = UserStatus.ACTIVE.value

        role_ids = data.get("role_ids", [])
        if role_ids:
            role_ids = list(set(role_ids))
            cursor = self.roles_collection.find({
                "_id": {"$in": [ObjectId(rid) for rid in role_ids]}
            })
            found_ids = set()
            async for role in cursor:
                found_ids.add(str(role["_id"]))
            for rid in role_ids:
                if rid not in found_ids:
                    raise ValueError(f"角色ID {rid} 不存在")

        return await self.create(data)

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        valid, errors = self.validate_user_update(user_data)
        if not valid:
            raise ValueError(errors)

        email = user_data.get("email")
        if email:
            existing = await self.find_one({"email": email, "_id": {"$ne": ObjectId(user_id)}})
            if existing:
                raise ValueError("邮箱已被其他用户使用")

        phone = user_data.get("phone")
        if phone:
            existing = await self.find_one({"phone": phone, "_id": {"$ne": ObjectId(user_id)}})
            if existing:
                raise ValueError("手机号已被其他用户使用")

        new_password = user_data.get("new_password")
        if new_password:
            hashed_password = self.get_password_hash(new_password)
            user_data["password"] = hashed_password
            del user_data["new_password"]

        role_ids = user_data.get("role_ids")
        if role_ids:
            role_ids = list(set(role_ids))
            cursor = self.roles_collection.find({
                "_id": {"$in": [ObjectId(rid) for rid in role_ids]}
            })
            found_ids = set()
            async for role in cursor:
                found_ids.add(str(role["_id"]))
            for rid in role_ids:
                if rid not in found_ids:
                    raise ValueError(f"角色ID {rid} 不存在")

        logger.info(f"更新用户 {user_id} 的角色为 {user_data}")
        return await self.update(user_id, user_data)

    def validate_password_change(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(data, PASSWORD_CHANGE_CONFIG)

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        valid, errors = self.validate_password_change({
            "old_password": old_password,
            "new_password": new_password
        })
        if not valid:
            raise ValueError(errors)

        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        if not self.verify_password(old_password, user.get("password", "")):
            raise ValueError("旧密码错误")

        hashed_password = self.get_password_hash(new_password)
        return await self.update(user_id, {"password": hashed_password})

    def validate_password_reset(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(data, PASSWORD_RESET_CONFIG)

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        valid, errors = self.validate_password_reset({"new_password": new_password})
        if not valid:
            raise ValueError(errors)

        logger.info(f"重置用户 {user_id} 的密码为 {new_password}")
        hashed_password = self.get_password_hash(new_password)
        return await self.update(user_id, {"password": hashed_password})

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        role: Optional[str] = None
    ) -> dict:
        filters = {}
        if status:
            filters["status"] = status
        if keyword:
            filters["$or"] = [
                {"username": {"$regex": keyword, "$options": "i"}},
                {"full_name": {"$regex": keyword, "$options": "i"}},
                {"email": {"$regex": keyword, "$options": "i"}}
            ]

        result = await self.list(page, page_size, filters, "created_at", -1)

        role_ids_set = set()
        for user in result["items"]:
            user_role_ids = user.get("role_ids", [])
            if isinstance(user_role_ids, list):
                role_ids_set.update(user_role_ids)

        if role_ids_set:
            roles_map, all_perms = await self._get_user_roles_optimized(list(role_ids_set))
            roles_by_id = {role["id"]: role for role in roles_map}

            for user in result["items"]:
                user_role_ids = user.get("role_ids", [])
                user_roles = []
                user_perm_codes = []
                for rid in user_role_ids:
                    if rid in roles_by_id:
                        user_roles.append(roles_by_id[rid])
                        for p in roles_by_id[rid].get("permissions", []):
                            if p.get("code") and p["code"] not in user_perm_codes:
                                user_perm_codes.append(p["code"])
                user["roles"] = user_roles
                user["permissions"] = user_perm_codes

        return result


class RoleService(BaseService):
    def __init__(self):
        super().__init__("roles")

    @property
    def permissions_collection(self):
        return self.db["permissions"]

    def validate_role_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(data, ROLE_CREATE_CONFIG)

    def validate_role_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(data, ROLE_UPDATE_CONFIG)

    async def create_role(self, role_data: Dict[str, Any]) -> dict:
        valid, errors = self.validate_role_create(role_data)
        if not valid:
            raise ValueError(errors)

        code = role_data.get("code")
        existing_role = await self.find_one({"code": code})
        if existing_role:
            raise ValueError("角色编码已存在")

        permission_ids = role_data.get("permission_ids", [])
        if permission_ids:
            perm_ids = list(set(permission_ids))
            cursor = self.permissions_collection.find({
                "_id": {"$in": [ObjectId(pid) for pid in perm_ids]}
            })
            found_ids = set()
            async for perm in cursor:
                found_ids.add(str(perm["_id"]))
            for pid in perm_ids:
                if pid not in found_ids:
                    raise ValueError(f"权限ID {pid} 不存在")

        data = dict(role_data)
        data["id"] = await self.create(data)
        if "_id" in data:
            data.pop("_id")
        return data

    async def update_role(self, role_id: str, role_data: Dict[str, Any]) -> bool:
        valid, errors = self.validate_role_update(role_data)
        if not valid:
            raise ValueError(errors)

        permission_ids = role_data.get("permission_ids")
        if permission_ids:
            perm_ids = list(set(permission_ids))
            cursor = self.permissions_collection.find({
                "_id": {"$in": [ObjectId(pid) for pid in perm_ids]}
            })
            found_ids = set()
            async for perm in cursor:
                found_ids.add(str(perm["_id"]))
            for pid in perm_ids:
                if pid not in found_ids:
                    raise ValueError(f"权限ID {pid} 不存在")

        return await self.update(role_id, role_data)

    async def list_roles(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> dict:
        filters = {}
        if status:
            filters["status"] = status
        if keyword:
            filters["$or"] = [
                {"code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ]

        result = await self.list(page, page_size, filters, "created_at", -1)

        all_perm_ids = []
        for role in result["items"]:
            if role.get("permission_ids"):
                all_perm_ids.extend(role["permission_ids"])

        if all_perm_ids:
            from bson import ObjectId
            unique_perm_ids = list(set(all_perm_ids))
            perm_cursor = self.permissions_collection.find({
                "_id": {"$in": [ObjectId(pid) for pid in unique_perm_ids]}
            })
            perm_map = {}
            async for perm in perm_cursor:
                perm["id"] = str(perm.pop("_id"))
                perm_map[perm["id"]] = perm

            for role in result["items"]:
                role_perms = []
                for pid in role.get("permission_ids", []):
                    if pid in perm_map:
                        role_perms.append(perm_map[pid])
                role["permissions"] = role_perms

        return result

class PermissionService(BaseService):
    def __init__(self):
        super().__init__("permissions")

    async def list_permissions(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> dict:
        filters = {}
        if keyword:
            filters["$or"] = [
                {"code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ]

        return await self.list(page, page_size, filters, "sort_order", 1)

    async def get_permission_tree(self) -> List[dict]:
        permissions = await self.collection.find({}).sort("sort_order", 1).to_list(length=None)

        perm_dict = {}
        for perm in permissions:
            perm["id"] = str(perm.pop("_id"))
            perm["children"] = []
            perm_dict[perm["id"]] = perm

        roots = []
        for perm in permissions:
            parent_id = perm.get("parent_id")
            if parent_id and parent_id in perm_dict:
                perm_dict[parent_id]["children"].append(perm)
            else:
                roots.append(perm)

        return roots


auth_service = AuthService()
role_service = RoleService()
permission_service = PermissionService()


# ============ MySQL 版服务（Tortoise ORM）============

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
        permissions = await role.permissions.all()
        return {
            "id": role.id,
            "code": role.code,
            "name": role.name,
            "description": role.description,
            "is_fixed": role.is_fixed,
            "status": role.status.value if role.status else None,
            "permissions": [{"id": p.id, "code": p.code, "name": p.name} for p in permissions],
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
            await role.permissions.add(*permissions)

        return await self._format_role(role)

    async def update_role(self, role_id: int, data: Dict[str, Any]) -> bool:
        """更新角色"""
        role = await Role.filter(id=role_id).first()
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

    async def delete(self, role_id: int) -> bool:
        """删除角色"""
        role = await Role.filter(id=role_id).first()
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


# MySQL 版服务实例
mysql_user_service = MySQLUserService()
mysql_role_service = MySQLRoleService()
mysql_permission_service = MySQLPermissionService()
