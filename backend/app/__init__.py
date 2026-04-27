from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from app.database import init_db, close_db
from app.middleware import LoggingMiddleware, AuthMiddleware

logger = logging.getLogger(__name__)


async def init_admin_user():
    """初始化管理员账号"""
    from services.auth_service import auth_service, role_service, permission_service

    try:
        existing_admin = await auth_service.find_one({"username": "admin"})
        if existing_admin:
            logger.info("管理员账号已存在")
            return

        all_perms = await permission_service.collection.find({}).to_list(length=None)
        all_perm_ids = [str(perm["_id"]) for perm in all_perms]

        admin_role = await role_service.find_one({"code": "admin"})
        if not admin_role:
            role_id = await role_service.create({
                "code": "admin",
                "name": "管理员",
                "description": "系统管理员角色",
                "permission_ids": all_perm_ids,
                "status": "active"
            })
            admin_role_id = role_id
            logger.info(f"创建管理员角色成功: {role_id}")
        else:
            await role_service.update(admin_role["id"], {"permission_ids": all_perm_ids})
            admin_role_id = admin_role["id"]
            logger.info("管理员角色已存在，已更新权限")

        from models.auth import UserCreate
        user_data = UserCreate(
            username="admin",
            password="admin123",
            email="admin@example.com",
            full_name="系统管理员",
            role_ids=[admin_role_id]
        )

        user_id = await auth_service.create_user(user_data)
        logger.info(f"创建管理员账号成功: {user_id}")

    except Exception as e:
        logger.error(f"初始化管理员账号失败: {e}")


async def init_default_roles():
    """初始化默认角色"""
    from services.auth_service import role_service, permission_service

    try:
        existing_role = await role_service.find_one({"code": "user"})
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
            "code": "user",
            "name": "普通用户",
            "description": "普通用户角色，拥有基础权限",
            "permission_ids": basic_perm_ids,
            "status": "active"
        })
        logger.info(f"创建普通用户角色成功: {role_id}")

    except Exception as e:
        logger.error(f"初始化默认角色失败: {e}")


async def init_default_agents():
    """初始化默认 Agent"""
    from services.ai_service import agent_service

    try:
        await agent_service.init_default_agents()
    except Exception as e:
        logger.error(f"初始化默认 Agent 失败: {e}")


async def init_agent_manager():
    """初始化 Agent 管理器"""
    from app.agent import agent_manager

    try:
        await agent_manager.initialize()
        logger.info("Agent 管理器初始化完成")
    except Exception as e:
        logger.error(f"初始化 Agent 管理器失败: {e}")


async def init_default_permissions():
    """初始化默认权限集"""
    from services.auth_service import permission_service

    try:
        await permission_service.collection.delete_many({})
        logger.info("已清空权限数据，准备重新初始化")

        menu_permissions = [
            {"code": "dashboard.view", "name": "工作台查看", "type": "menu", "sort_order": 1, "parent_id": None},
            {"code": "chat.view", "name": "智能助手查看", "type": "menu", "sort_order": 2, "parent_id": None},
            {"code": "customer.menu", "name": "客户管理菜单", "type": "menu", "sort_order": 10, "parent_id": None},
            {"code": "product.menu", "name": "商品管理菜单", "type": "menu", "sort_order": 15, "parent_id": None},
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
            {"code": "order.view", "name": "订单查看", "type": "menu", "sort_order": 21},
            {"code": "order.create", "name": "订单创建", "type": "button,tools", "sort_order": 22},
            {"code": "order.edit", "name": "订单编辑", "type": "button,tools", "sort_order": 23},
            {"code": "order.delete", "name": "订单删除", "type": "button,tools", "sort_order": 24},
            {"code": "order.confirm", "name": "订单确认", "type": "button,tools", "sort_order": 25},
            {"code": "procurement.view", "name": "采购单查看", "type": "menu", "sort_order": 31},
            {"code": "procurement.create", "name": "采购单创建", "type": "button,tools", "sort_order": 32},
            {"code": "procurement.edit", "name": "采购单编辑", "type": "button,tools", "sort_order": 33},
            {"code": "procurement.delete", "name": "采购单删除", "type": "button,tools", "sort_order": 34},
            {"code": "receivable.view", "name": "应收单查看", "type": "menu", "sort_order": 41},
            {"code": "receivable.create", "name": "应收单创建", "type": "button,tools", "sort_order": 42},
            {"code": "receivable.edit", "name": "应收单编辑", "type": "button,tools", "sort_order": 43},
            {"code": "receivable.delete", "name": "应收单删除", "type": "button,tools", "sort_order": 44},
            {"code": "receivable.record", "name": "收款记录", "type": "button,tools", "sort_order": 45},
            {"code": "inventory.stock.view", "name": "库存查看", "type": "menu", "sort_order": 51},
            {"code": "inventory.stock.edit", "name": "库存编辑", "type": "button,tools", "sort_order": 52},
            {"code": "inventory.check.view", "name": "盘点查看", "type": "menu", "sort_order": 53},
            {"code": "inventory.check.edit", "name": "盘点编辑", "type": "button,tools", "sort_order": 54},
            {"code": "warehouse.view", "name": "仓库查看", "type": "menu", "sort_order": 61},
            {"code": "warehouse.create", "name": "仓库创建", "type": "button,tools", "sort_order": 62},
            {"code": "warehouse.edit", "name": "仓库编辑", "type": "button,tools", "sort_order": 63},
            {"code": "warehouse.delete", "name": "仓库删除", "type": "button,tools", "sort_order": 64},
            {"code": "finance.invoice.view", "name": "发票查看", "type": "menu", "sort_order": 81},
            {"code": "finance.payment.view", "name": "付款查看", "type": "menu", "sort_order": 82},
            {"code": "finance.report.view", "name": "报表查看", "type": "menu", "sort_order": 83},
            {"code": "user.view", "name": "用户查看", "type": "menu", "sort_order": 91},
            {"code": "user.create", "name": "用户创建", "type": "button,tools", "sort_order": 92},
            {"code": "user.edit", "name": "用户编辑", "type": "button,tools", "sort_order": 93},
            {"code": "user.delete", "name": "用户删除", "type": "button,tools", "sort_order": 94},
            {"code": "user.reset-password", "name": "密码重置", "type": "button,tools", "sort_order": 95},
            {"code": "role.view", "name": "角色查看", "type": "menu", "sort_order": 101},
            {"code": "role.create", "name": "角色创建", "type": "button,tools", "sort_order": 102},
            {"code": "role.edit", "name": "角色编辑", "type": "button,tools", "sort_order": 103},
            {"code": "role.delete", "name": "角色删除", "type": "button,tools", "sort_order": 104},
            {"code": "permission.view", "name": "权限查看", "type": "menu", "sort_order": 111},
            {"code": "intelligent.settings.edit", "name": "智能设置编辑", "type": "button,tools", "sort_order": 121},
        ]

        menu_id_map = {}
        for perm in menu_permissions:
            result = await permission_service.create(perm)
            menu_id_map[perm["code"]] = result

        code_prefix_map = {
            "customer": "customer.menu",
            "product": "product.menu",
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_default_permissions()
    await init_default_roles()
    await init_admin_user()
    await init_default_agents()
    await init_agent_manager()
    yield
    await close_db()


def create_app() -> FastAPI:
    from fastapi.staticfiles import StaticFiles
    import os

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(AuthMiddleware)
    app.add_middleware(LoggingMiddleware)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/data/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    from app.routers import api_router
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
