"""
库存批次管理 - 数据库结构迁移脚本
新增字段和表结构，幂等执行
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from urllib.parse import quote_plus
load_dotenv()

DB_URL = (
    f"mysql://{os.getenv('MYSQL_USER')}:{quote_plus(os.getenv('MYSQL_PASSWORD'))}"
    f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}"
)


async def migrate():
    from tortoise import Tortoise
    await Tortoise.init(db_url=DB_URL, modules={"models": ["models_mysql.warehouse"]})
    conn = Tortoise.get_connection("default")

    # 1. 创建 warehouse_locations 表（如果不存在）
    await conn.execute_query("""
        CREATE TABLE IF NOT EXISTS warehouse_locations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            warehouse_id INT NOT NULL,
            location_code VARCHAR(50) NOT NULL,
            location_name VARCHAR(100) DEFAULT NULL,
            status VARCHAR(20) DEFAULT 'active',
            description VARCHAR(500) DEFAULT NULL,
            created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
            updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            UNIQUE KEY uk_warehouse_location (warehouse_id, location_code)
        )
    """)
    print("[OK] warehouse_locations 表已确保存在")

    # 2. inbound_batches 新增字段
    alters = [
        ("location_id", "ALTER TABLE inbound_batches ADD COLUMN location_id INT DEFAULT NULL"),
        ("location_code", "ALTER TABLE inbound_batches ADD COLUMN location_code VARCHAR(50) DEFAULT NULL"),
        ("expiry_date", "ALTER TABLE inbound_batches ADD COLUMN expiry_date DATETIME(6) DEFAULT NULL"),
        ("current_quantity", "ALTER TABLE inbound_batches ADD COLUMN current_quantity DOUBLE NOT NULL DEFAULT 0"),
    ]
    for col_name, sql in alters:
        try:
            await conn.execute_query(sql)
            print(f"[OK] inbound_batches.{col_name} 字段已添加")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print(f"[SKIP] inbound_batches.{col_name} 字段已存在")
            else:
                print(f"[ERROR] inbound_batches.{col_name}: {e}")

    # 3. outbound_batches 新增字段
    try:
        await conn.execute_query("ALTER TABLE outbound_batches ADD COLUMN inbound_batch_id INT DEFAULT NULL")
        print("[OK] outbound_batches.inbound_batch_id 字段已添加")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("[SKIP] outbound_batches.inbound_batch_id 字段已存在")
        else:
            print(f"[ERROR] outbound_batches.inbound_batch_id: {e}")

    # 4. 迁移数据：已有 InboundBatch 设置 current_quantity = quantity
    result = await conn.execute_query(
        "UPDATE inbound_batches SET current_quantity = quantity WHERE current_quantity = 0"
    )
    print(f"[OK] 已更新 {result[0]} 条 InboundBatch 的 current_quantity")

    await Tortoise.close_connections()
    print("\n迁移完成!")


if __name__ == "__main__":
    asyncio.run(migrate())
