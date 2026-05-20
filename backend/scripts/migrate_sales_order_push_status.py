"""
销售订单下推状态迁移脚本
为已存在的销售订单和明细计算 purchase_qty、pushed_qty 和 push_status

迁移逻辑:
1. 为每个销售订单明细计算 purchase_qty（直运全采购，仓库发货需采购数量）
2. 通过关联采购单明细聚合计算 pushed_qty
3. 计算订单的 push_status（none/partial/full/not_needed）
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from models_mysql.sales_order import SalesOrder, SalesOrderItem, OrderStatus, PushStatus, ShippingMethod
from models_mysql.purchase_order import PurchaseOrderItem


async def migrate_push_status():
    """迁移销售订单下推状态"""
    # 初始化数据库连接
    # 密码中的 @ 需要编码为 %40
    await Tortoise.init(
        db_url="mysql://admin:Chenglp1215%21%40%23@132.232.212.151:58901/erp_test",
        modules={"models": [
            "models_mysql.sales_order",
            "models_mysql.purchase_order",
            "models_mysql.product",
            "models_mysql.warehouse",
            "models_mysql.pending_outbound"
        ]},
    )

    print("开始迁移销售订单下推状态...")

    # 添加新字段（如果不存在）
    conn = Tortoise.get_connection("default")

    # 1. 添加 sales_orders.push_status 字段
    try:
        await conn.execute_query(
            "ALTER TABLE sales_orders ADD COLUMN push_status VARCHAR(20) DEFAULT 'none' COMMENT '下推状态'"
        )
        print("已添加 sales_orders.push_status 字段")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("sales_orders.push_status 字段已存在，跳过")
        else:
            print(f"添加 push_status 字段失败: {e}")

    # 2. 添加 sales_order_items.purchase_qty 字段
    try:
        await conn.execute_query(
            "ALTER TABLE sales_order_items ADD COLUMN purchase_qty INT DEFAULT 0 COMMENT '需采购数量'"
        )
        print("已添加 sales_order_items.purchase_qty 字段")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("sales_order_items.purchase_qty 字段已存在，跳过")
        else:
            print(f"添加 purchase_qty 字段失败: {e}")

    # 3. 添加 sales_order_items.pushed_qty 字段
    try:
        await conn.execute_query(
            "ALTER TABLE sales_order_items ADD COLUMN pushed_qty INT DEFAULT 0 COMMENT '已下推数量'"
        )
        print("已添加 sales_order_items.pushed_qty 字段")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("sales_order_items.pushed_qty 字段已存在，跳过")
        else:
            print(f"添加 pushed_qty 字段失败: {e}")

    # 4. 添加 purchase_order_items.source_sale_order_item_id 字段
    try:
        await conn.execute_query(
            "ALTER TABLE purchase_order_items ADD COLUMN source_sale_order_item_id INT NULL COMMENT '关联销售订单明细ID'"
        )
        print("已添加 purchase_order_items.source_sale_order_item_id 字段")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("purchase_order_items.source_sale_order_item_id 字段已存在，跳过")
        else:
            print(f"添加 source_sale_order_item_id 字段失败: {e}")

    # 5. 创建 pending_outbound_orders 表
    try:
        await conn.execute_query("""
            CREATE TABLE IF NOT EXISTS pending_outbound_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                pending_no VARCHAR(50) UNIQUE COMMENT '待出库单号',
                sales_order_id INT NULL COMMENT '销售订单ID',
                sales_order_no VARCHAR(50) NULL COMMENT '销售订单号',
                sales_order_item_id INT NULL COMMENT '销售订单明细ID',
                row_no INT NULL COMMENT '行号',
                warehouse_id INT NULL COMMENT '仓库ID',
                warehouse_name VARCHAR(100) NULL COMMENT '仓库名称',
                spec_id INT NULL COMMENT '规格ID',
                product_code VARCHAR(50) NULL COMMENT '商品编码',
                spec_code VARCHAR(50) NULL COMMENT '规格编码',
                locked_qty INT DEFAULT 0 COMMENT '锁定数量',
                out_qty INT DEFAULT 0 COMMENT '已出库数量',
                status VARCHAR(20) DEFAULT 'pending' COMMENT '状态',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) COMMENT '待出库单'
        """)
        print("已创建 pending_outbound_orders 表")
    except Exception as e:
        print(f"创建 pending_outbound_orders 表失败: {e}")

    # 获取所有已审核的订单（audited 状态）
    print("\n查询已审核订单...")
    audited_orders = await SalesOrder.filter(order_status=OrderStatus.AUDITED).all()
    print(f"找到 {len(audited_orders)} 个已审核订单")

    for order in audited_orders:
        print(f"\n处理订单: {order.order_no}")

        # 获取订单明细
        items = await SalesOrderItem.filter(sales_order_id=order.id).all()

        # 计算每个明细的 purchase_qty 和 pushed_qty
        total_purchase_qty = 0
        total_pushed_qty = 0

        for item in items:
            # 计算 purchase_qty
            # 直运发货：全部需要采购
            # 仓库发货：需要采购数量 = 数量 - 可用库存（暂时简化为全部需采购）
            if item.shipping_method == ShippingMethod.DIRECT:
                purchase_qty = item.qty
            else:
                # 仓库发货，暂时简化处理：全部需采购
                # 后续可通过库存查询优化
                purchase_qty = item.qty

            # 通过关联采购单明细计算 pushed_qty
            pushed_qty = 0
            if item.id:
                # 查询关联的采购单明细
                purchase_items = await PurchaseOrderItem.filter(
                    source_sale_order_item_id=item.id
                ).all()
                pushed_qty = sum(pi.purchase_qty for pi in purchase_items)

            # 更新明细
            item.purchase_qty = purchase_qty
            item.pushed_qty = pushed_qty
            await item.save()

            total_purchase_qty += purchase_qty
            total_pushed_qty += pushed_qty

            print(f"  行 {item.row_no}: qty={item.qty}, purchase_qty={purchase_qty}, pushed_qty={pushed_qty}")

        # 计算订单 push_status
        if total_purchase_qty == 0:
            push_status = PushStatus.NOT_NEEDED
        elif total_pushed_qty >= total_purchase_qty:
            push_status = PushStatus.FULL
        elif total_pushed_qty > 0:
            push_status = PushStatus.PARTIAL
        else:
            push_status = PushStatus.NONE

        # 更新订单
        order.push_status = push_status
        await order.save()

        print(f"  订单 push_status: {push_status.value}")

    # 验证迁移结果
    print("\n验证迁移结果:")

    none_count = await SalesOrder.filter(push_status=PushStatus.NONE).count()
    partial_count = await SalesOrder.filter(push_status=PushStatus.PARTIAL).count()
    full_count = await SalesOrder.filter(push_status=PushStatus.FULL).count()
    not_needed_count = await SalesOrder.filter(push_status=PushStatus.NOT_NEEDED).count()

    print(f"NONE: {none_count}")
    print(f"PARTIAL: {partial_count}")
    print(f"FULL: {full_count}")
    print(f"NOT_NEEDED: {not_needed_count}")

    await Tortoise.close_connections()
    print("\n迁移完成!")


if __name__ == "__main__":
    asyncio.run(migrate_push_status())