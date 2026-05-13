import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = "mongodb://132.232.212.151:58902"
MONGODB_DB_NAME = "oai_erp_test"


async def clean_warehouse_data():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("🗑️  清理仓库数据...")
    result = await db.warehouses.delete_many({})
    print(f"   ✅ 已清除 {result.deleted_count} 条仓库记录")

    print("🗑️  清理库存数据...")
    result = await db.stocks.delete_many({})
    print(f"   ✅ 已清除 {result.deleted_count} 条库存记录")

    print("🗑️  清理入库批次数据...")
    result = await db.inbound_batches.delete_many({})
    print(f"   ✅ 已清除 {result.deleted_count} 条入库批次记录")

    print("🗑️  清理出库批次数据...")
    result = await db.outbound_batches.delete_many({})
    print(f"   ✅ 已清除 {result.deleted_count} 条出库批次记录")

    print("\n✅ 仓库相关测试数据清理完成!")
    client.close()


if __name__ == "__main__":
    asyncio.run(clean_warehouse_data())
