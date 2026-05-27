"""
入库批次成本价 & 成本明细关联待出库单 迁移脚本
- inbound_batches 表新增 cost_price DECIMAL(12,2) NULL 列
- sales_order_cost_items 表新增 pending_outbound_id INT NULL 列
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.database import init_db


async def migrate():
    await init_db()
    conn = Tortoise.get_connection("default")

    # 1. inbound_batches 新增 cost_price
    try:
        await conn.execute_script("""
            ALTER TABLE inbound_batches
            ADD COLUMN cost_price DECIMAL(12, 2) NULL;
        """)
        print("[OK] inbound_batches.cost_price column added")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print("[SKIP] inbound_batches.cost_price column already exists")
        else:
            print(f"[ERROR] inbound_batches.cost_price: {e}")

    # 2. sales_order_cost_items 新增 pending_outbound_id
    try:
        await conn.execute_script("""
            ALTER TABLE sales_order_cost_items
            ADD COLUMN pending_outbound_id INT NULL;
        """)
        print("[OK] sales_order_cost_items.pending_outbound_id column added")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print("[SKIP] sales_order_cost_items.pending_outbound_id column already exists")
        else:
            print(f"[ERROR] sales_order_cost_items.pending_outbound_id: {e}")

    await Tortoise.close_connections()
    print("\nMigration completed!")


if __name__ == "__main__":
    asyncio.run(migrate())