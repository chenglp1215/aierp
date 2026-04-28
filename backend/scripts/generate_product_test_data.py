import asyncio
import random
import string
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from pymongo import MongoClient

MONGODB_URL = "mongodb://10.5.5.66:20001"
MONGODB_DB_NAME = "oai_erp"

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

CHEMICAL_CAS_PREFIXES = [
    "69", "71", "73", "75", "77", "79", "50", "52", "54", "56",
    "58", "60", "62", "64", "66", "67", "68", "72", "74", "76"
]

CHEMICAL_CATEGORIES = [
    "有机原料", "无机原料", "溶剂", "助剂", "单体", "中间体",
    "表面活性剂", "聚合物", "催化剂", "颜料", "染料", "香精",
    "树脂", "橡胶", "塑料", "纤维", "农药", "医药原料", "食品添加剂"
]

PRODUCT_PREFIXES = [
    "有机", "天然", "高纯", "分析纯", "化学纯", "工业级", "食品级", "医药级",
    "优级", "一级", "特级", "普通", "环保", "绿色", "进口", "出口"
]

PRODUCT_NAMES = [
    "乙醇", "甲醇", "丙酮", "丁酮", "乙酸乙酯", "二甲苯", "甲苯", "苯", "环己烷", "正己烷",
    "盐酸", "硫酸", "硝酸", "磷酸", "硼酸", "氢氟酸", "醋酸", "草酸", "柠檬酸", "乳酸",
    "氢氧化钠", "氢氧化钾", "碳酸钠", "碳酸钾", "氯化钠", "氯化钾", "硫酸铵", "硝酸铵", "磷酸铵",
    "甲醛", "乙醛", "丙醛", "丁醛", "苯甲醛", "糠醛", "丙酮", "丁酮", "环己酮", "甲乙酮",
    "苯酚", "甲酚", "萘酚", "对苯二酚", "邻苯二酚", "间苯二酚", "硝基苯", "苯胺", "甲苯胺", "二苯胺",
    "尿素", "三聚氰胺", "硝酸胍", "磷酸胍", "氨基胍", "硝基胍", "氯化石蜡", "阻燃剂", "增塑剂", "稳定剂",
    "钛白粉", "立德粉", "氧化锌", "氧化铁", "炭黑", "石墨", "滑石粉", "云母粉", "碳酸钙", "硫酸钡",
    "聚乙烯", "聚丙烯", "聚氯乙烯", "聚苯乙烯", "ABS", "PMMA", "PC", "PET", "PBT", "尼龙",
    "环氧树脂", "酚醛树脂", "氨基树脂", "聚氨酯", "有机硅", "氟树脂", "丙烯酸树脂", "聚酯树脂", "醇酸树脂", "天然树脂"
]

PACKAGING_UNITS = ["kg", "g", "L", "mL", "t", "袋", "桶", "箱", "瓶", "罐", "盒", "支"]
PACKAGING_SIZES = ["1", "5", "10", "20", "25", "50", "100", "200", "500", "1000"]
SALES_SPEC_UNITS = ["箱", "件", "桶", "袋", "盒", "托盘"]

def generate_product_code(index):
    date_str = datetime.now().strftime("%Y%m%d")
    return f"PROD{date_str}{index:06d}"

def generate_spec_code(product_index, spec_index):
    date_str = datetime.now().strftime("%Y%m%d")
    return f"SPEC{date_str}{product_index:04d}{spec_index:02d}"

def generate_cas_number():
    prefix = random.choice(CHEMICAL_CAS_PREFIXES)
    mid = ''.join(random.choices(string.digits, k=4))
    suffix = ''.join(random.choices(string.digits, k=1))
    return f"{prefix}-{mid}-{suffix}"

def generate_tax_code():
    chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=18))
    return chars

def generate_product_name():
    prefix = random.choice(PRODUCT_PREFIXES + [""])
    name = random.choice(PRODUCT_NAMES)
    suffix = random.choice(["", "溶液", "粉末", "颗粒", "晶体", "膏体", "乳浊液", "悬浮液", "浓缩液"])
    return f"{prefix}{name}{suffix}".strip()

