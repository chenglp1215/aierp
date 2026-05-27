"""
入库批次管理数据迁移脚本（幂等执行）
- 已有 InboundBatch 设置 current_quantity = quantity
- 已有 OutboundBatch 的 inbound_batch_id 留空（历史数据无法追溯）
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from models_mysql.warehouse import InboundBatch, OutboundBatch


async def migrate():
    """执行迁移"""
    # 初始化数据库连接
    await Tortoise.init(
        db_url="mysql://admin:Chenglp1215!%40%23@132.232.212.151:58901/erp_test",
        modules={"models": ["models_mysql.warehouse"]},
    )

    print("开始入库批次管理数据迁移...")

    # 1. 已有 InboundBatch 设置 current_quantity = quantity（幂等：仅处理 current_quantity 为 0 的记录）
    inbound_batches = await InboundBatch.filter(current_quantity=0).all()
    print(f"共 {len(inbound_batches)} 条入库批次需要设置 current_quantity")

    updated_inbound = 0
    for batch in inbound_batches:
        # 仅当 current_quantity 为默认值 0 时才更新（避免覆盖已有数据）
        if batch.current_quantity == 0 and batch.quantity > 0:
            batch.current_quantity = batch.quantity
            await batch.save()
            updated_inbound += 1

    print(f"入库批次迁移完成，更新 {updated_inbound} 条记录")

    # 2. 已有 OutboundBatch 的 inbound_batch_id 留空（历史数据无法追溯）
    # 无需操作，字段默认为 null，历史数据无法追溯

    print("出库批次 inbound_batch_id 保持为空（历史数据无法追溯）")

    # 关闭数据库连接
    await Tortoise.close_connections()

    print("迁移全部完成")


if __name__ == "__main__":
    asyncio.run(migrate())
