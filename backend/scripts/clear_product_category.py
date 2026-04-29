import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = "mongodb://10.5.5.66:20001"
MONGODB_DB_NAME = "oai_erp"


async def clear_product_category_fields():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("🧹 开始清除产品分类字段...")

    products_collection = db.products

    result = await products_collection.update_many(
        {},
        {
            "$unset": {
                "category": ""
            }
        }
    )
    print(f"✅ 已从 {result.modified_count} 个产品中清除 category 字段")

    client.close()
    print("\n✅ 完成!")


if __name__ == "__main__":
    asyncio.run(clear_product_category_fields())
