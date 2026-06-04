"""注册客户模块缺失的权限"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config.settings import settings
from urllib.parse import quote_plus
from models_mysql.auth import Permission, PermissionType

encoded_password = quote_plus(settings.MYSQL_PASSWORD)
DB_URL = (
    f"mysql://{settings.MYSQL_USER}:{encoded_password}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
)

# 需要注册的新权限
NEW_PERMISSIONS = [
    ("customer.claim", "客户认领", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer.member", "会员管理", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer.order-defaults", "订单默认值设置", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer.credit", "账期额度管理", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer.export", "客户导出", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer.transfer", "客户转移", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer.status", "客户状态管理", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer.stats", "客户统计", PermissionType.API, "customer.menu"),
    ("customer.check-overdue", "超账期检查", PermissionType.API, "customer.menu"),
    ("customer-discount.view", "客户折扣查看", PermissionType.MENU, "customer.menu"),
    ("customer-discount.create", "客户折扣创建", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer-discount.edit", "客户折扣编辑", PermissionType.BUTTON_TOOLS, "customer.menu"),
    ("customer-discount.delete", "客户折扣删除", PermissionType.BUTTON_TOOLS, "customer.menu"),
]


async def register_permissions():
    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ["models_mysql.auth", "models_mysql.customer"]}
    )

    print("开始注册客户模块缺失权限...")

    # 获取 customer.menu 的 ID 作为父权限
    menu_perm = await Permission.filter(code="customer.menu").first()
    parent_id = menu_perm.id if menu_perm else None
    print(f"customer.menu 父权限ID: {parent_id}")

    # 获取现有权限码
    existing_codes = set()
    existing_perms = await Permission.all()
    for p in existing_perms:
        existing_codes.add(p.code)
    print(f"现有权限数量: {len(existing_codes)}")

    # 获取最大 sort_order
    max_sort = max((p.sort_order for p in existing_perms), default=0)
    sort_order = max_sort + 1

    registered = 0
    for code, name, ptype, parent_code in NEW_PERMISSIONS:
        if code in existing_codes:
            print(f"  SKIP(已存在): {code}")
            continue

        # 查找父权限
        pid = parent_id  # 默认用 customer.menu
        if parent_code != "customer.menu":
            parent = await Permission.filter(code=parent_code).first()
            if parent:
                pid = parent.id

        try:
            await Permission.create(
                code=code,
                name=name,
                type=ptype,
                parent_id=pid,
                sort_order=sort_order,
            )
            sort_order += 1
            registered += 1
            print(f"  OK: {code} ({name})")
        except Exception as e:
            print(f"  ERROR: {code} -> {e}")

    # 确保超级管理员角色拥有所有权限
    from models_mysql.auth import Role
    admin_role = await Role.filter(name="超级管理员").first()
    if admin_role:
        all_perms = await Permission.all()
        await admin_role.permissions.clear()
        await admin_role.permissions.add(*all_perms)
        print(f"\n已更新超级管理员角色权限，共 {len(all_perms)} 条")

    print(f"\n注册完成: 新增 {registered} 条权限")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(register_permissions())
