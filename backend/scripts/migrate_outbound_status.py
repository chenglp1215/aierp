"""
出库单状态枚举迁移脚本
- partial → outbound（部分出库视为已出库）
- full → outbound
- pending/cancelled 保持不变
- 新增 shipped_at, shipping_company, tracking_no 列
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from tortoise import Tortoise
from models_mysql.pending_outbound import PendingOutboundOrder


async def migrate():
    db_url = (
        f"mysql://{os.getenv('MYSQL_USER', 'admin')}"
        f":{os.getenv('MYSQL_PASSWORD', 'Chenglp1215!@#')}"
        f"@{os.getenv('MYSQL_HOST', '132.232.212.151')}"
        f":{os.getenv('MYSQL_PORT', '58901')}"
        f"/{os.getenv('MYSQL_DATABASE', 'erp_test')}"
    )

    await Tortoise.init(
        db_url=db_url,
        modules={"models": [
            "models_mysql.auth", "models_mysql.product", "models_mysql.customer",
            "models_mysql.stock_check", "models_mysql.warehouse", "models_mysql.sales_order",
            "models_mysql.purchase_order", "models_mysql.pending_outbound",
            "models_mysql.order_status_flow", "models_mysql.supplier"
        ]}
    )

    # 迁移 partial → outbound
    partial_count = await PendingOutboundOrder.filter(status="partial").update(status="outbound")
    print(f"已将 {partial_count} 条 partial 记录更新为 outbound")

    # 迁移 full → outbound
    full_count = await PendingOutboundOrder.filter(status="full").update(status="outbound")
    print(f"已将 {full_count} 条 full 记录更新为 outbound")

    # 数据库字段变更：新增 shipped_at, shipping_company, tracking_no
    conn = Tortoise.get_connection("default")
    try:
        await conn.execute_query(
            "ALTER TABLE pending_outbound_orders ADD COLUMN shipped_at DATETIME NULL"
        )
        print("已新增 shipped_at 列")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("shipped_at 列已存在，跳过")
        else:
            raise

    try:
        await conn.execute_query(
            "ALTER TABLE pending_outbound_orders ADD COLUMN shipping_company VARCHAR(100) NULL"
        )
        print("已新增 shipping_company 列")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("shipping_company 列已存在，跳过")
        else:
            raise

    try:
        await conn.execute_query(
            "ALTER TABLE pending_outbound_orders ADD COLUMN tracking_no VARCHAR(100) NULL"
        )
        print("已新增 tracking_no 列")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("tracking_no 列已存在，跳过")
        else:
            raise

    print("迁移完成！out_qty 列暂时保留，后续可手动执行: ALTER TABLE pending_outbound_orders DROP COLUMN out_qty")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
