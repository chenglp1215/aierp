"""
迁移脚本：为 pending_outbound_orders 表新增 delivery_type 字段
- delivery_type: 配送方式，logistics-物流发货（默认），pickup-等待自提
- 对应需求：仓库自提发货方式
"""
import asyncio
import os
import sys

# 将 backend 目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载 .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "erp_test")

DB_URL = f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"


async def migrate():
    """执行迁移：新增 delivery_type 字段"""
    from tortoise import Tortoise

    await Tortoise.init(
        db_url=DB_URL,
        modules={"models": ["models_mysql.pending_outbound"]},
    )
    conn = Tortoise.get_connection("default")

    # 检查字段是否已存在
    check_sql = """
        SELECT COUNT(*) AS cnt FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = 'pending_outbound_orders'
          AND COLUMN_NAME = 'delivery_type'
    """
    rows = await conn.execute_query_dict(check_sql, [MYSQL_DATABASE])
    if rows[0]["cnt"] > 0:
        print("[SKIP] delivery_type 字段已存在，跳过迁移")
        await Tortoise.close_connections()
        return

    # 新增 delivery_type 字段
    alter_sql = """
        ALTER TABLE pending_outbound_orders
        ADD COLUMN delivery_type VARCHAR(50) NOT NULL DEFAULT 'logistics'
        COMMENT '配送方式：logistics-物流发货，pickup-等待自提'
        AFTER outbound_type
    """
    await conn.execute_query(alter_sql)
    print("[OK] delivery_type 字段已成功添加到 pending_outbound_orders 表")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
