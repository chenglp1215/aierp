"""
待出库单增强功能数据迁移脚本
- 补充已存在待出库单的 outbound_type
- 补充已存在待出库单的收货地址
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from urllib.parse import quote_plus
from tortoise import Tortoise
from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus, OutboundType
from models_mysql.sales_order import SalesDeliverInfo


async def migrate():
    """执行迁移"""
    # 初始化数据库连接
    await Tortoise.init(
        db_url="mysql://admin:Chenglp1215!%40%23@132.232.212.151:58901/erp_test",
        modules={"models": ["models_mysql.auth", "models_mysql.warehouse", "models_mysql.sales_order", "models_mysql.pending_outbound", "models_mysql.product"]},
    )

    print("开始迁移...")

    # 获取所有待出库单
    pendings = await PendingOutboundOrder.all()
    print(f"共 {len(pendings)} 条待出库单")

    updated_count = 0
    for pending in pendings:
        need_save = False

        # 补充 outbound_type
        if pending.outbound_type is None:
            pending.outbound_type = OutboundType.ORDER_OUTBOUND
            need_save = True

        # 补充收货地址
        if pending.province is None and pending.city is None:
            deliver_info = await SalesDeliverInfo.filter(sales_order_id=pending.sales_order_id).first()
            if deliver_info:
                pending.province = deliver_info.province
                pending.city = deliver_info.city
                pending.address = deliver_info.addr
                pending.recipient_name = deliver_info.person_name
                pending.recipient_phone = deliver_info.person_tel
                need_save = True

        if need_save:
            await pending.save()
            updated_count += 1

    print(f"迁移完成，更新 {updated_count} 条记录")

    # 关闭数据库连接
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
