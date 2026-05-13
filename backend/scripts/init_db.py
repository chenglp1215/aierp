"""
数据库初始化脚本
在服务启动前单独运行一次，初始化默认数据

使用方法：
    cd /root/aierp/backend
    /root/aierp/venv/bin/python scripts/init_db.py
"""
import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from app.database import init_db, close_db
from config import settings

SUPER_ADMIN_CODE = "super_admin"
WAREHOUSE_ADMIN_CODE = "warehouse_admin"
PURCHASER_GROUP_CODE = "purchaser_group"
USER_ROLE_CODE = "user"


async def init_default_permissions():
    """初始化默认权限集（幂等：已存在则跳过）"""
    from services.auth_service import permission_service

    try:
        existing_count = await permission_service.collection.count_documents({})
        if existing_count > 0:
            logger.info(f"权限已存在（共 {existing_count} 条），跳过初始化")
            return

        menu_permissions = [
            {"code": "dashboard.view", "name": "工作台查看", "type": "menu", "sort_order": 1, "parent_id": None},
            {"code": "chat.view", "name": "智能助手查看", "type": "menu", "sort_order": 2, "parent_id": None},
            {"code": "customer.menu", "name": "客户管理菜单", "type": "menu", "sort_order": 10, "parent_id": None},
            {"code": "product.menu", "name": "商品管理菜单", "type": "menu", "sort_order": 15, "parent_id": None},
            {"code": "category.menu", "name": "分类管理菜单", "type": "menu", "sort_order": 16, "parent_id": None},
            {"code": "order.menu", "name": "订单管理菜单", "type": "menu", "sort_order": 20, "parent_id": None},
            {"code": "procurement.menu", "name": "采购管理菜单", "type": "menu", "sort_order": 30, "parent_id": None},
            {"code": "receivable.menu", "name": "应收款管理菜单", "type": "menu", "sort_order": 40, "parent_id": None},
            {"code": "inventory.menu", "name": "库存管理菜单", "type": "menu", "sort_order": 50, "parent_id": None},
            {"code": "warehouse.menu", "name": "仓库管理菜单", "type": "menu", "sort_order": 60, "parent_id": None},
            {"code": "knowledge.view", "name": "知识库查看", "type": "menu", "sort_order": 70, "parent_id": None},
            {"code": "finance.menu", "name": "财务管理菜单", "type": "menu", "sort_order": 80, "parent_id": None},
            {"code": "user.menu", "name": "用户管理菜单", "type": "menu", "sort_order": 90, "parent_id": None},
            {"code": "role.menu", "name": "角色管理菜单", "type": "menu", "sort_order": 100, "parent_id": None},
            {"code": "permission.menu", "name": "权限管理菜单", "type": "menu", "sort_order": 110, "parent_id": None},
            {"code": "intelligent.settings.view", "name": "智能设置查看", "type": "menu", "sort_order": 120, "parent_id": None},
        ]

        button_permissions = [
            {"code": "customer.view", "name": "客户查看", "type": "menu", "sort_order": 11},
            {"code": "customer.create", "name": "客户创建", "type": "button,tools", "sort_order": 12},
            {"code": "customer.edit", "name": "客户编辑", "type": "button,tools", "sort_order": 13},
            {"code": "customer.delete", "name": "客户删除", "type": "button,tools", "sort_order": 14},
            {"code": "product.view", "name": "商品查看", "type": "menu", "sort_order": 16},
            {"code": "product.create", "name": "商品创建", "type": "button,tools", "sort_order": 17},
            {"code": "product.edit", "name": "商品编辑", "type": "button,tools", "sort_order": 18},
            {"code": "product.delete", "name": "商品删除", "type": "button,tools", "sort_order": 19},
            {"code": "category.view", "name": "分类查看", "type": "menu", "sort_order": 20},
            {"code": "category.create", "name": "分类创建", "type": "button,tools", "sort_order": 21},
            {"code": "category.edit", "name": "分类编辑", "type": "button,tools", "sort_order": 22},
            {"code": "category.delete", "name": "分类删除", "type": "button,tools", "sort_order": 23},
            {"code": "order.view", "name": "订单查看", "type": "menu", "sort_order": 25},
            {"code": "order.create", "name": "订单创建", "type": "button,tools", "sort_order": 26},
            {"code": "order.edit", "name": "订单编辑", "type": "button,tools", "sort_order": 27},
            {"code": "order.delete", "name": "订单删除", "type": "button,tools", "sort_order": 28},
            {"code": "order.confirm", "name": "订单确认", "type": "button,tools", "sort_order": 29},
            {"code": "procurement.view", "name": "采购单查看", "type": "menu", "sort_order": 35},
            {"code": "procurement.create", "name": "采购单创建", "type": "button,tools", "sort_order": 36},
            {"code": "procurement.edit", "name": "采购单编辑", "type": "button,tools", "sort_order": 37},
            {"code": "procurement.delete", "name": "采购单删除", "type": "button,tools", "sort_order": 38},
            {"code": "receivable.view", "name": "应收单查看", "type": "menu", "sort_order": 45},
            {"code": "receivable.create", "name": "应收单创建", "type": "button,tools", "sort_order": 46},
            {"code": "receivable.edit", "name": "应收单编辑", "type": "button,tools", "sort_order": 47},
            {"code": "receivable.delete", "name": "应收单删除", "type": "button,tools", "sort_order": 48},
            {"code": "receivable.record", "name": "收款记录", "type": "button,tools", "sort_order": 49},
            {"code": "inventory.stock.view", "name": "库存查看", "type": "menu", "sort_order": 55},
            {"code": "inventory.stock.edit", "name": "库存编辑", "type": "button,tools", "sort_order": 56},
            {"code": "inventory.check.view", "name": "盘点查看", "type": "menu", "sort_order": 57},
            {"code": "inventory.check.edit", "name": "盘点编辑", "type": "button,tools", "sort_order": 58},
            {"code": "warehouse.view", "name": "仓库查看", "type": "menu", "sort_order": 65},
            {"code": "warehouse.create", "name": "仓库创建", "type": "button,tools", "sort_order": 66},
            {"code": "warehouse.edit", "name": "仓库编辑", "type": "button,tools", "sort_order": 67},
            {"code": "warehouse.delete", "name": "仓库删除", "type": "button,tools", "sort_order": 68},
            {"code": "finance.invoice.view", "name": "发票查看", "type": "menu", "sort_order": 85},
            {"code": "finance.payment.view", "name": "付款查看", "type": "menu", "sort_order": 86},
            {"code": "finance.report.view", "name": "报表查看", "type": "menu", "sort_order": 87},
            {"code": "user.view", "name": "用户查看", "type": "menu", "sort_order": 95},
            {"code": "user.create", "name": "用户创建", "type": "button,tools", "sort_order": 96},
            {"code": "user.edit", "name": "用户编辑", "type": "button,tools", "sort_order": 97},
            {"code": "user.delete", "name": "用户删除", "type": "button,tools", "sort_order": 98},
            {"code": "user.reset-password", "name": "密码重置", "type": "button,tools", "sort_order": 99},
            {"code": "role.view", "name": "角色查看", "type": "menu", "sort_order": 105},
            {"code": "role.create", "name": "角色创建", "type": "button,tools", "sort_order": 106},
            {"code": "role.edit", "name": "角色编辑", "type": "button,tools", "sort_order": 107},
            {"code": "role.delete", "name": "角色删除", "type": "button,tools", "sort_order": 108},
            {"code": "permission.view", "name": "权限查看", "type": "menu", "sort_order": 115},
            {"code": "intelligent.settings.edit", "name": "智能设置编辑", "type": "button,tools", "sort_order": 125},
        ]

        menu_id_map = {}
        for perm in menu_permissions:
            result = await permission_service.create(perm)
            menu_id_map[perm["code"]] = result

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
            await permission_service.create(perm)

        logger.info(f"初始化默认权限成功")

    except Exception as e:
        logger.error(f"初始化默认权限失败: {e}")


