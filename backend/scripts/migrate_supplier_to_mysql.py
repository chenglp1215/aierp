"""
供应商数据迁移脚本 - MongoDB 到 MySQL
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from tortoise import Tortoise
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.settings import settings
from models_mysql.supplier import Supplier, SupplierBankAccount, SupplierBrand
from models_mysql.product import Brand


async def get_mongo_client():
    """获取 MongoDB 客户端"""
    mongo_url = settings.MONGO_URL
    client = AsyncIOMotorClient(mongo_url)
    return client


async def init_tortoise():
    """初始化 Tortoise ORM"""
    await Tortoise.init(
        db_url=f"mysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
        modules={"models": ["models_mysql.auth", "models_mysql.product", "models_mysql.supplier"]},
    )
    await Tortoise.generate_schemas()


async def get_brand_id_mapping() -> Dict[str, int]:
    """获取品牌 ObjectId 到 MySQL ID 的映射"""
    brands = await Brand.all()
    # 假设品牌已迁移，需要根据品牌名称匹配
    # 这里返回空字典，实际需要根据业务逻辑调整
    return {}


async def migrate_supplier(supplier_doc: Dict[str, Any], brand_mapping: Dict[str, int]) -> Optional[int]:
    """迁移单个供应商"""
    try:
        name = supplier_doc.get("name")
        if not name:
            print(f"跳过无名称供应商: {supplier_doc.get('_id')}")
            return None

        # 检查是否已存在
        existing = await Supplier.filter(name=name).first()
        if existing:
            print(f"供应商已存在: {name}, ID: {existing.id}")
            return existing.id

        # 创建供应商
        supplier = await Supplier.create(
            name=name,
            contact_person=supplier_doc.get("contact_person"),
            contact_phone=supplier_doc.get("contact_phone"),
            contact_email=supplier_doc.get("contact_email"),
            address=supplier_doc.get("address"),
            remark=supplier_doc.get("remark"),
            is_active=supplier_doc.get("is_active", True),
        )

        # 创建银行账户
        bank_account = supplier_doc.get("bank_account")
        if bank_account:
            await SupplierBankAccount.create(
                supplier=supplier,
                bank_name=bank_account.get("bank_name"),
                account_name=bank_account.get("account_name"),
                account_no=bank_account.get("account_no"),
                is_default=True,
            )

        # 创建品牌关联
        supplied_brands = supplier_doc.get("supplied_brands", [])
        for brand_data in supplied_brands:
            brand_id_str = str(brand_data.get("brand_id", ""))
            # 尝试通过名称匹配品牌
            brand_name = brand_data.get("brand_name")
            if brand_name:
                brand = await Brand.filter(name=brand_name).first()
                if brand:
                    await SupplierBrand.create(
                        supplier=supplier,
                        brand_id=brand.id,
                        discount=brand_data.get("discount", 1.0),
                        is_priority=brand_data.get("is_priority", False),
                    )

        return supplier.id
    except Exception as e:
        print(f"迁移供应商失败: {supplier_doc.get('name')}, 错误: {e}")
        return None


async def main():
    """主迁移函数"""
    print("=" * 60)
    print("开始供应商数据迁移...")
    print("=" * 60)

    # 初始化
    await init_tortoise()
    mongo_client = await get_mongo_client()
    db = mongo_client[settings.MONGO_DB_NAME]
    collection = db["suppliers"]

    # 获取品牌映射
    brand_mapping = await get_brand_id_mapping()

    # 统计
    total_count = await collection.count_documents({})
    print(f"MongoDB 供应商总数: {total_count}")

    # 迁移
    success_count = 0
    skip_count = 0
    error_count = 0

    cursor = collection.find({})
    async for doc in cursor:
        result = await migrate_supplier(doc, brand_mapping)
        if result:
            success_count += 1
        elif result is None:
            skip_count += 1
        else:
            error_count += 1

    # 输出统计
    print("\n" + "=" * 60)
    print("迁移完成!")
    print(f"成功: {success_count}")
    print(f"跳过: {skip_count}")
    print(f"失败: {error_count}")
    print("=" * 60)

    # 验证
    mysql_count = await Supplier.all().count()
    print(f"MySQL 供应商总数: {mysql_count}")

    # 关闭连接
    mongo_client.close()
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())