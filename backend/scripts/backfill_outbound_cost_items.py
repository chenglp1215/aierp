"""
补录历史出库批次对应的成本明细
- 对于已出库的批次，若入库批次有 cost_price 且待出库单有 sales_order_id，
  但尚未创建对应的 OUTBOUND 成本明细，则自动创建
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

    from models_mysql.warehouse import OutboundBatch, InboundBatch
    from models_mysql.pending_outbound import PendingOutboundOrder
    from models_mysql.sales_order import SalesOrderCostItem, CostType, CostSourceType

    outbound_batches = await OutboundBatch.filter(inbound_batch_id__isnull=False).all()
    created = 0
    skipped = 0

    for ob in outbound_batches:
        inbound_batch = await InboundBatch.filter(id=ob.inbound_batch_id).first()
        pending = await PendingOutboundOrder.filter(id=ob.pending_outbound_id).first()

        if not inbound_batch or inbound_batch.cost_price is None:
            skipped += 1
            continue
        if not pending or not pending.sales_order_id:
            skipped += 1
            continue

        # 检查是否已存在该出库批次的成本明细
        existing = await SalesOrderCostItem.filter(
            pending_outbound_id=pending.id,
            source_type=CostSourceType.OUTBOUND,
        ).all()

        # 检查 remark 中是否包含该 inbound_batch_id（粗粒度匹配）
        already_exists = any(
            str(ob.inbound_batch_id) in (ci.remark or "") for ci in existing
        )
        if already_exists:
            skipped += 1
            continue

        cost_amount = float(inbound_batch.cost_price) * ob.quantity
        await SalesOrderCostItem.create(
            sales_order_id=pending.sales_order_id,
            cost_type=CostType.PURCHASE,
            amount=round(cost_amount, 2),
            source_type=CostSourceType.OUTBOUND,
            source_no=pending.pending_no,
            pending_outbound_id=pending.id,
            remark=f"成本 {float(inbound_batch.cost_price):.2f} × 数量 {int(ob.quantity) if ob.quantity == int(ob.quantity) else ob.quantity}",
        )
        created += 1
        print(f"  创建: pending_id={pending.id}, inbound_id={ob.inbound_batch_id}, "
              f"cost_price={float(inbound_batch.cost_price)}, qty={ob.quantity}, "
              f"amount={round(cost_amount, 2)}, order_id={pending.sales_order_id}")

    print(f"\n完成: 创建 {created} 条成本明细, 跳过 {skipped} 条")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())