async def init_super_admin_group():
    from services.auth_service import role_service, permission_service
    try:
        existing_fixed = await role_service.collection.count_documents({"code": SUPER_ADMIN_CODE})
        all_perms = await permission_service.collection.find({}).to_list(length=None)
        all_perm_ids = [str(perm["_id"]) for perm in all_perms]

        if existing_fixed > 0:
            existing_role = await role_service.find_one({"code": SUPER_ADMIN_CODE})
            if existing_role and not existing_role.get("permission_ids"):
                await role_service.update(existing_role["id"], {"permission_ids": all_perm_ids})
                logger.info(f"更新超级管理员角色权限成功")
            else:
                logger.info(f"固化超级管理员角色已存在且已有权限，跳过初始化")
            return

        await role_service.create({
            "code": SUPER_ADMIN_CODE,
            "name": "超级管理员",
            "description": "系统超级管理员，拥有所有权限",
            "permission_ids": all_perm_ids,
            "status": "active",
            "is_fixed": True
        })
        logger.info(f"创建超级管理员角色成功")
    except Exception as e:
        logger.error(f"初始化超级管理员角色失败: {e}")


async def init_warehouse_admin_group():
    from services.auth_service import role_service, permission_service
    try:
        existing_fixed = await role_service.collection.count_documents({"code": WAREHOUSE_ADMIN_CODE})
        if existing_fixed > 0:
            logger.info(f"固化仓库管理员角色已存在（共 {existing_fixed} 条），跳过初始化")
            return

        warehouse_perms = await permission_service.collection.find({
            "code": {"$in": [
                "warehouse.view", "warehouse.create", "warehouse.edit", "warehouse.delete",
                "inventory.stock.view", "inventory.stock.edit",
                "inventory.check.view", "inventory.check.edit",
            ]}
        }).to_list(length=None)
        warehouse_perm_ids = [str(perm["_id"]) for perm in warehouse_perms]

        warehouse_admin_id = await role_service.create({
            "code": WAREHOUSE_ADMIN_CODE,
            "name": "仓库管理员",
            "description": "仓库管理员，负责仓库日常管理",
            "permission_ids": warehouse_perm_ids,
            "status": "active",
            "is_fixed": True
        })
        logger.info(f"创建仓库管理员角色成功: {warehouse_admin_id}")
    except Exception as e:
        logger.error(f"初始化仓库管理员角色失败: {e}")


