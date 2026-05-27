"""
出库单新增 logistics_status 字段迁移脚本
- 在 pending_outbound_orders 表添加 logistics_status 列（VARCHAR(50), NULL）
- 幂等性：列已存在则跳过
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
            "models_mysql.warehouse", "models_mysql.sales_order",
            "models_mysql.purchase_order", "models_mysql.pending_outbound",
            "models_mysql.order_status_flow", "models_mysql.supplier"
        ]}
    )

    conn = Tortoise.get_connection("default")

    # 新增 logistics_status 列
    col_name = "logistics_status"
    col_def = f"{col_name} VARCHAR(50) NULL"
    try:
        await conn.execute_query(f"ALTER TABLE pending_outbound_orders ADD COLUMN {col_def}")
        print(f"已新增 {col_name} 列")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print(f"{col_name} 列已存在，跳过")
        else:
            raise

    print("迁移完成！")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
