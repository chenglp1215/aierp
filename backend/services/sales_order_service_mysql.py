"""
销售订单管理 - 服务层 (MySQL)
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

from tortoise.expressions import Q
from tortoise.functions import Count

from models_mysql.sales_order import (
    SalesOrder, SalesOrderItem, SalesDeliverInfo,
    OrderStatus, DeliveryStatus, ReceiveStatus, InvoiceStatus, ShippingMethod
)
from models_mysql.order_status_flow import OrderStatusFlow

logger = logging.getLogger(__name__)


class SalesOrderService:
    """销售订单服务"""

    # ============ 订单号生成 ============

    async def generate_order_no(self) -> str:
        """生成订单号: SO + 日期 + 4位序列号"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"SO{today}"
        # 查询当天最大序号
        count = await SalesOrder.filter(order_no__startswith=prefix).count()
        sequence = count + 1
        return f"{prefix}{sequence:04d}"

    # ============ 金额计算 ============

    def _calculate_item_amount(self, qty: int, price: Decimal, discount: Decimal) -> Dict[str, Any]:
        """计算明细金额"""
        discounted_price = round(float(price) * float(discount), 2)
        amt = round(qty * discounted_price, 2)
        return {
            "discounted_price": discounted_price,
            "amt": amt,
        }

    def _calculate_order_totals(self, items: List[Dict], tax_rate: float) -> Dict[str, float]:
        """计算订单总金额"""
        total_amt = sum(item.get("amt", 0) for item in items)
        tax_amt = round(total_amt * tax_rate, 2)
        total_tax_amt = round(total_amt + tax_amt, 2)
        return {
            "total_amt": round(total_amt, 2),
            "tax_amt": tax_amt,
            "total_tax_amt": total_tax_amt,
        }

    # ============ 状态转换验证 ============

    def _can_transition_status(self, current: OrderStatus, target: OrderStatus) -> bool:
        """验证状态转换是否合法"""
        transitions = {
            OrderStatus.DRAFT: [OrderStatus.PENDING, OrderStatus.CANCELLED],
            OrderStatus.PENDING: [OrderStatus.AUDITED, OrderStatus.DRAFT],
            OrderStatus.AUDITED: [
                OrderStatus.PARTIALLY_PUSHED_TO_PURCHASE,
                OrderStatus.PUSHED_TO_PURCHASE,
                OrderStatus.CLOSED,
                OrderStatus.CANCELLED,
            ],
            OrderStatus.PARTIALLY_PUSHED_TO_PURCHASE: [
                OrderStatus.PUSHED_TO_PURCHASE,
                OrderStatus.CLOSED,
                OrderStatus.CANCELLED,
            ],
            OrderStatus.PUSHED_TO_PURCHASE: [OrderStatus.CLOSED, OrderStatus.CANCELLED],
            OrderStatus.CLOSED: [],
            OrderStatus.CANCELLED: [],
        }
        return target in transitions.get(current, [])

    # ============ 创建订单 ============

    async def create_order(
        self,
        data: Dict[str, Any],
        current_user: Dict[str, Any] = None,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """创建销售订单"""
        current_user = current_user or {}

        # 生成订单号
        order_no = await self.generate_order_no()

        # 计算明细金额
        items_data = data.get("items", [])
        for item in items_data:
            calc = self._calculate_item_amount(
                item.get("qty", 0),
                Decimal(str(item.get("price", 0))),
                Decimal(str(item.get("discount", 1.0))),
            )
            item["discounted_price"] = calc["discounted_price"]
            item["amt"] = calc["amt"]

        # 计算订单总金额
        tax_rate = data.get("tax_rate", 0.13)
        totals = self._calculate_order_totals(items_data, tax_rate)

        # 确定初始状态
        initial_status = OrderStatus.AUDITED if auto_approve else OrderStatus.DRAFT

        # 创建订单主表
        order = await SalesOrder.create(
            order_no=order_no,
            order_date=data.get("order_date") or date.today(),
            customer_id=data.get("customer_id"),
            customer_name=data.get("customer_name"),
            sale_user_id=current_user.get("id"),
            sale_user_name=current_user.get("full_name") or current_user.get("username"),
            order_status=initial_status,
            total_amt=totals["total_amt"],
            tax_rate=tax_rate,
            tax_amt=totals["tax_amt"],
            total_tax_amt=totals["total_tax_amt"],
            total_discount_amt=data.get("total_discount_amt", 0),
            expect_deliver_date=data.get("expect_deliver_date"),
            settle_type=data.get("settle_type"),
            remark=data.get("remark"),
            creator_id=current_user.get("id"),
            creator_name=current_user.get("full_name") or current_user.get("username"),
        )

        # 创建明细
        for idx, item in enumerate(items_data, 1):
            await SalesOrderItem.create(
                sales_order=order,
                row_no=item.get("row_no", idx),
                product_id=item.get("product_id"),
                product_code=item.get("product_code"),
                product_name=item.get("product_name"),
                spec_id=item.get("spec_id"),
                spec_code=item.get("spec_code"),
                brand_id=item.get("brand_id"),
                brand_name=item.get("brand_name"),
                warehouse_id=item.get("warehouse_id"),
                warehouse_name=item.get("warehouse_name"),
                qty=item.get("qty"),
                price=item.get("price"),
                discount=item.get("discount", 1.0),
                discounted_price=item.get("discounted_price"),
                amt=item.get("amt"),
                shipping_method=item.get("shipping_method", ShippingMethod.WAREHOUSE),
            )

        # 创建发货信息
        deliver_info = data.get("deliver_info", {})
        if deliver_info:
            await SalesDeliverInfo.create(
                sales_order=order,
                addr=deliver_info.get("addr"),
                province=deliver_info.get("province"),
                city=deliver_info.get("city"),
                person_name=deliver_info.get("person_name"),
                person_tel=deliver_info.get("person_tel"),
            )

        # 记录状态流转
        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=None,
            new_value=initial_status.value,
            operator=current_user.get("username", "system"),
            remark="创建订单" + ("并审核通过" if auto_approve else ""),
        )

        logger.info(f"销售订单创建成功: {order_no}")
        return {"order_no": order_no, "id": order.id}

    # ============ 查询订单 ============

    async def get_order_by_no(self, order_no: str) -> Optional[Dict[str, Any]]:
        """根据订单号获取订单详情"""
        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items", "deliver_infos").first()
        if not order:
            return None

        result = order.to_dict()
        result["items"] = [item.to_dict() for item in order.items]
        result["deliver_info"] = order.deliver_infos[0].to_dict() if order.deliver_infos else {}
        return result

    async def list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        order_status: str = None,
        customer_id: int = None,
        order_no: str = None,
        keyword: str = None,
    ) -> Tuple[List[Dict], int]:
        """获取订单列表"""
        query = SalesOrder.all()

        if order_status:
            query = query.filter(order_status=order_status)
        if customer_id:
            query = query.filter(customer_id=customer_id)
        if order_no:
            query = query.filter(order_no__contains=order_no)
        if keyword:
            query = query.filter(
                Q(order_no__contains=keyword) |
                Q(customer_name__contains=keyword)
            )

        total = await query.count()
        orders = await query.offset((page - 1) * page_size).limit(page_size)

        return [order.to_dict() for order in orders], total

    # ============ 更新订单 ============

    async def update_order(self, order_no: str, data: Dict[str, Any], current_user: Dict = None) -> bool:
        """更新订单（仅草稿状态可修改）"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if order.order_status not in [OrderStatus.DRAFT, OrderStatus.CANCELLED]:
            raise ValueError("只能修改草稿或已取消的订单")

        # 更新主表字段
        for field in ["order_date", "customer_id", "customer_name", "expect_deliver_date", "settle_type", "remark"]:
            if field in data:
                setattr(order, field, data[field])

        await order.save()

        # 更新明细
        if "items" in data:
            # 删除旧明细
            await SalesOrderItem.filter(sales_order=order).delete()
            # 创建新明细
            for idx, item in enumerate(data["items"], 1):
                calc = self._calculate_item_amount(
                    item.get("qty", 0),
                    Decimal(str(item.get("price", 0))),
                    Decimal(str(item.get("discount", 1.0))),
                )
                await SalesOrderItem.create(
                    sales_order=order,
                    row_no=item.get("row_no", idx),
                    product_id=item.get("product_id"),
                    product_code=item.get("product_code"),
                    product_name=item.get("product_name"),
                    spec_id=item.get("spec_id"),
                    spec_code=item.get("spec_code"),
                    brand_id=item.get("brand_id"),
                    brand_name=item.get("brand_name"),
                    warehouse_id=item.get("warehouse_id"),
                    warehouse_name=item.get("warehouse_name"),
                    qty=item.get("qty"),
                    price=item.get("price"),
                    discount=item.get("discount", 1.0),
                    discounted_price=calc["discounted_price"],
                    amt=calc["amt"],
                    shipping_method=item.get("shipping_method", ShippingMethod.WAREHOUSE),
                )

        logger.info(f"销售订单更新成功: {order_no}")
        return True

    # ============ 删除订单 ============

    async def delete_order(self, order_no: str) -> bool:
        """删除订单（仅草稿或已取消状态可删除）"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if order.order_status not in [OrderStatus.DRAFT, OrderStatus.CANCELLED]:
            raise ValueError("只能删除草稿或已取消的订单")

        await order.delete()
        logger.info(f"销售订单删除成功: {order_no}")
        return True

    # ============ 状态操作 ============

    async def submit_order(self, order_no: str, operator: str = "system") -> bool:
        """提交审核（draft → pending）"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if not self._can_transition_status(order.order_status, OrderStatus.PENDING):
            raise ValueError(f"订单状态不允许从 {order.order_status.value} 变更为 pending")

        old_status = order.order_status
        order.order_status = OrderStatus.PENDING
        await order.save()

        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=old_status.value,
            new_value=OrderStatus.PENDING.value,
            operator=operator,
            remark="提交审核",
        )

        logger.info(f"销售订单提交审核: {order_no}")
        return True

    async def approve_order(self, order_no: str, operator: str = "system") -> bool:
        """审核通过（pending → audited）"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if not self._can_transition_status(order.order_status, OrderStatus.AUDITED):
            raise ValueError(f"订单状态不允许从 {order.order_status.value} 变更为 audited")

        old_status = order.order_status
        order.order_status = OrderStatus.AUDITED
        await order.save()

        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=old_status.value,
            new_value=OrderStatus.AUDITED.value,
            operator=operator,
            remark="审核通过",
        )

        logger.info(f"销售订单审核通过: {order_no}")
        return True

    async def reject_order(self, order_no: str, operator: str = "system") -> bool:
        """驳回（pending → draft）"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if not self._can_transition_status(order.order_status, OrderStatus.DRAFT):
            raise ValueError(f"订单状态不允许从 {order.order_status.value} 变更为 draft")

        old_status = order.order_status
        order.order_status = OrderStatus.DRAFT
        await order.save()

        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=old_status.value,
            new_value=OrderStatus.DRAFT.value,
            operator=operator,
            remark="驳回",
        )

        logger.info(f"销售订单驳回: {order_no}")
        return True

    async def cancel_order(self, order_no: str, operator: str = "system") -> bool:
        """取消订单"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if not self._can_transition_status(order.order_status, OrderStatus.CANCELLED):
            raise ValueError(f"订单状态不允许取消")

        old_status = order.order_status
        order.order_status = OrderStatus.CANCELLED
        await order.save()

        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=old_status.value,
            new_value=OrderStatus.CANCELLED.value,
            operator=operator,
            remark="取消订单",
        )

        logger.info(f"销售订单取消: {order_no}")
        return True

    # ============ 下推采购相关 ============

    async def update_push_status(
        self,
        order_no: str,
        pushed_row_nos: List[int],
        operator: str = "system"
    ) -> bool:
        """更新下推状态"""
        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        # 更新明细的 pushed 标志
        for item in order.items:
            if item.row_no in pushed_row_nos:
                item.pushed = True
                await item.save()

        # 重新计算订单状态
        all_items = order.items
        all_pushed = all(item.pushed for item in all_items)
        any_pushed = any(item.pushed for item in all_items)

        old_status = order.order_status
        if all_pushed:
            order.order_status = OrderStatus.PUSHED_TO_PURCHASE
        elif any_pushed:
            order.order_status = OrderStatus.PARTIALLY_PUSHED_TO_PURCHASE

        await order.save()

        if order.order_status != old_status:
            await OrderStatusFlow.create(
                order_no=order_no,
                order_type="sales",
                field="order_status",
                old_value=old_status.value,
                new_value=order.order_status.value,
                operator=operator,
                remark="下推采购",
            )

        logger.info(f"销售订单下推状态更新: {order_no} -> {order.order_status.value}")
        return True

    async def reset_push_status(self, order_no: str, row_nos: List[int], operator: str = "system") -> bool:
        """重置下推状态（采购单撤销时使用）"""
        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        # 重置明细的 pushed 标志
        for item in order.items:
            if item.row_no in row_nos:
                item.pushed = False
                await item.save()

        # 重新计算订单状态
        all_items = order.items
        any_pushed = any(item.pushed for item in all_items)

        old_status = order.order_status
        if not any_pushed:
            order.order_status = OrderStatus.AUDITED
        elif all(item.pushed for item in all_items):
            order.order_status = OrderStatus.PUSHED_TO_PURCHASE
        else:
            order.order_status = OrderStatus.PARTIALLY_PUSHED_TO_PURCHASE

        await order.save()

        if order.order_status != old_status:
            await OrderStatusFlow.create(
                order_no=order_no,
                order_type="sales",
                field="order_status",
                old_value=old_status.value,
                new_value=order.order_status.value,
                operator=operator,
                remark="采购单撤销回退",
            )

        logger.info(f"销售订单下推状态重置: {order_no} -> {order.order_status.value}")
        return True


# 创建服务实例
sales_order_service_mysql = SalesOrderService()