async def init_purchaser_group():
    from services.auth_service import role_service, permission_service
    try:
        existing_fixed = await role_service.collection.count_documents({"code": PURCHASER_GROUP_CODE})
        if existing_fixed > 0:
            logger.info(f"固化采购组角色已存在（共 {existing_fixed} 条），跳过初始化")
            return
        purchaser_perms = await permission_service.collection.find({
            "code": {"$in": [
                "procurement.view", "procurement.create", "procurement.edit",
                "order.view",
            ]}
        }).to_list(length=None)
        purchaser_perm_ids = [str(perm["_id"]) for perm in purchaser_perms]
        purchaser_group_id = await role_service.create({
            "code": PURCHASER_GROUP_CODE,
            "name": "采购组",
            "description": "采购组成员，负责品牌商品采购",
            "permission_ids": purchaser_perm_ids,
            "status": "active",
            "is_fixed": True
        })
        logger.info(f"创建采购组角色成功: {purchaser_group_id}")

    except Exception as e:
        logger.error(f"初始化采购组角色失败: {e}")


async def init_admin_user():
    """初始化管理员账号（幂等：已存在则跳过）"""
    from services.auth_service import auth_service, role_service

    try:
        existing_admin = await auth_service.find_one({"username": "admin"})
        if existing_admin:
            logger.info("管理员账号已存在，跳过")
            return

        super_admin_role = await role_service.find_one({"code": SUPER_ADMIN_CODE})
        if not super_admin_role:
            logger.error("超级管理员角色不存在，请先初始化固化角色")
            return

        user_data = {
            "username": "admin",
            "password": "admin123",
            "email": "admin@example.com",
            "full_name": "系统管理员",
            "role_ids": [super_admin_role["id"]]
        }

        user_id = await auth_service.create_user(user_data)
        logger.info(f"创建管理员账号成功，绑定超级管理员角色")

    except Exception as e:
        logger.error(f"初始化管理员账号失败: {e}")


async def init_default_roles():
    """初始化默认角色：普通用户（幂等：已存在则跳过）"""
    from services.auth_service import role_service, permission_service

    try:
        existing_role = await role_service.find_one({"code": USER_ROLE_CODE})
        if existing_role:
            logger.info("普通用户角色已存在，跳过")
            return

        basic_perms = await permission_service.collection.find({
            "code": {"$in": [
                "dashboard.view", "chat.view",
                "customer.view", "customer.create", "customer.edit",
                "product.view", "product.create", "product.edit",
                "order.view", "order.create", "order.edit", "order.confirm",
                "procurement.view", "procurement.create", "procurement.edit",
                "receivable.view", "receivable.create", "receivable.edit", "receivable.record",
                "warehouse.view", "warehouse.create", "warehouse.edit",
                "stock.view", "stock.create", "stock.edit",
                "finance.invoice.view", "finance.payment.view",
                "intelligent.settings.view"
            ]}
        }).to_list(length=None)

        basic_perm_ids = [str(perm["_id"]) for perm in basic_perms]

        role_id = await role_service.create({
            "code": USER_ROLE_CODE,
            "name": "普通用户",
            "description": "普通用户角色，拥有基础权限",
            "permission_ids": basic_perm_ids,
            "status": "active"
        })
        logger.info(f"创建普通用户角色成功: {role_id}")

    except Exception as e:
        logger.error(f"初始化默认角色失败: {e}")


async def init_default_agents():
    """初始化默认 Agent（幂等：已存在则跳过）"""
    from services.ai_service import agent_service

    try:
        await agent_service.init_default_agents()
    except Exception as e:
        logger.error(f"初始化默认 Agent 失败: {e}")


async def main():
    """执行所有初始化"""
    logger.info("开始初始化数据库...")

    try:
        await init_db()
        await init_default_permissions()
        await init_super_admin_group()
        await init_warehouse_admin_group()
        await init_purchaser_group()
        await init_admin_user()
        await init_default_roles()
        await init_default_agents()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
