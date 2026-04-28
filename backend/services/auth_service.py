from datetime import datetime, timedelta
from typing import Optional, List
import logging
import bcrypt
from bson import ObjectId
from jose import JWTError, jwt

from config import settings
from models.auth import (
    User, UserCreate, UserUpdate, UserStatus,
    Role, RoleCreate, RoleUpdate,
)
from .base_service import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """认证服务"""

    def __init__(self):
        super().__init__("users")

    @property
    def roles_collection(self):
        return self.db["roles"]

    @property
    def permissions_collection(self):
        return self.db["permissions"]

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        if not hashed_password:
            return False
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """认证用户"""
        user = await self.find_one({"username": username})
        if not user:
            return None
        if not self.verify_password(password, user.get("password", "")):
            return None
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        user = await self.get_by_id(user_id)
        if user:
            # 加载用户角色
            roles, all_permissions = await self._get_user_roles_optimized(user["role_ids"])
            user["roles"] = roles
            user["permissions"] = all_permissions
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user = await self.find_one({"username": username})
        if user:
            roles, all_permissions = await self._get_user_roles_optimized(user["role_ids"])
            user["roles"] = roles
            user["permissions"] = all_permissions
        return user


    async def _get_user_roles_optimized(self, role_ids: List[str]) -> tuple[List[dict], List[str]]:
        """批量获取用户角色及所有权限（优化版）

        Returns:
            tuple: (roles_with_permissions, all_permission_codes)
        """
        if not role_ids:
            return [], []

        from bson import ObjectId
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

    async def create_user(self, user_data: UserCreate) -> str:
        """创建用户"""
        existing_user = await self.find_one({"username": user_data.username})
        if existing_user:
            raise ValueError("用户名已存在")

        if user_data.email:
            existing_email = await self.find_one({"email": user_data.email})
            if existing_email:
                raise ValueError("邮箱已存在")

        data = user_data.model_dump()
        data["password"] = self.get_password_hash(data["password"])
        data["status"] = UserStatus.ACTIVE.value

        if data.get("role_ids"):
            role_ids = list(set(data["role_ids"]))
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

    async def update_user(self, user_id: str, user_data: UserUpdate) -> bool:
        """更新用户信息"""
        data = user_data.model_dump(exclude_unset=True)

        if "new_password" in data and data["new_password"]:
            hashed_password = self.get_password_hash(data["new_password"])
            data["password"] = hashed_password
            del data["new_password"]

        if "role_ids" in data and data["role_ids"]:
            role_ids = list(set(data["role_ids"]))
            cursor = self.roles_collection.find({
                "_id": {"$in": [ObjectId(rid) for rid in role_ids]}
            })
            found_ids = set()
            async for role in cursor:
                found_ids.add(str(role["_id"]))
            for rid in role_ids:
                if rid not in found_ids:
                    raise ValueError(f"角色ID {rid} 不存在")

        logger.info(f"更新用户 {user_id} 的角色为 {data}")
        return await self.update(user_id, data)

    async def change_password(self, user_id: str, new_password: str) -> bool:
        """修改密码"""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        hashed_password = self.get_password_hash(new_password)
        return await self.update(user_id, {"password": hashed_password})

    async def reset_password(self, user_id: str, new_password: str) -> bool:
        """重置密码（管理员操作）"""
        logger.info(f"重置用户 {user_id} 的密码为 {new_password}")
        hashed_password = self.get_password_hash(new_password)
        return await self.update(user_id, {"password": hashed_password})

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> dict:
        """分页查询用户列表"""
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
    """角色服务"""

    def __init__(self):
        super().__init__("roles")

    @property
    def permissions_collection(self):
        return self.db["permissions"]

    async def create_role(self, role_data: RoleCreate) -> str:
        """创建角色"""
        existing_role = await self.find_one({"code": role_data.code})
        if existing_role:
            raise ValueError("角色编码已存在")

        if role_data.permission_ids:
            perm_ids = list(set(role_data.permission_ids))
            from bson import ObjectId
            cursor = self.permissions_collection.find({
                "_id": {"$in": [ObjectId(pid) for pid in perm_ids]}
            })
            found_ids = set()
            async for perm in cursor:
                found_ids.add(str(perm["_id"]))
            for pid in perm_ids:
                if pid not in found_ids:
                    raise ValueError(f"权限ID {pid} 不存在")

        data = role_data.model_dump()
        data["id"] = await self.create(data)
        return data

    async def update_role(self, role_id: str, role_data: RoleUpdate) -> bool:
        """更新角色"""
        data = role_data.model_dump(exclude_unset=True)

        if "permission_ids" in data and data["permission_ids"]:
            perm_ids = list(set(data["permission_ids"]))
            from bson import ObjectId
            cursor = self.permissions_collection.find({
                "_id": {"$in": [ObjectId(pid) for pid in perm_ids]}
            })
            found_ids = set()
            async for perm in cursor:
                found_ids.add(str(perm["_id"]))
            for pid in perm_ids:
                if pid not in found_ids:
                    raise ValueError(f"权限ID {pid} 不存在")

        return await self.update(role_id, data)

    async def list_roles(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> dict:
        """分页查询角色列表"""
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
    """权限服务"""

    def __init__(self):
        super().__init__("permissions")

    async def list_permissions(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> dict:
        """分页查询权限列表"""
        filters = {}
        if keyword:
            filters["$or"] = [
                {"code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ]

        return await self.list(page, page_size, filters, "sort_order", 1)

    async def get_permission_tree(self) -> List[dict]:
        """获取权限树形结构"""
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


# 全局实例
auth_service = AuthService()
role_service = RoleService()
permission_service = PermissionService()
