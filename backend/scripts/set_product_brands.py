import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URL = "mongodb://10.5.5.66:20001"
MONGODB_DB_NAME = "oai_erp"

CHINESE_BRANDS = [
    "华为", "小米", "OPPO", "vivo", "一加", "realme", "荣耀", "中兴", "联想", "TCL",
    "海尔", "格力", "美的", "海信", "长虹", "创维", "小天鹅", "西门子", "松下", "索尼",
    "茅台", "五粮液", "泸州老窖", "洋河", "剑南春", "汾酒", "古井贡", "郎酒", "水井坊", "舍得",
    "农夫山泉", "怡宝", "康师傅", "统一", "娃哈哈", "王老吉", "加多宝", "雪碧", "可乐",
    "伊利", "蒙牛", "光明", "三元", "旺旺", "圣牧",
    "同仁堂", "云南白药", "999", "片仔癀", "马应龙", "九芝堂",
    "中粮", "益海", "鲁花", "金龙鱼", "福临门", "香满园",
    "安踏", "李宁", "361", "特步", "贵人鸟", "鸿星尔克",
    "立白", "蓝月亮", "超能", "雕牌", "奥妙", "汰渍", "碧浪", "威露士", "滴露"
]


async def set_product_brands():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("🏷️  开始为产品设置品牌...")
    products_collection = db.products

    updated_count = 0
    batch_size = 100

    async for product in products_collection.find({}):
        brand = random.choice(CHINESE_BRANDS)
        await products_collection.update_one(
            {"_id": product["_id"]},
            {"$set": {"brand": brand}}
        )
        updated_count += 1
        if updated_count % batch_size == 0:
            print(f"   已设置 {updated_count} 个产品的品牌...")

    print(f"\n✅ 品牌设置完成! 共更新 {updated_count} 个产品")
    client.close()


if __name__ == "__main__":
    asyncio.run(set_product_brands())
