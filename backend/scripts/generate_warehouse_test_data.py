import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

MONGODB_URL = "mongodb://10.5.5.66:20001"
MONGODB_DB_NAME = "oai_erp"

WAREHOUSE_NAMES = [
    "深圳中心仓", "广州配送中心", "东莞物流园", "佛山存储基地", "中山周转站",
    "珠海保税仓", "惠州仓储中心", "江门分发点", "肇庆中转仓", "清远储备库",
    "梅州地区仓", "汕头区域中心", "韶关物流站", "湛江配送点", "茂名储备中心",
    "潮州周转站", "揭阳存储基地", "汕尾物流园", "河源配送中心", "阳江仓储点"
]

CITIES = [
    "深圳市", "广州市", "东莞市", "佛山市", "中山市",
    "珠海市", "惠州市", "江门市", "肇庆市", "清远市",
    "梅州市", "汕头市", "韶关市", "湛江市", "茂名市",
    "潮州市", "揭阳市", "汕尾市", "河源市", "阳江市"
]

DISTRICTS = [
    "福田区", "罗湖区", "南山区", "宝安区", "龙岗区",
    "天河区", "越秀区", "白云区", "黄埔区", "番禺区",
    "莞城区", "南城区", "东城区", "万江区", "石碣镇",
    "禅城区", "南海区", "顺德区", "三水区", "高明区"
]

STREETS = [
    "工业园路", "科技园", "物流园", "仓储基地", "配送中心",
    "物流中心", "供应链园区", "电商产业园", "保税物流园", "货运站",
    "物流港", "仓储物流园", "工业大道", "物流园路", "仓储中心路"
]


def generate_warehouse_code(index: int) -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    return f"WH{date_str}{index:04d}"


def generate_address(city: str, district: str) -> str:
    street_num = random.randint(1, 999)
    street = random.choice(STREETS)
    return f"{city}{district}{street_num}号{street}"


def generate_description(name: str, city: str) -> str:
    descriptions = [
        f"{city}地区核心仓储中心，承担区域配送职能",
        f"{city}战略性物流节点，保障供应链畅通",
        f"{city}智能化仓储示范项目，提高物流效率",
        f"{city}综合型物流仓储基地，服务周边企业",
        f"{city}现代化配送中心，配备先进仓储设备"
    ]
    return random.choice(descriptions)


async def generate_warehouse_data():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    print("🗑️  清理旧仓库数据...")
    result = await db.warehouses.delete_many({})
    print(f"   已清除 {result.deleted_count} 条旧仓库记录")

    warehouse_admin_role = await db.roles.find_one({"code": "warehouse_admin"})
    if not warehouse_admin_role:
        print("❌ 未找到仓库管理员角色，请先运行 init_fixed_roles.py")
        client.close()
        return

    warehouse_admin_role_id = str(warehouse_admin_role["_id"])
    print(f"   仓库管理员角色ID: {warehouse_admin_role_id}")

    warehouse_admins = await db.users.find({
        "role_ids": warehouse_admin_role_id
    }).to_list(length=100)

    if not warehouse_admins:
        print("❌ 未找到仓库管理员用户，请先运行 init_fixed_roles.py")
        client.close()
        return

    admin_ids = [str(admin["_id"]) for admin in warehouse_admins]
    admin_names = {str(admin["_id"]): admin.get("full_name", admin["username"]) for admin in warehouse_admins}
    print(f"   找到 {len(admin_ids)} 个仓库管理员用户")

    print("\n📦 开始生成10个仓库数据...")

    warehouses_collection = db.warehouses
    used_names = set()

    for i in range(1, 11):
        warehouse_code = generate_warehouse_code(i)

        name = random.choice(WAREHOUSE_NAMES)
        while name in used_names:
            name = random.choice(WAREHOUSE_NAMES)
        used_names.add(name)

        city = random.choice(CITIES)
        district = random.choice(DISTRICTS)
        address = generate_address(city, district)

        manager_id = random.choice(admin_ids)
        manager_name = admin_names.get(manager_id, "未知")

        description = generate_description(name, city)

        status_choice = random.random()
        if status_choice < 0.7:
            status = "active"
        elif status_choice < 0.9:
            status = "inactive"
        else:
            status = "maintenance"

        warehouse = {
            "warehouse_code": warehouse_code,
            "name": name,
            "address": address,
            "manager_id": manager_id,
            "manager_name": manager_name,
            "status": status,
            "description": description,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        result = await warehouses_collection.insert_one(warehouse)
        print(f"   ✅ [{i}/10] {warehouse_code} - {name} | 管理员: {manager_name} ({status})")

    print(f"\n✅ 仓库数据生成完成! 共10条记录")

    print("\n📋 生成的数据预览:")
    cursor = warehouses_collection.find({}).limit(10)
    async for wh in cursor:
        print(f"   🏭 {wh['warehouse_code']} | {wh['name']} | {wh['address']} | 管理员: {wh.get('manager_name', 'N/A')}")

    client.close()


if __name__ == "__main__":
    asyncio.run(generate_warehouse_data())
