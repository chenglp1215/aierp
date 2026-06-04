"""
销售订单模块增强 - 数据库迁移脚本
添加新字段：
- SalesOrder: third_party_platform, platform_order_no
- SalesOrderItem: tax_rate, item_remark

执行方式：backend/venv/Scripts/python scripts/migrate_sales_order_enhance.py
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config import settings
from urllib.parse import quote_plus


async def migrate():
    """执行迁移"""
    # 初始化数据库连接
    encoded_password = quote_plus(settings.MYSQL_PASSWORD)
    db_url = (
        f"mysql://{settings.MYSQL_USER}:{encoded_password}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    )

    await Tortoise.init(
        db_url=db_url,
        modules={"models": [
            "models_mysql.auth",
            "models_mysql.product",
            "models_mysql.customer",
            "models_mysql.warehouse",
            "models_mysql.sales_order",
            "models_mysql.purchase_order",
            "models_mysql.pending_outbound",
            "models_mysql.order_status_flow",
            "models_mysql.supplier",
            "models_mysql.ai",
            "models_mysql.import_task",
        ]}
    )

    # 获取连接
    conn = Tortoise.get_connection("default")

    print("开始执行销售订单模块增强迁移...")

    # 1. SalesOrder 表新增字段
    print("\n[1] 检查 SalesOrder 表字段...")

    # 检查 third_party_platform 字段是否存在
    result = await conn.execute_query(
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{settings.MYSQL_DATABASE}' AND TABLE_NAME = 'sales_orders' AND COLUMN_NAME = 'third_party_platform'"
    )
    if not result[1]:
        print("  - 添加 third_party_platform 字段...")
        await conn.execute_query(
            "ALTER TABLE sales_orders ADD COLUMN third_party_platform VARCHAR(50) NULL COMMENT '第三方平台'"
        )
    else:
        print("  - third_party_platform 字段已存在，跳过")

    # 检查 platform_order_no 字段是否存在
    result = await conn.execute_query(
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{settings.MYSQL_DATABASE}' AND TABLE_NAME = 'sales_orders' AND COLUMN_NAME = 'platform_order_no'"
    )
    if not result[1]:
        print("  - 添加 platform_order_no 字段...")
        await conn.execute_query(
            "ALTER TABLE sales_orders ADD COLUMN platform_order_no VARCHAR(100) NULL COMMENT '平台订单号'"
        )
    else:
        print("  - platform_order_no 字段已存在，跳过")

    # 2. SalesOrderItem 表新增字段
    print("\n[2] 检查 SalesOrderItem 表字段...")

    # 检查 tax_rate 字段是否存在
    result = await conn.execute_query(
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{settings.MYSQL_DATABASE}' AND TABLE_NAME = 'sales_order_items' AND COLUMN_NAME = 'tax_rate'"
    )
    if not result[1]:
        print("  - 添加 tax_rate 字段...")
        await conn.execute_query(
            "ALTER TABLE sales_order_items ADD COLUMN tax_rate DECIMAL(5,4) DEFAULT 0.13 COMMENT '税率'"
        )
    else:
        print("  - tax_rate 字段已存在，跳过")

    # 检查 item_remark 字段是否存在
    result = await conn.execute_query(
        f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        f"WHERE TABLE_SCHEMA = '{settings.MYSQL_DATABASE}' AND TABLE_NAME = 'sales_order_items' AND COLUMN_NAME = 'item_remark'"
    )
    if not result[1]:
        print("  - 添加 item_remark 字段...")
        await conn.execute_query(
            "ALTER TABLE sales_order_items ADD COLUMN item_remark TEXT NULL COMMENT '商品备注'"
        )
    else:
        print("  - item_remark 字段已存在，跳过")

    print("\n迁移完成!")

    # 关闭连接
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())