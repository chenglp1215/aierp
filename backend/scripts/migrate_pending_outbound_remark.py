"""
迁移脚本：为 pending_outbound_orders 表添加 remark 字段
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from config.settings import settings, TORTOISE_ORM


async def migrate():
    """执行迁移"""
    # 使用 TORTOISE_ORM 配置
    await Tortoise.init(config=TORTOISE_ORM)

    # 获取原始连接执行 SQL
    conn = Tortoise.get_connection("default")

    # 检查字段是否已存在
    check_sql = """
        SELECT COUNT(*) as cnt
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'pending_outbound_orders'
        AND COLUMN_NAME = 'remark'
    """
    result = await conn.execute_query(check_sql)
    if result[1][0]['cnt'] > 0:
        print("remark 字段已存在，无需迁移")
        await Tortoise.close_connections()
        return

    # 添加 remark 字段
    alter_sql = """
        ALTER TABLE pending_outbound_orders
        ADD COLUMN remark TEXT NULL COMMENT '备注'
        AFTER status
    """
    await conn.execute_query(alter_sql)
    print("成功添加 remark 字段")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
