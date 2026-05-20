"""
待出库单管理 - 服务层
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from tortoise.expressions import Q

from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
from models_mysql.warehouse import Stock
from models_mysql.sales_order import SalesOrderItem

logger = logging.getLogger(__name__)


class PendingOutboundService:
    """待出库单服务"""

    async def generate_pending_no(self) -> str:
        """生成待出库单号: PEND-YYYYMMDD-NNNN"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"PEND-{today}"
        count = await PendingOutboundOrder.filter(pending_no__startswith=prefix).count()
        sequence = count + 1
        return f"{prefix}-{sequence:04d}"

    async def create_pending_outbound(
        self,
        sales_order_id: int,
        sales_order_no: str,
        sales_order_item_id: int,
        row_no: int,
        warehouse_id: int,
        warehouse_name: str,
        spec_id: int,
        product_code: str,
        spec_code: str,
        locked_qty: int
    ) -> PendingOutboundOrder:
        """创建待出库单并锁定库存"""
        pending_no = await self.generate_pending_no()

        # 使用数据库事务和行锁确保并发安全
        async with Stock._meta.db.transaction():
            # 使用 select_for_update 锁定库存行，防止并发冲突
            stock = await Stock.filter(
                warehouse_id=warehouse_id,
                spec_id=spec_id
            ).select_for_update().first()

            if stock:
                stock.quantity -= locked_qty
                await stock.save()

            # 创建待出库单
            pending = await PendingOutboundOrder.create(
                pending_no=pending_no,
                sales_order_id=sales_order_id,
                sales_order_no=sales_order_no,
                sales_order_item_id=sales_order_item_id,
                row_no=row_no,
                warehouse_id=warehouse_id,
                warehouse_name=warehouse_name,
                spec_id=spec_id,
                product_code=product_code,
                spec_code=spec_code,
                locked_qty=locked_qty,
                out_qty=0,
                status=PendingOutboundStatus.PENDING
            )

        logger.info(f"创建待出库单: {pending_no}, 锁定库存: {locked_qty}")
        return pending

    async def list_pending_outbounds(
        self,
        page: int = 1,
        page_size: int = 20,
        warehouse_id: int = None,
        sales_order_no: str = None,
        status: str = None
    ) -> Tuple[List[Dict], int]:
        """查询待出库单列表"""
        query = PendingOutboundOrder.all()

        if warehouse_id:
            query = query.filter(warehouse_id=warehouse_id)
        if sales_order_no:
            query = query.filter(sales_order_no__contains=sales_order_no)
        if status:
            query = query.filter(status=status)

        total = await query.count()
        items = await query.offset((page - 1) * page_size).limit(page_size)

        return [item.to_dict() for item in items], total

    async def get_by_sales_order(self, sales_order_no: str) -> List[Dict]:
        """根据销售订单号查询待出库单"""
        items = await PendingOutboundOrder.filter(
            sales_order_no=sales_order_no
        ).order_by("-created_at")
        return [item.to_dict() for item in items]

    async def execute_outbound(
        self,
        pending_id: int,
        out_qty: int,
        operator: str = "system"
    ) -> Dict:
        """执行出库"""
        pending = await PendingOutboundOrder.filter(id=pending_id).first()
        if not pending:
            raise ValueError("待出库单不存在")

        if pending.status == PendingOutboundStatus.CANCELLED:
            raise ValueError("待出库单已取消")

        if pending.status == PendingOutboundStatus.FULL:
            raise ValueError("待出库单已完成出库")

        remaining = pending.locked_qty - pending.out_qty
        if out_qty > remaining:
            raise ValueError(f"出库数量不能超过待出库数量 {remaining}")

        # 更新待出库单
        pending.out_qty += out_qty
        if pending.out_qty >= pending.locked_qty:
            pending.status = PendingOutboundStatus.FULL
        elif pending.out_qty > 0:
            pending.status = PendingOutboundStatus.PARTIAL
        await pending.save()

        # 更新销售订单明细出库数量
        item = await SalesOrderItem.filter(id=pending.sales_order_item_id).first()
        if item:
            item.out_qty += out_qty
            await item.save()

        logger.info(f"待出库单 {pending.pending_no} 出库: {out_qty}, 操作人: {operator}")
        return pending.to_dict()

    async def cancel_pending_outbounds(
        self,
        sales_order_no: str,
        operator: str = "system"
    ) -> int:
        """取消订单的所有待出库单并释放库存"""
        pendings = await PendingOutboundOrder.filter(
            sales_order_no=sales_order_no,
            status__in=[PendingOutboundStatus.PENDING, PendingOutboundStatus.PARTIAL]
        ).all()

        count = 0
        for pending in pendings:
            # 释放库存
            remaining = pending.locked_qty - pending.out_qty
            if remaining > 0:
                stock = await Stock.filter(
                    warehouse_id=pending.warehouse_id,
                    spec_id=pending.spec_id
                ).first()
                if stock:
                    stock.quantity += remaining
                    await stock.save()

            # 更新状态
            pending.status = PendingOutboundStatus.CANCELLED
            await pending.save()
            count += 1

        logger.info(f"取消待出库单: {sales_order_no}, 数量: {count}, 操作人: {operator}")
        return count


pending_outbound_service = PendingOutboundService()
