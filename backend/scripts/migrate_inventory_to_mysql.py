"""
数据迁移脚本：将库存管理数据从 MongoDB 迁移到 MySQL
"""
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from tortoise import Tortoise
from models_mysql.warehouse import Warehouse, Stock, InboundBatch, OutboundBatch
from models_mysql.product import Product, ProductSpec

# MongoDB 配置
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB = "erp"

# MySQL 配置
MYSQL_CONFIG = {
    "host": "132.232.212.151",
    "port": 58901,
    "user": "admin",
    "password": "Chenglp1215!@#",
    "database": "erp_test",
}


async def init_db():
    """初始化数据库连接"""
    # 初始化 Tortoise ORM
    await Tortoise.init(
        db_url=f"mysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}",
        modules={"models": ["models_mysql.auth", "models_mysql.product", "models_mysql.customer", "models_mysql.warehouse"]},
        generate_schemas=True,
    )
    print("MySQL 连接成功")


async def get_mongo_collections():
    """获取 MongoDB 集合"""
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    return {
        "warehouses": db["inventory_warehouses"],
        "stocks": db["inventory_stocks"],
        "inbound_batches": db["inventory_inbound_batches"],
        "outbound_batches": db["inventory_outbound_batches"],
    }


async def migrate_warehouses(collections: Dict) -> Dict[str, int]:
    """迁移仓库数据"""
    print("\n=== 开始迁移仓库数据 ===")
    warehouse_map = {}  # MongoDB ObjectId -> MySQL ID

    cursor = collections["warehouses"].find({})
    documents = await cursor.to_list(length=None)
    print(f"找到 {len(documents)} 条仓库记录")

    for doc in documents:
        try:
            warehouse = await Warehouse.create(
                warehouse_code=doc.get("warehouse_code", ""),
                name=doc.get("name", ""),
                address=doc.get("address", ""),
                manager_id=int(doc.get("manager_id", 0)) if doc.get("manager_id") else None,
                manager_name=doc.get("manager_name"),
                status=doc.get("status", "active"),
                description=doc.get("description"),
            )
            warehouse_map[str(doc["_id"])] = warehouse.id
            print(f"  迁移仓库: {warehouse.warehouse_code} - {warehouse.name}")
        except Exception as e:
            print(f"  迁移失败: {doc.get('warehouse_code')} - {e}")

    print(f"仓库迁移完成，共 {len(warehouse_map)} 条")
    return warehouse_map


async def migrate_stocks(collections: Dict, warehouse_map: Dict[str, int], product_map: Dict[str, int], spec_map: Dict[str, int]) -> Dict[str, int]:
    """迁移库存数据"""
    print("\n=== 开始迁移库存数据 ===")
    stock_map = {}  # MongoDB ObjectId -> MySQL ID

    cursor = collections["stocks"].find({})
    documents = await cursor.to_list(length=None)
    print(f"找到 {len(documents)} 条库存记录")

    for doc in documents:
        try:
            warehouse_id = warehouse_map.get(str(doc.get("warehouse_id", "")))
            product_id = product_map.get(str(doc.get("product_id", "")))
            spec_id = spec_map.get(str(doc.get("spec_id", "")))

            if not warehouse_id or not product_id or not spec_id:
                print(f"  跳过库存: 缺少关联ID - {doc.get('_id')}")
                continue

            stock = await Stock.create(
                warehouse_id=warehouse_id,
                product_id=product_id,
                product_code=doc.get("product_code", ""),
                product_name=doc.get("product_name", ""),
                spec_id=spec_id,
                spec_code=doc.get("spec_code", ""),
                quantity=float(doc.get("quantity", 0)),
                min_stock=float(doc.get("min_stock", 0)),
                max_stock=float(doc.get("max_stock", 0)),
                status=doc.get("status", "normal"),
            )
            stock_map[str(doc["_id"])] = stock.id
            print(f"  迁移库存: {stock.product_name} - {stock.spec_code}")
        except Exception as e:
            print(f"  迁移失败: {doc.get('_id')} - {e}")

    print(f"库存迁移完成，共 {len(stock_map)} 条")
    return stock_map


