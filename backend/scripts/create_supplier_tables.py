"""
创建供应商相关表的 SQL 脚本
运行此脚本前请确保数据库连接正常
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from urllib.parse import quote_plus
from config import settings


async def create_supplier_tables():
    """创建供应商相关表"""
    encoded_password = quote_plus(settings.MYSQL_PASSWORD)
    db_url = (
        f"mysql://{settings.MYSQL_USER}:{encoded_password}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    )

    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["models_mysql.supplier", "models_mysql.product"]},
    )

    # 生成表结构（如果表不存在则创建）
    await Tortoise.generate_schemas()

    print("供应商相关表创建完成!")
    print("- suppliers")
    print("- supplier_bank_accounts")
    print("- supplier_brands")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_supplier_tables())