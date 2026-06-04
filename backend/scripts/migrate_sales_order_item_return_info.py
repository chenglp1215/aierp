"""
数据库迁移脚本：为 sales_order_items 表新增 return_info 字段
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config import settings
from urllib.parse import quote_plus


async def migrate():
    """执行迁移"""
    # 连接数据库
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
            "models_mysql.supplier",
            "models_mysql.ai",
        ]}
    )

    # 获取连接
    conn = Tortoise.get_connection("default")

    # 执行 ALTER TABLE
    sql = """
    ALTER TABLE sales_order_items
    ADD COLUMN return_info VARCHAR(500) NULL COMMENT '退货信息：格式退货数量（退货方式，金额）'
    """

    try:
        await conn.execute_query(sql)
        print("[OK] return_info 字段添加成功")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("[INFO] return_info 字段已存在，跳过迁移")
        else:
            print(f"[FAIL] 迁移失败: {e}")
            raise

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
