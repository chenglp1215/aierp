import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient('mongodb://132.232.212.151:58902')
    db = client['oai_erp_test']

    # 检查 warehouse_admin 角色
    warehouse_admin_role = await db.roles.find_one({"code": "warehouse_admin"})
    if warehouse_admin_role:
        warehouse_admin_role_id = str(warehouse_admin_role['_id'])
        print(f"仓库管理员角色ID: {warehouse_admin_role_id}")

        # 查找所有用户
        users = await db.users.find({}).to_list(length=100)
        print(f"\n总用户数: {len(users)}")

        # 查找有仓库管理员角色的用户
        wh_admin_users = await db.users.find({
            "role_ids": warehouse_admin_role_id
        }).to_list(length=100)
        print(f"仓库管理员角色用户数: {len(wh_admin_users)}")
        for u in wh_admin_users:
            print(f"  - {u.get('username')} / {u.get('full_name')} / role_ids: {u.get('role_ids')}")
    else:
        print("未找到仓库管理员角色!")

    client.close()

asyncio.run(check())
