"""
待出库单管理 - 服务层
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from tortoise.expressions import Q
from tortoise.functions import Sum
from tortoise.transactions import in_transaction

from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
from models_mysql.warehouse import Stock, OutboundBatch, InboundBatch
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
        locked_qty: int,
        outbound_type: str = "order_outbound",
        province: str = None,
        city: str = None,
        address: str = None,
        recipient_name: str = None,
        recipient_phone: str = None
    ) -> PendingOutboundOrder:
        """创建待出库单（锁定量通过查询动态计算，不再直接扣减 stock.quantity）"""
        pending_no = await self.generate_pending_no()

        async with in_transaction() as conn:
            # 库存记录（不强制要求存在，入库时会自动创建）
            stock = await Stock.filter(
                warehouse_id=warehouse_id,
                spec_id=spec_id
            ).using_db(conn).select_for_update().first()

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
                status=PendingOutboundStatus.PENDING,
                outbound_type=outbound_type,
                province=province,
                city=city,
                address=address,
                recipient_name=recipient_name,
                recipient_phone=recipient_phone,
                using_db=conn
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

        # 批量计算 out_qty
        item_ids = [item.id for item in items]
        batch_totals = {}
        if item_ids:
            rows = await OutboundBatch.filter(
                pending_outbound_id__in=item_ids
            ).group_by("pending_outbound_id").annotate(
                total=Sum("quantity")
            ).values_list("pending_outbound_id", "total")
            batch_totals = {row[0]: int(row[1]) for row in rows if row[1]}

        result = []
        for item in items:
            d = item.to_dict()
            d["out_qty"] = batch_totals.get(item.id, 0)
            result.append(d)

        return result, total

    async def get_by_sales_order(self, sales_order_no: str) -> List[Dict]:
        """根据销售订单号查询待出库单"""
        items = await PendingOutboundOrder.filter(
            sales_order_no=sales_order_no
        ).order_by("-created_at")
        return [item.to_dict() for item in items]

    async def get_available_batches(self, pending_id: int) -> List[Dict]:
        """获取待出库单可用的入库批次（先进先出）"""
        pending = await PendingOutboundOrder.filter(id=pending_id).first()
        if not pending:
            raise ValueError("待出库单不存在")

        # 查询 spec_id + warehouse_id 匹配的入库批次
        # 条件：current_quantity > 0 且未过期
        batches = await InboundBatch.filter(
            spec_id=pending.spec_id,
            warehouse_id=pending.warehouse_id,
            current_quantity__gt=0,
        ).order_by("expiry_date").all()

        # 过滤过期批次（MySQL DATETIME 是 offset-naive，用 naive datetime 比较）
        now = datetime.now()
        result = []
        for batch in batches:
            if batch.expiry_date:
                # 确保 expiry_date 也是 naive（去除时区信息）
                expiry = batch.expiry_date.replace(tzinfo=None) if batch.expiry_date.tzinfo else batch.expiry_date
                if expiry <= now:
                    continue
            result.append({
                "id": batch.id,
                "batch_no": batch.batch_no,
                "location_code": batch.location_code,
                "expiry_date": batch.expiry_date.isoformat() if batch.expiry_date else None,
                "current_quantity": batch.current_quantity,
                "quantity": batch.quantity,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
            })

        return result

    async def execute_outbound(
        self,
        pending_id: int,
        out_qty: int,
        operator: str = "system",
        user_id: int = None,
        user_name: str = None,
        batch_items: List[Dict] = None
    ) -> Dict:
        """执行出库，支持批次选择"""
        pending = await PendingOutboundOrder.filter(id=pending_id).first()
        if not pending:
            raise ValueError("待出库单不存在")

        if pending.status == PendingOutboundStatus.CANCELLED:
            raise ValueError("待出库单已取消")

        if pending.status == PendingOutboundStatus.OUTBOUND:
            raise ValueError("待出库单已出库")

        if pending.status == PendingOutboundStatus.SHIPPED:
            raise ValueError("待出库单已发货")

        current_out_qty_result = await OutboundBatch.filter(
            pending_outbound_id=pending.id
        ).annotate(total=Sum("quantity")).values_list("total", flat=True)
        current_out_qty = int(current_out_qty_result[0]) if current_out_qty_result and current_out_qty_result[0] else 0
        remaining = pending.locked_qty - current_out_qty
        if out_qty > remaining:
            raise ValueError(f"出库数量不能超过待出库数量 {remaining}")

        # 获取库存记录
        stock = await Stock.filter(
            warehouse_id=pending.warehouse_id,
            spec_id=pending.spec_id
        ).first()

        # 如果提供了批次明细，验证并执行批次出库
        if batch_items:
            # 验证：各批次出库数量之和 = out_qty
            total_batch_qty = sum(float(item.get("quantity", 0)) for item in batch_items)
            if abs(total_batch_qty - float(out_qty)) > 0.001:
                raise ValueError(f"批次出库数量之和({total_batch_qty})与出库数量({out_qty})不一致")

            # 逐批次验证并扣减
            for batch_item in batch_items:
                inbound_batch_id = batch_item.get("inbound_batch_id")
                batch_qty = float(batch_item.get("quantity", 0))

                if batch_qty <= 0:
                    raise ValueError("批次出库数量必须大于0")

                inbound_batch = await InboundBatch.get_or_none(id=inbound_batch_id)
                if not inbound_batch:
                    raise ValueError(f"入库批次不存在: {inbound_batch_id}")

                if batch_qty > inbound_batch.current_quantity:
                    raise ValueError(
                        f"入库批次 {inbound_batch_id} 剩余数量不足: "
                        f"当前 {inbound_batch.current_quantity}, 需要 {batch_qty}"
                    )

                # 扣减入库批次当前剩余数量
                inbound_batch.current_quantity -= batch_qty
                await inbound_batch.save()

                # 创建出库批次记录，关联入库批次
                if stock:
                    await OutboundBatch.create(
                        warehouse_id=pending.warehouse_id,
                        product_id=stock.product_id,
                        product_code=pending.product_code,
                        product_name=stock.product_name,
                        spec_id=pending.spec_id,
                        spec_code=pending.spec_code,
                        stock_id=stock.id,
                        quantity=batch_qty,
                        user_id=user_id or 0,
                        user_name=user_name or operator,
                        remarks=f"待出库单 {pending.pending_no} 出库（批次{inbound_batch_id}）",
                        pending_outbound_id=pending.id,
                        inbound_batch_id=inbound_batch_id
                    )
        else:
            # 未提供批次明细时，保持原有逻辑（兼容旧调用）
            if stock:
                await OutboundBatch.create(
                    warehouse_id=pending.warehouse_id,
                    product_id=stock.product_id,
                    product_code=pending.product_code,
                    product_name=stock.product_name,
                    spec_id=pending.spec_id,
                    spec_code=pending.spec_code,
                    stock_id=stock.id,
                    quantity=out_qty,
                    user_id=user_id or 0,
                    user_name=user_name or operator,
                    remarks=f"待出库单 {pending.pending_no} 出库",
                    pending_outbound_id=pending.id
                )

        # 更新待出库单状态
        new_out_total = current_out_qty + out_qty
        if new_out_total >= pending.locked_qty:
            pending.status = PendingOutboundStatus.OUTBOUND
        await pending.save()

        # 更新销售订单明细出库数量（基于批次汇总）
        total_out_result = await OutboundBatch.filter(
            pending_outbound__sales_order_item_id=pending.sales_order_item_id
        ).annotate(total=Sum("quantity")).values_list("total", flat=True)
        item = await SalesOrderItem.filter(id=pending.sales_order_item_id).first()
        if item:
            item.out_qty = int(total_out_result[0]) if total_out_result and total_out_result[0] else 0
            await item.save()

        # 同步更新销售订单发货状态
        from services.sales_order_service_mysql import sales_order_service_mysql
        await sales_order_service_mysql.update_order_status(
            order_id=pending.sales_order_id,
            status_types=["delivery"],
            operator=operator
        )

        logger.info(f"待出库单 {pending.pending_no} 出库: {out_qty}, 操作人: {operator}, 批次明细: {batch_items}")
        return pending.to_dict()

    async def cancel_pending_outbounds(
        self,
        sales_order_no: str,
        operator: str = "system"
    ) -> int:
        """取消订单的所有待出库单并释放库存"""
        pendings = await PendingOutboundOrder.filter(
            sales_order_no=sales_order_no,
            status=PendingOutboundStatus.PENDING
        ).all()

        count = 0
        for pending in pendings:
            # 更新状态（不再恢复 stock.quantity，锁定量通过查询动态计算）
            pending.status = PendingOutboundStatus.CANCELLED
            await pending.save()
            count += 1

        logger.info(f"取消待出库单: {sales_order_no}, 数量: {count}, 操作人: {operator}")
        return count


pending_outbound_service = PendingOutboundService()
