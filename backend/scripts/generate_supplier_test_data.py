import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGODB_URL = "mongodb://10.5.5.66:20001"
MONGODB_DB_NAME = "oai_erp"

SUPPLIER_NAMES = [
    "鑫源化工", "华泰贸易", "中联物资", "东升供应链", "国润商贸",
    "天亿化工", "正本贸易", "合众物资", "瑞通化工", "恒昌商贸",
    "华盛化工", "金山物资", "永昌贸易", "中化国际", "华茂商贸",
    "龙腾化工", "盛源物资", "宏达贸易", "华北化工", "华东物资"
]

CONTACT_PERSONS = [
    "张经理", "李经理", "王经理", "刘经理", "陈经理",
    "赵经理", "黄经理", "周经理", "吴经理", "徐经理",
    "孙经理", "马经理", "朱经理", "胡经理", "郭经理"
]

BANK_NAMES = [
    "中国工商银行", "中国建设银行", "中国农业银行", "中国银行",
    "招商银行", "交通银行", "浦发银行", "民生银行", "兴业银行", "平安银行"
]

AREAS = [
    "北京市朝阳区", "上海市浦东新区", "广州市天河区", "深圳市南山区",
    "杭州市西湖区", "南京市鼓楼区", "武汉市武昌区", "成都市武侯区",
    "西安市雁塔区", "重庆市渝北区", "天津市滨海新区", "苏州市工业园区"
]

async def generate_supplier_test_data():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("📋 获取现有品牌数据...")
    brands = []
    async for brand in db.product_brands.find({}, {"_id": 1}).limit(20):
        brands.append(str(brand["_id"]))

    if not brands:
        print("⚠️  未找到品牌数据，请先创建品牌")
        return

    print(f"   找到 {len(brands)} 个品牌")

    print("🗑️  清理旧供应商数据...")
    await db.suppliers.delete_many({})
    print("✅ 旧供应商数据已清除")

    print("📦 开始生成供应商测试数据...")

    suppliers_collection = db.suppliers
    created_count = 0
    timestamp = datetime.now().strftime("%Y%m%d%H%M")

    for i in range(1, 11):
        num_brands = random.randint(1, min(5, len(brands)))
        selected_brands = random.sample(brands, num_brands)

        supplied_brands = []
        for brand_id in selected_brands:
            supplied_brands.append({
                "brand_id": brand_id,
                "discount": round(random.uniform(0.7, 1.0), 2),
                "is_priority": random.random() > 0.7
            })

        supplier = {
            "name": f"{random.choice(SUPPLIER_NAMES)}{timestamp[-4:]}{i:02d}",
            "contact_person": random.choice(CONTACT_PERSONS),
            "contact_phone": f"1{random.randint(3,9)}{random.randint(100000000, 999999999)}",
            "contact_email": f"supplier{i}@example.com",
            "address": f"{random.choice(AREAS)}{random.choice(['路', '街', '大道'])}{random.randint(1, 999)}号",
            "bank_account": {
                "bank_name": random.choice(BANK_NAMES),
                "account_name": f"{random.choice(SUPPLIER_NAMES)}有限公司",
                "account_no": f"{random.randint(100000000000, 999999999999)}{random.randint(1000, 9999)}"
            },
            "supplied_brands": supplied_brands,
            "remark": f"测试供应商{i}",
            "is_active": random.random() > 0.2,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        await suppliers_collection.insert_one(supplier)
        created_count += 1
        print(f"   ✅ 创建供应商: {supplier['name']} (供货品牌: {num_brands}个)")

    print(f"\n✅ 供应商测试数据生成完成!")
    print(f"   📦 供应商数量: {created_count}")

    client.close()

if __name__ == "__main__":
    asyncio.run(generate_supplier_test_data())