"""查询入库批次的 cost_price 实际值"""
import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

async def main():
    from tortoise import Tortoise
    config = {
        "connections": {
            "default": {
                "engine": "tortoise.backends.mysql",
                "credentials": {
                    "host": os.getenv("MYSQL_HOST", "132.232.212.151"),
                    "port": int(os.getenv("MYSQL_PORT", 58901)),
                    "user": os.getenv("MYSQL_USER", "admin"),
                    "password": os.getenv("MYSQL_PASSWORD", ""),
                    "database": os.getenv("MYSQL_DATABASE", "erp_test"),
                }
            }
        },
        "apps": {"models": {"models": ["models_mysql.warehouse", "models_mysql.product"], "default_connection": "default"}},
    }
    await Tortoise.init(config=config)

    from models_mysql.warehouse import InboundBatch
    batches = await InboundBatch.all().order_by("id")
    for b in batches:
        print(f"ID={b.id}, batch_no={b.batch_no}, spec_id={b.spec_id}, cost_price={b.cost_price}, qty={b.quantity}")

    await Tortoise.close_connections()

asyncio.run(main())
