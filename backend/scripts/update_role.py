import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from config import settings


async def init_db():
    """初始化数据库连接"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    try:
        await client.admin.command("ping")
        print("✅ MongoDB 连接成功")
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        return None
    return client


async def update_role_code(role_id: str, new_code: str):
    """更新角色的 code 字段"""
    client = await init_db()
    if not client:
        return

    db = client[settings.MONGODB_DB_NAME]
    from bson import ObjectId

    try:
        result = await db.roles.update_one(
            {"_id": ObjectId(role_id)},
            {"$set": {"code": new_code, "updated_at": asyncio.get_event_loop().time()}}
        )
        if result.modified_count > 0:
            print(f"✅ 角色 {role_id} 的 code 已更新为: {new_code}")
        else:
            print(f"⚠️  未找到角色或 code 未变化")
    except Exception as e:
        print(f"❌ 更新失败: {e}")


async def find_role_by_id(role_id: str):
    """根据 ID 查找角色"""
    client = await init_db()
    if not client:
        return

    db = client[settings.MONGODB_DB_NAME]
    from bson import ObjectId

    try:
        role = await db.roles.find_one({"_id": ObjectId(role_id)})
        if role:
            role["_id"] = str(role["_id"])
            print(f"🔍 角色信息: {role}")
        else:
            print(f"⚠️  未找到角色 {role_id}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")


async def list_all_roles():
    """列出所有角色"""
    client = await init_db()
    if not client:
        return

    db = client[settings.MONGODB_DB_NAME]

    try:
        cursor = db.roles.find({})
        roles = []
        async for role in cursor:
            role["_id"] = str(role["_id"])
            roles.append(role)
        print(f"📋 所有角色 ({len(roles)} 个):")
        for role in roles:
            print(f"  - {role}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")


async def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/update_role.py list              - 列出所有角色")
        print("  python scripts/update_role.py find <role_id>    - 查找角色")
        print("  python scripts/update_role.py update <role_id> <new_code>  - 更新角色 code")
        return

    command = sys.argv[1]

    if command == "list":
        await list_all_roles()
    elif command == "find" and len(sys.argv) >= 3:
        await find_role_by_id(sys.argv[2])
    elif command == "update" and len(sys.argv) >= 4:
        await update_role_code(sys.argv[2], sys.argv[3])
    else:
        print("❌ 参数错误")


if __name__ == "__main__":
    asyncio.run(main())
