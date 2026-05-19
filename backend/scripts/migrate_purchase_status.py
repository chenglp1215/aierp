"""
采购单状态迁移脚本
将现有采购单状态从旧值迁移到新值

旧状态 -> 新状态映射:
- draft -> pending_review
- audited -> ready_purchase
- closed -> closed (不变)
- cancelled -> cancelled (不变)
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from models_mysql.purchase_order import PurchaseOrder, PurchaseStatus


async def migrate_purchase_status():
    """迁移采购单状态"""
    # 初始化数据库连接
    await Tortoise.init(
        db_url="mysql://admin:Chenglp1215!@#@132.232.212.151:58901/erp_test",
        modules={"models": ["models_mysql.purchase_order", "models_mysql.product", "models_mysql.warehouse"]},
    )

    print("开始迁移采购单状态...")

    # 统计各状态数量
    draft_count = await PurchaseOrder.filter(purchase_status="draft").count()
    audited_count = await PurchaseOrder.filter(purchase_status="audited").count()

    print(f"待迁移: draft={draft_count}, audited={audited_count}")

    # 迁移 draft -> pending_review
    if draft_count > 0:
        draft_orders = await PurchaseOrder.filter(purchase_status="draft").all()
        for order in draft_orders:
            order.purchase_status = PurchaseStatus.PENDING_REVIEW
            await order.save()
        print(f"已迁移 {draft_count} 条 draft -> pending_review")

    # 迁移 audited -> ready_purchase
    if audited_count > 0:
        audited_orders = await PurchaseOrder.filter(purchase_status="audited").all()
        for order in audited_orders:
            order.purchase_status = PurchaseStatus.READY_PURCHASE
            await order.save()
        print(f"已迁移 {audited_count} 条 audited -> ready_purchase")

    # 添加新字段（如果不存在）
    print("检查并添加新字段...")

    # 执行 ALTER TABLE 添加新字段
    conn = Tortoise.get_connection("default")
    try:
        await conn.execute_query(
            "ALTER TABLE purchase_orders ADD COLUMN logistics_company VARCHAR(100) NULL COMMENT '物流公司'"
        )
        print("已添加 logistics_company 字段")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("logistics_company 字段已存在，跳过")
        else:
            print(f"添加 logistics_company 字段失败: {e}")

    try:
        await conn.execute_query(
            "ALTER TABLE purchase_orders ADD COLUMN logistics_no VARCHAR(100) NULL COMMENT '物流单号'"
        )
        print("已添加 logistics_no 字段")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("logistics_no 字段已存在，跳过")
        else:
            print(f"添加 logistics_no 字段失败: {e}")

    try:
        await conn.execute_query(
            "ALTER TABLE purchase_orders ADD COLUMN source_purchase_order_id VARCHAR(100) NULL COMMENT '采购源订单ID'"
        )
        print("已添加 source_purchase_order_id 字段")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("source_purchase_order_id 字段已存在，跳过")
        else:
            print(f"添加 source_purchase_order_id 字段失败: {e}")

    # 验证迁移结果
    print("\n验证迁移结果:")
    pending_review_count = await PurchaseOrder.filter(purchase_status=PurchaseStatus.PENDING_REVIEW).count()
    ready_purchase_count = await PurchaseOrder.filter(purchase_status=PurchaseStatus.READY_PURCHASE).count()

    print(f"pending_review: {pending_review_count}")
    print(f"ready_purchase: {ready_purchase_count}")

    await Tortoise.close_connections()
    print("\n迁移完成!")


if __name__ == "__main__":
    asyncio.run(migrate_purchase_status())
