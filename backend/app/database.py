from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from tortoise import Tortoise
from typing import Optional
from urllib.parse import quote_plus

from config import settings


class Database:
    """数据库连接管理"""

    _mongo_client: Optional[AsyncIOMotorClient] = None
    _redis_client: Optional[Redis] = None

    @classmethod
    async def init_db(cls):
        """初始化数据库连接"""
        # MongoDB 连接
        cls._mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls._redis_client = Redis.from_url(settings.REDIS_URL)

        # 测试连接
        try:
            await cls._mongo_client.admin.command("ping")
            print("[OK] MongoDB 连接成功")
        except Exception as e:
            print(f"[FAIL] MongoDB 连接失败: {e}")

        try:
            await cls._redis_client.ping()
            print("[OK] Redis 连接成功")
        except Exception as e:
            print(f"[FAIL] Redis 连接失败: {e}")

    @classmethod
    async def close_db(cls):
        """关闭数据库连接"""
        if cls._mongo_client:
            cls._mongo_client.close()
            print("[OK] MongoDB 连接已关闭")

        if cls._redis_client:
            await cls._redis_client.close()
            print("[OK] Redis 连接已关闭")

    @classmethod
    def get_mongo_client(cls) -> AsyncIOMotorClient:
        """获取 MongoDB 客户端"""
        if not cls._mongo_client:
            raise RuntimeError("MongoDB 客户端未初始化")
        return cls._mongo_client

    @classmethod
    def get_redis_client(cls) -> Redis:
        """获取 Redis 客户端"""
        if not cls._redis_client:
            raise RuntimeError("Redis 客户端未初始化")
        return cls._redis_client

    @classmethod
    def get_mongo_db(cls):
        """获取 MongoDB 数据库"""
        client = cls.get_mongo_client()
        return client[settings.MONGODB_DB_NAME]


# 全局实例
db = Database()


async def init_mysql():
    """初始化 MySQL (Tortoise ORM) 连接"""
    # URL 编码密码中的特殊字符
    encoded_password = quote_plus(settings.MYSQL_PASSWORD)
    # 连接池参数通过 URL 查询参数传递
    db_url = (
        f"mysql://{settings.MYSQL_USER}:{encoded_password}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        f"?minsize=1&maxsize=5&pool_recycle=1800"
    )

    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["models_mysql.auth", "models_mysql.product"]},
    )
    await Tortoise.generate_schemas()
    print("[OK] MySQL (Tortoise ORM) 连接成功")


async def close_mysql():
    """关闭 MySQL 连接"""
    await Tortoise.close_connections()
    print("[OK] MySQL 连接已关闭")


async def init_db():
    """初始化数据库"""
    await db.init_db()
    await init_mysql()


async def close_db():
    """关闭数据库连接"""
    await db.close_db()
    await close_mysql()
