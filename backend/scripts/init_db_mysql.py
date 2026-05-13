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
import bcrypt


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


# 角色编码常量
SUPER_ADMIN_CODE = "super_admin"
WAREHOUSE_ADMIN_CODE = "warehouse_admin"
PURCHASER_GROUP_CODE = "purchaser_group"
USER_ROLE_CODE = "user"


async def init_default_permissions():
    """初始化默认权限集（幂等：已存在则跳过）"""
    try:
        existing_count = await Permission.all().count()
        if existing_count > 0:
            logger.info(f"权限已存在（共 {existing_count} 条），跳过初始化")
            return

        # 菜单权限（顶级权限）
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

        # 创建菜单权限并记录 ID 映射
        menu_id_map = {}
        for perm_data in menu_permissions:
            perm = await Permission.create(**perm_data)
            menu_id_map[perm_data["code"]] = perm.id
            logger.debug(f"创建菜单权限: {perm_data['code']}")

        # 按钮权限（子权限）
        button_permissions = [
            # 客户管理
            {"code": "customer.view", "name": "客户查看", "type": PermissionType.MENU, "sort_order": 11, "parent_code": "customer.menu"},
            {"code": "customer.create", "name": "客户创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 12, "parent_code": "customer.menu"},
            {"code": "customer.edit", "name": "客户编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 13, "parent_code": "customer.menu"},
            {"code": "customer.delete", "name": "客户删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 14, "parent_code": "customer.menu"},
            # 商品管理
            {"code": "product.view", "name": "商品查看", "type": PermissionType.MENU, "sort_order": 16, "parent_code": "product.menu"},
            {"code": "product.create", "name": "商品创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 17, "parent_code": "product.menu"},
            {"code": "product.edit", "name": "商品编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 18, "parent_code": "product.menu"},
            {"code": "product.delete", "name": "商品删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 19, "parent_code": "product.menu"},
            # 分类管理
            {"code": "category.view", "name": "分类查看", "type": PermissionType.MENU, "sort_order": 20, "parent_code": "category.menu"},
            {"code": "category.create", "name": "分类创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 21, "parent_code": "category.menu"},
            {"code": "category.edit", "name": "分类编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 22, "parent_code": "category.menu"},
            {"code": "category.delete", "name": "分类删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 23, "parent_code": "category.menu"},
            # 订单管理
            {"code": "order.view", "name": "订单查看", "type": PermissionType.MENU, "sort_order": 25, "parent_code": "order.menu"},
            {"code": "order.create", "name": "订单创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 26, "parent_code": "order.menu"},
            {"code": "order.edit", "name": "订单编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 27, "parent_code": "order.menu"},
            {"code": "order.delete", "name": "订单删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 28, "parent_code": "order.menu"},
            {"code": "order.confirm", "name": "订单确认", "type": PermissionType.BUTTON_TOOLS, "sort_order": 29, "parent_code": "order.menu"},
            # 采购管理
            {"code": "procurement.view", "name": "采购单查看", "type": PermissionType.MENU, "sort_order": 35, "parent_code": "procurement.menu"},
            {"code": "procurement.create", "name": "采购单创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 36, "parent_code": "procurement.menu"},
            {"code": "procurement.edit", "name": "采购单编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 37, "parent_code": "procurement.menu"},
            {"code": "procurement.delete", "name": "采购单删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 38, "parent_code": "procurement.menu"},
            # 应收款管理
            {"code": "receivable.view", "name": "应收单查看", "type": PermissionType.MENU, "sort_order": 45, "parent_code": "receivable.menu"},
            {"code": "receivable.create", "name": "应收单创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 46, "parent_code": "receivable.menu"},
            {"code": "receivable.edit", "name": "应收单编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 47, "parent_code": "receivable.menu"},
            {"code": "receivable.delete", "name": "应收单删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 48, "parent_code": "receivable.menu"},
            {"code": "receivable.record", "name": "收款记录", "type": PermissionType.BUTTON_TOOLS, "sort_order": 49, "parent_code": "receivable.menu"},
            # 库存管理
            {"code": "inventory.stock.view", "name": "库存查看", "type": PermissionType.MENU, "sort_order": 55, "parent_code": "inventory.menu"},
            {"code": "inventory.stock.edit", "name": "库存编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 56, "parent_code": "inventory.menu"},
            {"code": "inventory.check.view", "name": "盘点查看", "type": PermissionType.MENU, "sort_order": 57, "parent_code": "inventory.menu"},
            {"code": "inventory.check.edit", "name": "盘点编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 58, "parent_code": "inventory.menu"},
            # 仓库管理
            {"code": "warehouse.view", "name": "仓库查看", "type": PermissionType.MENU, "sort_order": 65, "parent_code": "warehouse.menu"},
            {"code": "warehouse.create", "name": "仓库创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 66, "parent_code": "warehouse.menu"},
            {"code": "warehouse.edit", "name": "仓库编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 67, "parent_code": "warehouse.menu"},
            {"code": "warehouse.delete", "name": "仓库删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 68, "parent_code": "warehouse.menu"},
            # 财务管理
            {"code": "finance.invoice.view", "name": "发票查看", "type": PermissionType.MENU, "sort_order": 85, "parent_code": "finance.menu"},
            {"code": "finance.payment.view", "name": "付款查看", "type": PermissionType.MENU, "sort_order": 86, "parent_code": "finance.menu"},
            {"code": "finance.report.view", "name": "报表查看", "type": PermissionType.MENU, "sort_order": 87, "parent_code": "finance.menu"},
            # 用户管理
            {"code": "user.view", "name": "用户查看", "type": PermissionType.MENU, "sort_order": 95, "parent_code": "user.menu"},
            {"code": "user.create", "name": "用户创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 96, "parent_code": "user.menu"},
            {"code": "user.edit", "name": "用户编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 97, "parent_code": "user.menu"},
            {"code": "user.delete", "name": "用户删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 98, "parent_code": "user.menu"},
            {"code": "user.reset-password", "name": "密码重置", "type": PermissionType.BUTTON_TOOLS, "sort_order": 99, "parent_code": "user.menu"},
            # 角色管理
            {"code": "role.view", "name": "角色查看", "type": PermissionType.MENU, "sort_order": 105, "parent_code": "role.menu"},
            {"code": "role.create", "name": "角色创建", "type": PermissionType.BUTTON_TOOLS, "sort_order": 106, "parent_code": "role.menu"},
            {"code": "role.edit", "name": "角色编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 107, "parent_code": "role.menu"},
            {"code": "role.delete", "name": "角色删除", "type": PermissionType.BUTTON_TOOLS, "sort_order": 108, "parent_code": "role.menu"},
            # 权限管理
            {"code": "permission.view", "name": "权限查看", "type": PermissionType.MENU, "sort_order": 115, "parent_code": "permission.menu"},
            # 智能设置
            {"code": "intelligent.settings.edit", "name": "智能设置编辑", "type": PermissionType.BUTTON_TOOLS, "sort_order": 125, "parent_code": "intelligent.settings.view"},
        ]

        # 创建按钮权限并关联父权限
        for perm_data in button_permissions:
            parent_code = perm_data.pop("parent_code", None)
            parent_id = menu_id_map.get(parent_code) if parent_code else None

            perm = await Permission.create(
                **perm_data,
                parent_id=parent_id
            )
            logger.debug(f"创建按钮权限: {perm_data['code']}")

        total_count = await Permission.all().count()
        logger.info(f"初始化默认权限成功，共 {total_count} 条")

    except Exception as e:
        logger.error(f"初始化默认权限失败: {e}")
        raise


async def init_super_admin_group():
    """初始化超级管理员角色（幂等：已存在则跳过）"""
    try:
        existing_role = await Role.get_or_none(code=SUPER_ADMIN_CODE)
        all_perms = await Permission.all()

        if existing_role:
            # 检查是否需要更新权限
            existing_perms = await existing_role.permissions.all()
            if len(existing_perms) != len(all_perms):
                await existing_role.permissions.clear()
                await existing_role.permissions.add(*all_perms)
                logger.info(f"更新超级管理员角色权限成功，共 {len(all_perms)} 条权限")
            else:
                logger.info(f"超级管理员角色已存在且权限完整，跳过初始化")
            return

        # 创建新的超级管理员角色
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


async def init_warehouse_admin_group():
    """初始化仓库管理员角色（幂等：已存在则跳过）"""
    try:
        existing_role = await Role.get_or_none(code=WAREHOUSE_ADMIN_CODE)
        if existing_role:
            logger.info(f"仓库管理员角色已存在，跳过初始化")
            return

        # 获取仓库和库存相关权限
        warehouse_perm_codes = [
            "warehouse.view", "warehouse.create", "warehouse.edit", "warehouse.delete",
            "inventory.stock.view", "inventory.stock.edit",
            "inventory.check.view", "inventory.check.edit",
        ]
        warehouse_perms = await Permission.filter(code__in=warehouse_perm_codes)

        role = await Role.create(
            code=WAREHOUSE_ADMIN_CODE,
            name="仓库管理员",
            description="仓库管理员，负责仓库日常管理",
            is_fixed=True,
            status=RoleStatus.ACTIVE
        )
        await role.permissions.add(*warehouse_perms)
        logger.info(f"创建仓库管理员角色成功，关联 {len(warehouse_perms)} 条权限")

    except Exception as e:
        logger.error(f"初始化仓库管理员角色失败: {e}")
        raise


async def init_purchaser_group():
    """初始化采购组角色（幂等：已存在则跳过）"""
    try:
        existing_role = await Role.get_or_none(code=PURCHASER_GROUP_CODE)
        if existing_role:
            logger.info(f"采购组角色已存在，跳过初始化")
            return

        # 获取采购和订单查看相关权限
        purchaser_perm_codes = [
            "procurement.view", "procurement.create", "procurement.edit",
            "order.view",
        ]
        purchaser_perms = await Permission.filter(code__in=purchaser_perm_codes)

        role = await Role.create(
            code=PURCHASER_GROUP_CODE,
            name="采购组",
            description="采购组成员，负责品牌商品采购",
            is_fixed=True,
            status=RoleStatus.ACTIVE
        )
        await role.permissions.add(*purchaser_perms)
        logger.info(f"创建采购组角色成功，关联 {len(purchaser_perms)} 条权限")

    except Exception as e:
        logger.error(f"初始化采购组角色失败: {e}")
        raise


async def init_default_user_role():
    """初始化普通用户角色（幂等：已存在则跳过）"""
    try:
        existing_role = await Role.get_or_none(code=USER_ROLE_CODE)
        if existing_role:
            logger.info(f"普通用户角色已存在，跳过初始化")
            return

        # 获取基础权限
        basic_perm_codes = [
            "dashboard.view", "chat.view",
            "customer.view", "customer.create", "customer.edit",
            "product.view", "product.create", "product.edit",
            "order.view", "order.create", "order.edit", "order.confirm",
            "procurement.view", "procurement.create", "procurement.edit",
            "receivable.view", "receivable.create", "receivable.edit", "receivable.record",
            "warehouse.view", "warehouse.create", "warehouse.edit",
            "inventory.stock.view", "inventory.stock.edit",
            "finance.invoice.view", "finance.payment.view",
            "intelligent.settings.view"
        ]
        basic_perms = await Permission.filter(code__in=basic_perm_codes)

        role = await Role.create(
            code=USER_ROLE_CODE,
            name="普通用户",
            description="普通用户角色，拥有基础权限",
            is_fixed=False,
            status=RoleStatus.ACTIVE
        )
        await role.permissions.add(*basic_perms)
        logger.info(f"创建普通用户角色成功，关联 {len(basic_perms)} 条权限")

    except Exception as e:
        logger.error(f"初始化普通用户角色失败: {e}")
        raise


async def init_admin_user():
    """初始化管理员账号（幂等：已存在则跳过）"""
    try:
        existing_admin = await User.get_or_none(username="admin")
        if existing_admin:
            logger.info("管理员账号已存在，跳过初始化")
            return

        # 获取超级管理员角色
        super_admin_role = await Role.get_or_none(code=SUPER_ADMIN_CODE)
        if not super_admin_role:
            logger.error("超级管理员角色不存在，请先初始化角色")
            return

        # 创建管理员账号
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
    """执行所有初始化"""
    logger.info("开始初始化 MySQL 数据库...")

    try:
        # 初始化数据库连接
        await init_mysql()

        # 按顺序执行初始化
        await init_default_permissions()
        await init_super_admin_group()
        await init_warehouse_admin_group()
        await init_purchaser_group()
        await init_default_user_role()
        await init_admin_user()

        logger.info("MySQL 数据库初始化完成")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
    finally:
        await close_mysql()


if __name__ == "__main__":
    asyncio.run(main())
