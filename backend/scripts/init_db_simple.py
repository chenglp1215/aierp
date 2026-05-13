"""
MySQL 数据库初始化脚本（简化版）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from urllib.parse import quote_plus
import bcrypt

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from tortoise import Tortoise
from config import settings
from models_mysql.auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType

encoded_password = quote_plus(settings.MYSQL_PASSWORD)
db_url = f"mysql://{settings.MYSQL_USER}:{encoded_password}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"

SUPER_ADMIN_CODE = "super_admin"


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def init_default_permissions():
    try:
        existing_count = await Permission.all().count()
        if existing_count > 0:
            logger.info(f"权限已存在（共 {existing_count} 条），跳过初始化")
            return

        menu_permissions = [
            {"code": "dashboard.view", "name": "工作台查看", "type": PermissionType.MENU, "sort_order": 1},
            {"code": "chat.view", "name": "智能助手查看", "type": PermissionType.MENU, "sort_order": 2},
            {"code": "customer.menu", "name": "客户管理菜单", "type": PermissionType.MENU, "sort_order": 10},
            {"code": "product.menu", "name": "商品管理菜单", "type": PermissionType.MENU, "sort_order": 15},
            {"code": "category.menu", "name": "分类管理菜单", "type": PermissionType.MENU, "sort_order": 16},
            {"code": "order.menu", "name": "订单管理菜单", "type": PermissionType.MENU, "sort_order": 20},
            {"code": "procurement.menu", "name": "采购管理菜单", "type": PermissionType.MENU, "sort_order": 30},
            {"code": "receivable.menu", "name": "应收款管理菜单", "type": PermissionType.MENU, "sort_order": 40},
            {"code": "inventory.menu", "name": "库存管理菜单", "type": PermissionType.MENU, "sort_order": 50},
            {"code": "warehouse.menu", "name": "仓库管理菜单", "type": PermissionType.MENU, "sort_order": 60},
            {"code": "knowledge.view", "name": "知识库查看", "type": PermissionType.MENU, "sort_order": 70},
            {"code": "finance.menu", "name": "财务管理菜单", "type": PermissionType.MENU, "sort_order": 80},
            {"code": "user.menu", "name": "用户管理菜单", "type": PermissionType.MENU, "sort_order": 90},
            {"code": "role.menu", "name": "角色管理菜单", "type": PermissionType.MENU, "sort_order": 100},
            {"code": "permission.menu", "name": "权限管理菜单", "type": PermissionType.MENU, "sort_order": 110},
            {"code": "intelligent.settings.view", "name": "智能设置查看", "type": PermissionType.MENU, "sort_order": 120},
        ]

        menu_id_map = {}
        for perm_data in menu_permissions:
            perm = await Permission.create(**perm_data)
            menu_id_map[perm_data["code"]] = perm.id

        button_permissions = [
            {"code": "customer.view", "name": "客户查看", "type": PermissionType.MENU, "sort_order": 11, "parent_code": "customer.menu"},
            {"code": "customer.create", "name": "客户创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 12, "parent_code": "customer.menu"},
            {"code": "customer.edit", "name": "客户编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 13, "parent_code": "customer.menu"},
            {"code": "customer.delete", "name": "客户删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 14, "parent_code": "customer.menu"},
            {"code": "product.view", "name": "商品查看", "type": PermissionType.MENU, "sort_order": 16, "parent_code": "product.menu"},
            {"code": "product.create", "name": "商品创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 17, "parent_code": "product.menu"},
            {"code": "product.edit", "name": "商品编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 18, "parent_code": "product.menu"},
            {"code": "product.delete", "name": "商品删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 19, "parent_code": "product.menu"},
            {"code": "warehouse.view", "name": "仓库查看", "type": PermissionType.MENU, "sort_order": 65, "parent_code": "warehouse.menu"},
            {"code": "warehouse.create", "name": "仓库创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 66, "parent_code": "warehouse.menu"},
            {"code": "warehouse.edit", "name": "仓库编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 67, "parent_code": "warehouse.menu"},
            {"code": "warehouse.delete", "name": "仓库删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 68, "parent_code": "warehouse.menu"},
            {"code": "user.view", "name": "用户查看", "type": PermissionType.MENU, "sort_order": 95, "parent_code": "user.menu"},
            {"code": "user.create", "name": "用户创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 96, "parent_code": "user.menu"},
            {"code": "user.edit", "name": "用户编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 97, "parent_code": "user.menu"},
            {"code": "user.delete", "name": "用户删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 98, "parent_code": "user.menu"},
            {"code": "role.view", "name": "角色查看", "type": PermissionType.MENU, "sort_order": 105, "parent_code": "role.menu"},
            {"code": "role.create", "name": "角色创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 106, "parent_code": "role.menu"},
            {"code": "role.edit", "name": "角色编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 107, "parent_code": "role.menu"},
            {"code": "role.delete", "name": "角色删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 108, "parent_code": "role.menu"},
        ]

        for perm_data in button_permissions:
            parent_code = perm_data.pop("parent_code", None)
            parent_id = menu_id_map.get(parent_code) if parent_code else None
            await Permission.create(**perm_data, parent_id=parent_id)

        total_count = await Permission.all().count()
        logger.info(f"初始化默认权限成功，共 {total_count} 条")

    except Exception as e:
        logger.error(f"初始化默认权限失败: {e}")
        raise


async def init_super_admin_group():
    try:
        existing_role = await Role.get_or_none(code=SUPER_ADMIN_CODE)
        all_perms = await Permission.all()

        if existing_role:
            existing_perms = await existing_role.permissions.all()
            if len(existing_perms) != len(all_perms):
                await existing_role.permissions.clear()
                await existing_role.permissions.add(*all_perms)
                logger.info(f"更新超级管理员角色权限成功，共 {len(all_perms)} 条权限")
            else:
                logger.info("超级管理员角色已存在且权限完整，跳过初始化")
            return

        role = await Role.create(
            code=SUPER_ADMIN_CODE,
            name="超级管理员",
            description="系统超级管理员，拥有所有权限",
            is_fixed=True,
            status=RoleStatus.ACTIVE
        )
        await role.permissions.add(*all_perms)
        logger.info(f"创建超级管理员角色成功，关联 {len(all_perms)} 条权限")

    except Exception as e:
        logger.error(f"初始化超级管理员角色失败: {e}")
        raise


async def init_admin_user():
    try:
        existing_admin = await User.get_or_none(username="admin")
        if existing_admin:
            logger.info("管理员账号已存在，跳过初始化")
            return

        super_admin_role = await Role.get_or_none(code=SUPER_ADMIN_CODE)
        if not super_admin_role:
            logger.error("超级管理员角色不存在，请先初始化角色")
            return

        user = await User.create(
            username="admin",
            password=get_password_hash("admin123"),
            email="admin@example.com",
            full_name="系统管理员",
            status=UserStatus.ACTIVE
        )
        await user.roles.add(super_admin_role)
        logger.info("创建管理员账号成功，绑定超级管理员角色")

    except Exception as e:
        logger.error(f"初始化管理员账号失败: {e}")
        raise


async def main():
    logger.info("开始初始化 MySQL 数据库数据...")
    try:
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["models_mysql.auth"]},
        )

        await init_default_permissions()
        await init_super_admin_group()
        await init_admin_user()

        logger.info("MySQL 数据库初始化完成")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()
        logger.info("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
