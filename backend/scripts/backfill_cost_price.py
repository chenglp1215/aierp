"""
补录历史入库批次的成本价
- cost_price 为空的入库批次，从对应 ProductSpec.price 取默认值
- cost_price 已有值的保持不变
"""
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
        "apps": {
            "models": {
                "models": [
                    "models_mysql.warehouse",
                    "models_mysql.product",
                    "models_mysql.sales_order",
                    "models_mysql.pending_outbound",
                ],
                "default_connection": "default",
            }
        },
    }
    await Tortoise.init(config=config)

    from models_mysql.warehouse import InboundBatch
    from models_mysql.product import ProductSpec

    null_batches = await InboundBatch.filter(cost_price=None).all()
    print(f"cost_price 为空的入库批次: {len(null_batches)} 条")

    updated = 0
    skipped = 0
    for batch in null_batches:
        spec = await ProductSpec.filter(id=batch.spec_id).first()
        if spec and spec.price is not None:
            batch.cost_price = spec.price
            await batch.save()
            updated += 1
            print(f"  更新: ID={batch.id}, batch_no={batch.batch_no}, spec_id={batch.spec_id}, cost_price={float(spec.price)}")
        else:
            skipped += 1
            print(f"  跳过: ID={batch.id}, spec_id={batch.spec_id}, 规格无价格")

    print(f"\n完成: 更新 {updated} 条, 跳过 {skipped} 条")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())