async def migrate_inbound_batches(collections: Dict, warehouse_map: Dict[str, int], stock_map: Dict[str, int]) -> int:
    """迁移入库批次数据"""
    print("\n=== 开始迁移入库批次数据 ===")
    count = 0

    cursor = collections["inbound_batches"].find({})
    documents = await cursor.to_list(length=None)
    print(f"找到 {len(documents)} 条入库批次记录")

    for doc in documents:
        try:
            warehouse_id = warehouse_map.get(str(doc.get("warehouse_id", "")))
            stock_id = stock_map.get(str(doc.get("stock_id", "")))

            if not warehouse_id:
                print(f"  跳过入库批次: 缺少仓库ID - {doc.get('_id')}")
                continue

            await InboundBatch.create(
                warehouse_id=warehouse_id,
                product_id=int(doc.get("product_id", 0)),
                product_code=doc.get("product_code", ""),
                product_name=doc.get("product_name", ""),
                spec_id=int(doc.get("spec_id", 0)),
                spec_code=doc.get("spec_code", ""),
                stock_id=stock_id or 0,
                quantity=float(doc.get("quantity", 0)),
                user_id=int(doc.get("user_id", 0)),
                user_name=doc.get("user_name", ""),
                remarks=doc.get("remarks"),
            )
            count += 1
        except Exception as e:
            print(f"  迁移失败: {doc.get('_id')} - {e}")

    print(f"入库批次迁移完成，共 {count} 条")
    return count


async def migrate_outbound_batches(collections: Dict, warehouse_map: Dict[str, int], stock_map: Dict[str, int]) -> int:
    """迁移出库批次数据"""
    print("\n=== 开始迁移出库批次数据 ===")
    count = 0

    cursor = collections["outbound_batches"].find({})
    documents = await cursor.to_list(length=None)
    print(f"找到 {len(documents)} 条出库批次记录")

    for doc in documents:
        try:
            warehouse_id = warehouse_map.get(str(doc.get("warehouse_id", "")))
            stock_id = stock_map.get(str(doc.get("stock_id", "")))

            if not warehouse_id:
                print(f"  跳过出库批次: 缺少仓库ID - {doc.get('_id')}")
                continue

            await OutboundBatch.create(
                warehouse_id=warehouse_id,
                product_id=int(doc.get("product_id", 0)),
                product_code=doc.get("product_code", ""),
                product_name=doc.get("product_name", ""),
                spec_id=int(doc.get("spec_id", 0)),
                spec_code=doc.get("spec_code", ""),
                stock_id=stock_id or 0,
                quantity=float(doc.get("quantity", 0)),
                user_id=int(doc.get("user_id", 0)),
                user_name=doc.get("user_name", ""),
                remarks=doc.get("remarks"),
            )
            count += 1
        except Exception as e:
            print(f"  迁移失败: {doc.get('_id')} - {e}")

    print(f"出库批次迁移完成，共 {count} 条")
    return count


async def build_product_maps() -> tuple[Dict[str, int], Dict[str, int]]:
    """构建商品和规格的 ID 映射"""
    print("\n=== 构建商品和规格映射 ===")

    # 获取所有商品
    products = await Product.all()
    product_map = {}  # 这里需要根据实际情况建立映射
    # 由于 MongoDB 和 MySQL 的 ID 不同，需要根据业务逻辑建立映射
    # 例如根据 product_code 匹配
    for product in products:
        product_map[str(product.id)] = product.id

    # 获取所有规格
    specs = await ProductSpec.all()
    spec_map = {}
    for spec in specs:
        spec_map[str(spec.id)] = spec.id

    print(f"商品映射: {len(product_map)} 条")
    print(f"规格映射: {len(spec_map)} 条")

    return product_map, spec_map


async def main():
    """主函数"""
    print("=" * 50)
    print("库存管理数据迁移脚本")
    print(f"开始时间: {datetime.now()}")
    print("=" * 50)

    # 初始化数据库
    await init_db()

    # 获取 MongoDB 集合
    collections = await get_mongo_collections()

    # 构建商品和规格映射
    product_map, spec_map = await build_product_maps()

    # 迁移数据
    warehouse_map = await migrate_warehouses(collections)
    stock_map = await migrate_stocks(collections, warehouse_map, product_map, spec_map)
    inbound_count = await migrate_inbound_batches(collections, warehouse_map, stock_map)
    outbound_count = await migrate_outbound_batches(collections, warehouse_map, stock_map)

    # 关闭数据库连接
    await Tortoise.close_connections()

    print("\n" + "=" * 50)
    print("迁移完成!")
    print(f"仓库: {len(warehouse_map)} 条")
    print(f"库存: {len(stock_map)} 条")
    print(f"入库批次: {inbound_count} 条")
    print(f"出库批次: {outbound_count} 条")
    print(f"结束时间: {datetime.now()}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())