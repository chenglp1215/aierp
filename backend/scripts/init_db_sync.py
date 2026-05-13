"""
MySQL 数据库初始化脚本（同步版本）
使用 pymysql 直接操作数据库
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
import bcrypt
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from config import settings


def get_connection():
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset="utf8mb4",
    )


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def init_default_permissions(conn):
    cursor = conn.cursor()

    # 检查是否已有权限
    cursor.execute("SELECT COUNT(*) FROM permissions")
    count = cursor.fetchone()[0]
    if count > 0:
        logger.info(f"权限已存在（共 {count} 条），跳过初始化")
        return {}

    # 菜单权限
    menu_permissions = [
        ("dashboard.view", "工作台查看", "menu", 1, None),
        ("chat.view", "智能助手查看", "menu", 2, None),
        ("customer.menu", "客户管理菜单", "menu", 10, None),
        ("product.menu", "商品管理菜单", "menu", 15, None),
        ("category.menu", "分类管理菜单", "menu", 16, None),
        ("order.menu", "订单管理菜单", "menu", 20, None),
        ("procurement.menu", "采购管理菜单", "menu", 30, None),
        ("receivable.menu", "应收款管理菜单", "menu", 40, None),
        ("inventory.menu", "库存管理菜单", "menu", 50, None),
        ("warehouse.menu", "仓库管理菜单", "menu", 60, None),
        ("knowledge.view", "知识库查看", "menu", 70, None),
        ("finance.menu", "财务管理菜单", "menu", 80, None),
        ("user.menu", "用户管理菜单", "menu", 90, None),
        ("role.menu", "角色管理菜单", "menu", 100, None),
        ("permission.menu", "权限管理菜单", "menu", 110, None),
        ("intelligent.settings.view", "智能设置查看", "menu", 120, None),
    ]

    menu_id_map = {}
    for code, name, ptype, sort_order, parent_id in menu_permissions:
        cursor.execute(
            "INSERT INTO permissions (code, name, type, sort_order, parent_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
            (code, name, ptype, sort_order, parent_id)
        )
        menu_id_map[code] = cursor.lastrowid

    # 按钮权限
    button_permissions = [
        ("customer.view", "客户查看", "menu", 11, "customer.menu"),
        ("customer.create", "客户创建", "button,tools", 12, "customer.menu"),
        ("customer.edit", "客户编辑", "button,tools", 13, "customer.menu"),
        ("customer.delete", "客户删除", "button,tools", 14, "customer.menu"),
        ("product.view", "商品查看", "menu", 16, "product.menu"),
        ("product.create", "商品创建", "button,tools", 17, "product.menu"),
        ("product.edit", "商品编辑", "button,tools", 18, "product.menu"),
        ("product.delete", "商品删除", "button,tools", 19, "product.menu"),
        ("warehouse.view", "仓库查看", "menu", 65, "warehouse.menu"),
        ("warehouse.create", "仓库创建", "button,tools", 66, "warehouse.menu"),
        ("warehouse.edit", "仓库编辑", "button,tools", 67, "warehouse.menu"),
        ("warehouse.delete", "仓库删除", "button,tools", 68, "warehouse.menu"),
        ("user.view", "用户查看", "menu", 95, "user.menu"),
        ("user.create", "用户创建", "button,tools", 96, "user.menu"),
        ("user.edit", "用户编辑", "button,tools", 97, "user.menu"),
        ("user.delete", "用户删除", "button,tools", 98, "user.menu"),
        ("role.view", "角色查看", "menu", 105, "role.menu"),
        ("role.create", "角色创建", "button,tools", 106, "role.menu"),
        ("role.edit", "角色编辑", "button,tools", 107, "role.menu"),
        ("role.delete", "角色删除", "button,tools", 108, "role.menu"),
    ]

    for code, name, ptype, sort_order, parent_code in button_permissions:
        parent_id = menu_id_map.get(parent_code)
        cursor.execute(
            "INSERT INTO permissions (code, name, type, sort_order, parent_id, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())",
            (code, name, ptype, sort_order, parent_id)
        )

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM permissions")
    total = cursor.fetchone()[0]
    logger.info(f"初始化默认权限成功，共 {total} 条")
    return menu_id_map


def init_super_admin_role(conn):
    cursor = conn.cursor()

    # 检查是否已有角色
    cursor.execute("SELECT id FROM roles WHERE code = 'super_admin'")
    result = cursor.fetchone()

    if result:
        role_id = result[0]
        # 检查权限数量
        cursor.execute("SELECT COUNT(*) FROM permissions")
        perm_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM role_permissions WHERE roles_id = %s", (role_id,))
        role_perm_count = cursor.fetchone()[0]

        if role_perm_count != perm_count:
            # 更新权限
            cursor.execute("DELETE FROM role_permissions WHERE roles_id = %s", (role_id,))
            cursor.execute("SELECT id FROM permissions")
            perm_ids = [r[0] for r in cursor.fetchall()]
            for perm_id in perm_ids:
                cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))
            conn.commit()
            logger.info(f"更新超级管理员角色权限成功，共 {perm_count} 条权限")
        else:
            logger.info("超级管理员角色已存在且权限完整，跳过初始化")
        return

    # 创建新角色
    cursor.execute(
        "INSERT INTO roles (code, name, description, is_fixed, status, created_at, updated_at) VALUES ('super_admin', '超级管理员', '系统超级管理员，拥有所有权限', 1, 'active', NOW(), NOW())"
    )
    role_id = cursor.lastrowid

    # 获取所有权限并关联
    cursor.execute("SELECT id FROM permissions")
    perm_ids = [r[0] for r in cursor.fetchall()]
    for perm_id in perm_ids:
        cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))

    conn.commit()
    logger.info(f"创建超级管理员角色成功，关联 {len(perm_ids)} 条权限")


def init_warehouse_admin_role(conn):
    """初始化仓库管理员角色"""
    cursor = conn.cursor()

    # 检查是否已有角色
    cursor.execute("SELECT id FROM roles WHERE code = 'warehouse_admin'")
    result = cursor.fetchone()

    if result:
        logger.info("仓库管理员角色已存在，跳过初始化")
        return

    # 获取仓库和库存相关权限
    warehouse_perm_codes = [
        "warehouse.view", "warehouse.create", "warehouse.edit", "warehouse.delete",
        "inventory.stock.view", "inventory.stock.edit",
        "inventory.check.view", "inventory.check.edit",
    ]
    cursor.execute("SELECT id FROM permissions WHERE code IN (%s)" % ",".join(["%s"] * len(warehouse_perm_codes)), warehouse_perm_codes)
    perm_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute(
        "INSERT INTO roles (code, name, description, is_fixed, status, created_at, updated_at) VALUES ('warehouse_admin', '仓库管理员', '仓库管理员，负责仓库日常管理', 1, 'active', NOW(), NOW())"
    )
    role_id = cursor.lastrowid

    for perm_id in perm_ids:
        cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))

    conn.commit()
    logger.info(f"创建仓库管理员角色成功，关联 {len(perm_ids)} 条权限")


def init_purchaser_group_role(conn):
    """初始化采购组角色"""
    cursor = conn.cursor()

    # 检查是否已有角色
    cursor.execute("SELECT id FROM roles WHERE code = 'purchaser_group'")
    result = cursor.fetchone()

    if result:
        logger.info("采购组角色已存在，跳过初始化")
        return

    # 获取采购和订单查看相关权限
    purchaser_perm_codes = [
        "procurement.view", "procurement.create", "procurement.edit",
        "order.view",
    ]
    cursor.execute("SELECT id FROM permissions WHERE code IN (%s)" % ",".join(["%s"] * len(purchaser_perm_codes)), purchaser_perm_codes)
    perm_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute(
        "INSERT INTO roles (code, name, description, is_fixed, status, created_at, updated_at) VALUES ('purchaser_group', '采购组', '采购组成员，负责品牌商品采购', 1, 'active', NOW(), NOW())"
    )
    role_id = cursor.lastrowid

    for perm_id in perm_ids:
        cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))

    conn.commit()
    logger.info(f"创建采购组角色成功，关联 {len(perm_ids)} 条权限")


def init_default_user_role(conn):
    """初始化普通用户角色"""
    cursor = conn.cursor()

    # 检查是否已有角色
    cursor.execute("SELECT id FROM roles WHERE code = 'user'")
    result = cursor.fetchone()

    if result:
        logger.info("普通用户角色已存在，跳过初始化")
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
    cursor.execute("SELECT id FROM permissions WHERE code IN (%s)" % ",".join(["%s"] * len(basic_perm_codes)), basic_perm_codes)
    perm_ids = [r[0] for r in cursor.fetchall()]

    cursor.execute(
        "INSERT INTO roles (code, name, description, is_fixed, status, created_at, updated_at) VALUES ('user', '普通用户', '普通用户角色，拥有基础权限', 0, 'active', NOW(), NOW())"
    )
    role_id = cursor.lastrowid

    for perm_id in perm_ids:
        cursor.execute("INSERT INTO role_permissions (roles_id, permission_id) VALUES (%s, %s)", (role_id, perm_id))

    conn.commit()
    logger.info(f"创建普通用户角色成功，关联 {len(perm_ids)} 条权限")


def init_admin_user(conn):
    cursor = conn.cursor()

    # 检查是否已有用户
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    result = cursor.fetchone()

    if result:
        logger.info("管理员账号已存在，跳过初始化")
        return

    # 获取超级管理员角色
    cursor.execute("SELECT id FROM roles WHERE code = 'super_admin'")
    role_result = cursor.fetchone()
    if not role_result:
        logger.error("超级管理员角色不存在，请先初始化角色")
        return

    role_id = role_result[0]

    # 创建用户
    password_hash = get_password_hash("admin123")
    cursor.execute(
        "INSERT INTO users (username, password, email, full_name, status, created_at, updated_at) VALUES ('admin', %s, 'admin@example.com', '系统管理员', 'active', NOW(), NOW())",
        (password_hash,)
    )
    user_id = cursor.lastrowid

    # 关联角色
    cursor.execute("INSERT INTO user_roles (users_id, role_id) VALUES (%s, %s)", (user_id, role_id))

    conn.commit()
    logger.info("创建管理员账号成功，绑定超级管理员角色")


def main():
    logger.info("开始初始化 MySQL 数据库数据...")

    try:
        conn = get_connection()

        init_default_permissions(conn)
        init_super_admin_role(conn)
        init_warehouse_admin_role(conn)
        init_purchaser_group_role(conn)
        init_default_user_role(conn)
        init_admin_user(conn)

        conn.close()
        logger.info("MySQL 数据库初始化完成")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise


if __name__ == "__main__":
    main()