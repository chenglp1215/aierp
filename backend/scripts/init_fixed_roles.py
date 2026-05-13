import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import bcrypt

MONGODB_URL = "mongodb://132.232.212.151:58902"
MONGODB_DB_NAME = "oai_erp_test"


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


async def init_fixed_roles():
    print("🔄 连接到 MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]

    roles_collection = db["roles"]
    permissions_collection = db["permissions"]
    users_collection = db["users"]

    print("🗑️  清理旧角色和权限数据...")
    roles_result = await roles_collection.delete_many({})
    permissions_result = await permissions_collection.delete_many({})
    print(f"   已清除 {roles_result.deleted_count} 条角色记录")
    print(f"   已清除 {permissions_result.deleted_count} 条权限记录")

    print("\n📋 创建固化角色...")

    fixed_roles = [
        {
            "code": "super_admin",
            "name": "超级管理员",
            "description": "系统超级管理员，拥有所有权限",
            "is_fixed": True,
            "permissions": []
        },
        {
            "code": "warehouse_admin",
            "name": "仓库管理员",
            "description": "仓库管理员，负责仓库日常管理",
            "is_fixed": True,
            "permissions": []
        }
    ]

    role_ids = {}
    for role_data in fixed_roles:
        role_data["created_at"] = datetime.now()
        role_data["updated_at"] = datetime.now()
        role_data["status"] = "active"

        result = await roles_collection.insert_one(role_data)
        role_id = str(result.inserted_id)
        role_ids[role_data["code"]] = role_id

        print(f"   ✅ 角色: {role_data['name']} (code: {role_data['code']}, id: {role_id})")

    print("\n📋 创建测试用户...")

    test_users = [
        {
            "username": "admin",
            "password": get_password_hash("admin123"),
            "full_name": "系统管理员",
            "email": "admin@example.com",
            "phone": "13800138000",
            "status": "active",
            "role_ids": [role_ids["super_admin"]],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "username": "wh_admin",
            "password": get_password_hash("wh123456"),
            "full_name": "仓库管理员",
            "email": "wh_admin@example.com",
            "phone": "13800138001",
            "status": "active",
            "role_ids": [role_ids["warehouse_admin"]],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        },
        {
            "username": "wh_admin2",
            "password": get_password_hash("wh123456"),
            "full_name": "仓库管理员2号",
            "email": "wh_admin2@example.com",
            "phone": "13800138002",
            "status": "active",
            "role_ids": [role_ids["warehouse_admin"]],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]

    for user_data in test_users:
        existing = await users_collection.find_one({"username": user_data["username"]})
        if existing:
            await users_collection.update_one(
                {"username": user_data["username"]},
                {"$set": {
                    "role_ids": user_data["role_ids"],
                    "updated_at": datetime.now()
                }}
            )
            print(f"   🔄 用户 {user_data['username']} 已存在，已更新角色")
            continue

        result = await users_collection.insert_one(user_data)
        user_id = str(result.inserted_id)
        print(f"   ✅ 用户: {user_data['username']} (full_name: {user_data['full_name']}, id: {user_id})")

    print("\n" + "="*50)
    print("✅ 固化角色初始化完成!")
    print("="*50)
    print("\n📋 角色信息:")
    print(f"   超级管理员 (super_admin): {role_ids.get('super_admin', 'N/A')}")
    print(f"   仓库管理员 (warehouse_admin): {role_ids.get('warehouse_admin', 'N/A')}")

    print("\n📋 测试账号:")
    print("   超级管理员: admin / admin123")
    print("   仓库管理员: wh_admin / wh123456")
    print("   仓库管理员: wh_admin2 / wh123456")

    client.close()


if __name__ == "__main__":
    asyncio.run(init_fixed_roles())
