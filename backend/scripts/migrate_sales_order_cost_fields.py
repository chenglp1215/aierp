"""
销售单成本明细字段迁移脚本
- 创建 sales_order_cost_items 表
- sales_orders 表新增 finance_status 字段
- sales_order_items 表新增 exchange_qty、supplement_qty 字段
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.database import init_db


async def migrate():
    """执行迁移"""
    await init_db()
    conn = Tortoise.get_connection("default")

    # 1. 创建 sales_order_cost_items 表
    try:
        await conn.execute_script("""
            CREATE TABLE IF NOT EXISTS sales_order_cost_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sales_order_id INT NOT NULL,
                cost_type VARCHAR(20) NOT NULL,
                amount DECIMAL(12, 2) NOT NULL,
                source_type VARCHAR(20) NOT NULL,
                source_no VARCHAR(50),
                purchase_order_id INT,
                remark TEXT,
                creator_id INT,
                creator_name VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id) ON DELETE CASCADE,
                INDEX idx_sales_order_id (sales_order_id),
                INDEX idx_purchase_order_id (purchase_order_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("[OK] sales_order_cost_items table created")
    except Exception as e:
        print(f"[SKIP] sales_order_cost_items table already exists: {e}")

    # 2. sales_orders 表新增 finance_status 字段
    try:
        await conn.execute_script("""
            ALTER TABLE sales_orders
            ADD COLUMN finance_status VARCHAR(20) DEFAULT 'unpaid';
        """)
        print("[OK] sales_orders.finance_status column added")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print("[SKIP] sales_orders.finance_status column already exists")
        else:
            print(f"[ERROR] sales_orders.finance_status: {e}")

    # 3. sales_order_items 表新增字段
    try:
        await conn.execute_script("""
            ALTER TABLE sales_order_items
            ADD COLUMN exchange_qty INT DEFAULT 0,
            ADD COLUMN supplement_qty INT DEFAULT 0;
        """)
        print("[OK] sales_order_items.exchange_qty, supplement_qty columns added")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print("[SKIP] sales_order_items columns already exist")
        else:
            print(f"[ERROR] sales_order_items: {e}")

    await Tortoise.close_connections()
    print("\nMigration completed!")


if __name__ == "__main__":
    asyncio.run(migrate())
