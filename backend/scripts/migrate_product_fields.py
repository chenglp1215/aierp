import asyncio
import random
import string
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

MONGODB_URL = "mongodb://132.232.212.151:58902"
MONGODB_DB_NAME = "oai_erp_test"

CHINESE_BRANDS = [
    "华为", "小米", "OPPO", "vivo", "一加", "realme", "荣耀", "中兴", "联想", "TCL",
    "海尔", "格力", "美的", "海信", "长虹", "创维", "小天鹅", "西门子", "松下", "索尼",
    "茅台", "五粮液", "泸州老窖", "洋河", "剑南春", "汾酒", "古井贡", "郎酒", "水井坊", "舍得",
    "农夫山泉", "怡宝", "康师傅", "统一", "娃哈哈", "王老吉", "加多宝", "雪碧", "可乐", "雪碧",
    "伊利", "蒙牛", "光明", "三元", "旺旺", "伊利", "蒙牛", "圣牧", "现代", "三元",
    "同仁堂", "云南白药", "999", "白药", "片仔癀", "马应龙", "九芝堂", "桐昆", "华润", "国药",
    "中粮", "益海", "鲁花", "金龙鱼", "福临门", "香满园", "元宝", "可口", "百事", "好丽友",
    "安踏", "李宁", "361", "特步", "贵人鸟", "鸿星尔克", "回力", "双星", "德尔惠", "361",
    "南极人", "北极绒", "恒源祥", "俞兆林", "三枪", "浪莎", "红蜻蜓", "奥康", "意尔康", "蜘蛛王",
    "立白", "蓝月亮", "超能", "雕牌", "奥妙", "汰渍", "碧浪", "洁霸", "威露士", "滴露"
]

CHEMICAL_CATEGORIES = [
    "有机原料", "无机原料", "溶剂", "助剂", "单体", "中间体",
    "表面活性剂", "聚合物", "催化剂", "颜料", "染料", "香精",
    "树脂", "橡胶", "塑料", "纤维", "农药", "医药原料", "食品添加剂"
]

def generate_tax_code():
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=18))
    return chars

async def migrate_products():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("📦 开始迁移商品数据...")

    products_collection = db.products
    specs_collection = db.product_specs

    batch_size = 100
    updated_count = 0

    async for product in products_collection.find({}):
        brand = random.choice(CHINESE_BRANDS)
        category = random.choice(CHEMICAL_CATEGORIES)
        tax_code = generate_tax_code()

        await products_collection.update_one(
            {"_id": product["_id"]},
            {
                "$set": {
                    "brand": brand,
                    "category": category,
                    "tax_code": tax_code
                }
            }
        )
        updated_count += 1

        if updated_count % batch_size == 0:
            print(f"   已迁移 {updated_count} 个商品...")

    print(f"\n✅ 商品迁移完成! 共更新 {updated_count} 个商品")

    print("\n🧹 开始清理规格中的冗余字段...")
    result = await specs_collection.update_many(
        {},
        {
            "$unset": {
                "brand": "",
                "category": "",
                "tax_code": ""
            }
        }
    )
    print(f"✅ 已从 {result.modified_count} 个规格中移除冗余字段")

    client.close()

if __name__ == "__main__":
    asyncio.run(migrate_products())
