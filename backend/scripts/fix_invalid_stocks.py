import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGODB_URL = "mongodb://10.5.5.66:20001"
MONGODB_DB_NAME = "oai_erp"


async def fix_stock_data():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("📋 获取所有仓库ID...")
    warehouse_ids = set()
    async for wh in db.warehouses.find({}, {"_id": 1}):
        warehouse_ids.add(str(wh["_id"]))
    print(f"   现有仓库数量: {len(warehouse_ids)}")

    print("\n🔍 检查库存记录中的 warehouse_id...")
    invalid_stock_ids = []
    async for stock in db.stocks.find({}, {"_id": 1, "warehouse_id": 1}):
        stock_id = str(stock["_id"])
        warehouse_id = stock.get("warehouse_id")
        if not warehouse_id or warehouse_id not in warehouse_ids:
            invalid_stock_ids.append(stock_id)

    print(f"   发现 {len(invalid_stock_ids)} 条无效库存记录")

    if invalid_stock_ids:
        print(f"\n🗑️  删除无效库存记录...")
        result = await db.stocks.delete_many({"_id": {"$in": [ObjectId(sid) for sid in invalid_stock_ids]}})
        print(f"   已删除 {result.deleted_count} 条记录")
    else:
        print("   无需删除的记录")

    client.close()
    print("\n✅ 修复完成!")


if __name__ == "__main__":
    asyncio.run(fix_stock_data())