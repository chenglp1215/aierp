"""
数据库迁移脚本：为销售订单运费功能添加字段

迁移内容：
1. brands 表添加 default_freight 字段
2. sales_orders 表添加 freight_amt 字段
"""
import asyncio
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.database import init_db


async def run_migration():
    """执行数据库迁移"""
    # 使用项目的 init_db 初始化数据库连接
    await init_db()
    conn = Tortoise.get_connection("default")

    print(f"[{datetime.now()}] 开始执行迁移...")

    # 1. 为 brands 表添加 default_freight 字段
    try:
        await conn.execute_script(
            "ALTER TABLE brands ADD COLUMN default_freight DECIMAL(12,2) DEFAULT 0 COMMENT '默认运费';"
        )
        print(f"[{datetime.now()}] brands 表添加 default_freight 字段成功")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print(f"[{datetime.now()}] brands.default_freight 字段已存在，跳过")
        else:
            print(f"[{datetime.now()}] brands 表迁移失败: {e}")

    # 2. 为 sales_orders 表添加 freight_amt 字段
    try:
        await conn.execute_script(
            "ALTER TABLE sales_orders ADD COLUMN freight_amt DECIMAL(12,2) DEFAULT 0 COMMENT '运费金额';"
        )
        print(f"[{datetime.now()}] sales_orders 表添加 freight_amt 字段成功")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print(f"[{datetime.now()}] sales_orders.freight_amt 字段已存在，跳过")
        else:
            print(f"[{datetime.now()}] sales_orders 表迁移失败: {e}")

    # 关闭连接
    await Tortoise.close_connections()

    print(f"[{datetime.now()}] 迁移完成")


if __name__ == "__main__":
    asyncio.run(run_migration())