def generate_packaging():
    size = random.choice(PACKAGING_SIZES)
    unit = random.choice(PACKAGING_UNITS)
    return f"{size}{unit}"

def generate_sales_spec():
    size = random.choice(PACKAGING_SIZES)
    unit = random.choice(PACKAGING_UNITS)
    qty = random.randint(2, 24)
    sales_unit = random.choice(SALES_SPEC_UNITS)
    return f"{size}{unit}*{qty}{sales_unit}"

def generate_price():
    base = random.choice([1, 10, 100, 1000])
    return round(random.uniform(0.5, 10) * base, 2)

def sync_clear_old_data():
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("🗑️  清理旧数据...")
    db.products.delete_many({})
    db.stocks.delete_many({})

    print("✅ 旧商品数据和库存数据已清除")

    client.close()
    return db

async def generate_test_data():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("🗑️  清理旧数据...")
    await db.products.delete_many({})
    await db.stocks.delete_many({})
    await db.product_specs.delete_many({})

    print("✅ 旧数据已清除")

    print("📦 开始生成测试数据...")

    products_collection = db.products
    specs_collection = db.product_specs
    stocks_collection = db.stocks

    product_count = 1000
    specs_per_product_range = (1, 5)
    specs_count = 0
    stocks_count = 0

    warehouse_ids = []
    cursor = db.warehouses.find({}, {"_id": 1}).limit(10)
    async for wh in cursor:
        warehouse_ids.append(wh["_id"])

    if not warehouse_ids:
        print("⚠️  未找到仓库数据，将创建不带仓库关联的库存")
        warehouse_ids = [None]

    batch_size = 100
    for i in range(1, product_count + 1):
        product_code = generate_product_code(i)
        product_name = generate_product_name()
        brand = random.choice(CHINESE_BRANDS)

        product = {
            "product_code": product_code,
            "name": product_name,
            "image_url": f"https://picsum.photos/seed/{product_code}/200/200",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        result = await products_collection.insert_one(product)
        product_id = result.inserted_id

        num_specs = random.randint(*specs_per_product_range)
        for j in range(1, num_specs + 1):
            spec_code = generate_spec_code(i, j)
            packaging = generate_packaging()
            sales_spec = generate_sales_spec()
            price = generate_price()
            tax_code = generate_tax_code()
            category = random.choice(CHEMICAL_CATEGORIES)
            cas_number = generate_cas_number()
            is_active = random.random() > 0.1

            spec = {
                "spec_code": spec_code,
                "product_id": str(product_id),
                "packaging": packaging,
                "sales_spec": sales_spec,
                "price": price,
                "brand": brand,
                "tax_code": tax_code,
                "category": category,
                "cas_number": cas_number,
                "is_active": is_active,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            spec_result = await specs_collection.insert_one(spec)
            spec_id = spec_result.inserted_id
            specs_count += 1

            if random.random() > 0.1:
                warehouse_id = random.choice(warehouse_ids)
                quantity = random.randint(0, 10000) if is_active else 0
                min_stock = random.randint(10, 100)
                max_stock = random.randint(min_stock * 10, min_stock * 100)

                if quantity == 0:
                    status = "out_of_stock"
                elif quantity < min_stock:
                    status = "low_stock"
                elif quantity > max_stock:
                    status = "overstock"
                else:
                    status = "normal"

                stock = {
                    "spec_id": str(spec_id),
                    "warehouse_id": str(warehouse_id) if warehouse_id else None,
                    "quantity": quantity,
                    "min_stock": min_stock,
                    "max_stock": max_stock,
                    "status": status,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                await stocks_collection.insert_one(stock)
                stocks_count += 1

        if i % batch_size == 0:
            print(f"   已生成 {i}/{product_count} 个商品...")

    print(f"\n✅ 测试数据生成完成!")
    print(f"   📦 商品数量: {product_count}")
    print(f"   🏷️  规格数量: {specs_count}")
    print(f"   📊 库存记录: {stocks_count}")

    client.close()

if __name__ == "__main__":
    asyncio.run(generate_test_data())
