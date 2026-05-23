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

from urllib.parse import quote_plus
from tortoise import Tortoise


async def migrate():
    db_url = (
        f"mysql://{quote_plus(os.getenv('MYSQL_USER', 'admin'))}"
        f":{quote_plus(os.getenv('MYSQL_PASSWORD', 'Chenglp1215!@#'))}"
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

    conn = Tortoise.get_connection("default")

    # 使用原始 SQL 迁移状态值（ORM 枚举已更新，无法用 filter 查询旧值）
    result = await conn.execute_query(
        "UPDATE pending_outbound_orders SET status = 'outbound' WHERE status IN ('partial', 'full')"
    )
    count = result[0]
    print(f"已将 {count} 条 partial/full 记录更新为 outbound")

    # 新增字段
    for col_def in [
        "shipped_at DATETIME NULL",
        "shipping_company VARCHAR(100) NULL",
        "tracking_no VARCHAR(100) NULL"
    ]:
        col_name = col_def.split()[0]
        try:
            await conn.execute_query(f"ALTER TABLE pending_outbound_orders ADD COLUMN {col_def}")
            print(f"已新增 {col_name} 列")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print(f"{col_name} 列已存在，跳过")
            else:
                raise

    print("迁移完成！out_qty 列暂时保留，后续可手动执行: ALTER TABLE pending_outbound_orders DROP COLUMN out_qty")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
