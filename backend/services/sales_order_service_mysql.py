"""
销售订单管理 - 服务层 (MySQL)
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

from tortoise.expressions import Q
from tortoise.functions import Count, Sum

from models_mysql.sales_order import (
    SalesOrder, SalesOrderItem, SalesDeliverInfo, SalesInvoiceInfo,
    SalesOrderCostItem,
    OrderStatus, DeliveryStatus, ReceiveStatus, InvoiceStatus, ShippingMethod,
    CostType, CostSourceType, FinanceStatus, PushStatus
)
from models_mysql.order_status_flow import OrderStatusFlow
from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
from models_mysql.warehouse import Stock

logger = logging.getLogger(__name__)


class SalesOrderService:
    """销售订单服务"""

    def _parse_int_field(self, value: Any) -> Optional[int]:
        """将字段值转换为整数或 None，处理空字符串情况"""
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _parse_shipping_method(self, value: Any) -> ShippingMethod:
        """将发货方式转换为枚举值，支持中文和英文"""
        if value is None:
            return ShippingMethod.WAREHOUSE
        # 中文映射
        shipping_map = {
            "直运": ShippingMethod.DIRECT,
            "direct": ShippingMethod.DIRECT,
            "仓库发货": ShippingMethod.WAREHOUSE,
            "warehouse": ShippingMethod.WAREHOUSE,
        }
        return shipping_map.get(value, ShippingMethod.WAREHOUSE)

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

    def _calculate_order_totals(self, items: List[Dict], tax_rate: float, freight_amt: float = 0) -> Dict[str, float]:
        """计算订单总金额

        运费不计税，计算公式：
        - 不含税最终金额 = 商品总金额 - 折扣 + 运费
        - 税额 = 商品总金额 * 税率（运费不参与计税）
        - 含税总额 = 不含税最终金额 + 税额
        """
        total_amt = sum(item.get("amt", 0) for item in items)
        # 运费不计税，税额仅基于商品总金额
        tax_amt = round(total_amt * tax_rate, 2)
        # 含税总额 = 商品总金额 + 税额 + 运费
        total_tax_amt = round(total_amt + tax_amt + freight_amt, 2)
        return {
            "total_amt": round(total_amt, 2),
            "tax_amt": tax_amt,
            "total_tax_amt": total_tax_amt,
        }

    async def _calculate_cost_amt(self, sales_order_id: int) -> float:
        """计算销售单成本总额（含税）"""
        result = await SalesOrderCostItem.filter(
            sales_order_id=sales_order_id
        ).annotate(total=Sum("amount")).first()
        return float(result.total) if result and result.total else 0.0

    async def _calculate_profit_amt(self, sales_order_id: int, total_tax_amt: float) -> float:
        """计算销售单利润（含税销售额 - 含税成本）"""
        cost_amt = await self._calculate_cost_amt(sales_order_id)
        return round(total_tax_amt - cost_amt, 2)

    # ============ 状态转换验证 ============

    def _can_transition_status(self, current: OrderStatus, target: OrderStatus) -> bool:
        """验证状态转换是否合法"""
        transitions = {
            OrderStatus.DRAFT: [OrderStatus.PENDING, OrderStatus.CANCELLED],
            OrderStatus.PENDING: [OrderStatus.AUDITED, OrderStatus.DRAFT],
            OrderStatus.AUDITED: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELLED: [],
        }
        return target in transitions.get(current, [])

    async def _calculate_push_status(self, order_id: int) -> PushStatus:
        """计算订单下推状态"""
        items = await SalesOrderItem.filter(sales_order_id=order_id).all()

        has_pending = False  # 有待下推
        has_pushed = False   # 有已下推
        all_not_needed = True  # 全部无需采购

        for item in items:
            if item.purchase_qty > 0:
                all_not_needed = False
                if item.pushed_qty < item.purchase_qty:
                    has_pending = True
                elif item.pushed_qty >= item.purchase_qty:
                    has_pushed = True

        if all_not_needed:
            return PushStatus.NOT_NEEDED
        if has_pending and has_pushed:
            return PushStatus.PARTIAL
        if has_pending:
            return PushStatus.NONE
        return PushStatus.FULL

    async def _calculate_delivery_status(self, order_id: int) -> DeliveryStatus:
        """计算发货状态（仅仓库发货）

        根据仓库发货明细的出库单发货状态计算订单发货状态。
        出库单状态为 shipped 视为已发货。
        直运明细不参与计算。
        """
        # 获取仓库发货方式的明细
        items = await SalesOrderItem.filter(
            sales_order_id=order_id,
            shipping_method=ShippingMethod.WAREHOUSE
        ).all()

        if not items:
            return DeliveryStatus.NONE  # 无仓库发货明细

        # 批量获取所有出库单
        item_ids = [item.id for item in items]
        all_pendings = await PendingOutboundOrder.filter(
            sales_order_item_id__in=item_ids
        ).all()

        # 按明细ID分组
        pendings_by_item = {}
        for p in all_pendings:
            if p.sales_order_item_id not in pendings_by_item:
                pendings_by_item[p.sales_order_item_id] = []
            pendings_by_item[p.sales_order_item_id].append(p)

        has_unshipped = False  # 有未发货
        has_shipped = False   # 有已发货

        for item in items:
            pendings = pendings_by_item.get(item.id, [])
            if not pendings:
                has_unshipped = True
                continue

            item_shipped = all(p.status == PendingOutboundStatus.SHIPPED for p in pendings)
            if item_shipped:
                has_shipped = True
            else:
                has_unshipped = True

        if has_shipped and has_unshipped:
            return DeliveryStatus.PARTIAL
        if has_shipped and not has_unshipped:
            return DeliveryStatus.FULL
        return DeliveryStatus.NONE

    async def update_order_status(
        self,
        order_id: int,
        status_types: List[str] = None,
        operator: str = "system"
    ) -> Dict[str, Any]:
        """更新销售订单状态

        统一的状态更新方法，支持选择性更新特定状态。

        Args:
            order_id: 订单ID
            status_types: 要更新的状态类型列表，可选值:
                - "push": 更新下推状态
                - "delivery": 更新发货状态
                - "receive": 更新收货状态（预留，暂不支持）
                - "invoice": 更新开票状态（预留，暂不支持）
                - "finance": 更新财务状态（预留，暂不支持）
                - None: 更新全部可计算状态（push, delivery）
            operator: 操作人

        Returns:
            更新后的状态字典
        """
        order = await SalesOrder.filter(id=order_id).first()
        if not order:
            raise ValueError(f"订单不存在: {order_id}")

        # 默认更新全部可计算状态
        if status_types is None:
            status_types = ["push", "delivery"]

        result = {
            "order_id": order_id,
            "order_no": order.order_no,
            "updated": {}
        }

        # 支持的状态类型
        supported_types = {
            "push": self._update_push_status,
            "delivery": self._update_delivery_status,
        }
        reserved_types = ["receive", "invoice", "finance"]

        for status_type in status_types:
            if status_type in supported_types:
                # 调用对应的更新方法
                update_result = await supported_types[status_type](order, operator)
                result["updated"][status_type] = update_result
            elif status_type in reserved_types:
                # 预留状态，暂不支持计算
                result["updated"][status_type] = {
                    "status": "skipped",
                    "reason": f"{status_type}_status 暂不支持自动计算"
                }
            else:
                logger.warning(f"未知的状态类型: {status_type}")

        await order.save()
        logger.info(f"订单 {order.order_no} 状态更新完成: {result['updated']}")
        return result

    async def _update_push_status(
        self,
        order: SalesOrder,
        operator: str
    ) -> Dict[str, Any]:
        """更新下推状态"""
        old_status = order.push_status
        new_status = await self._calculate_push_status(order.id)

        if old_status != new_status:
            order.push_status = new_status

            # 记录状态变更
            await OrderStatusFlow.create(
                order_no=order.order_no,
                order_type="sales",
                field="push_status",
                old_value=old_status.value if old_status else None,
                new_value=new_status.value,
                operator=operator,
                remark="状态自动计算更新"
            )

        return {
            "old": old_status.value if old_status else None,
            "new": new_status.value,
            "changed": old_status != new_status
        }

    async def _update_delivery_status(
        self,
        order: SalesOrder,
        operator: str
    ) -> Dict[str, Any]:
        """更新发货状态"""
        old_status = order.delivery_status
        new_status = await self._calculate_delivery_status(order.id)

        if old_status != new_status:
            order.delivery_status = new_status

            # 记录状态变更
            await OrderStatusFlow.create(
                order_no=order.order_no,
                order_type="sales",
                field="delivery_status",
                old_value=old_status.value if old_status else None,
                new_value=new_status.value,
                operator=operator,
                remark="状态自动计算更新"
            )

        return {
            "old": old_status.value if old_status else None,
            "new": new_status.value,
            "changed": old_status != new_status
        }

    async def _process_audit_pass(self, order: SalesOrder, operator: str = "system") -> None:
        """审核通过后处理：计算采购数量、生成待出库单、更新下推状态"""
        from services.pending_outbound_service import pending_outbound_service

        # 获取发货信息
        deliver_info = await SalesDeliverInfo.filter(sales_order_id=order.id).first()
        deliver_data = {
            "province": deliver_info.province if deliver_info else None,
            "city": deliver_info.city if deliver_info else None,
            "address": deliver_info.addr if deliver_info else None,
            "recipient_name": deliver_info.person_name if deliver_info else None,
            "recipient_phone": deliver_info.person_tel if deliver_info else None,
        }

        items = await SalesOrderItem.filter(sales_order_id=order.id).select_related(
            "spec__product__brand",
            "warehouse"
        ).all()

        for item in items:
            if item.shipping_method == ShippingMethod.DIRECT:
                # 直运：全部走采购
                item.purchase_qty = item.qty
            else:
                # 仓库发货：基于批次计算可用库存
                from models_mysql.warehouse import InboundBatch

                # 入库批次 current_quantity 之和
                batch_total = await InboundBatch.filter(
                    warehouse_id=item.warehouse_id,
                    spec_id=item.spec_id
                ).only("current_quantity").all()
                batch_sum = sum(float(b.current_quantity) for b in batch_total) if batch_total else 0

                # 锁定量 = PENDING 待出库单的 locked_qty 之和（out_qty 动态计算）
                pendings = await PendingOutboundOrder.filter(
                    warehouse_id=item.warehouse_id,
                    spec_id=item.spec_id,
                    status=PendingOutboundStatus.PENDING
                ).only("id", "locked_qty").all()
                pending_ids = [p.id for p in pendings]

                locked = 0
                if pending_ids:
                    from models_mysql.warehouse import OutboundBatch as _OutboundBatch
                    from tortoise.functions import Sum as _Sum
                    out_rows = await _OutboundBatch.filter(
                        pending_outbound_id__in=pending_ids
                    ).group_by("pending_outbound_id").annotate(
                        total=_Sum("quantity")
                    ).values_list("pending_outbound_id", "total")
                    out_map = {r[0]: int(r[1]) for r in out_rows if r[1]}
                    for p in pendings:
                        locked += p.locked_qty - out_map.get(p.id, 0)

                available_qty = max(0, batch_sum - locked)
                stock_out_qty = min(int(available_qty), item.qty)
                purchase_qty = item.qty - stock_out_qty

                logger.info(f"仓库发货计算: item={item.id}, warehouse={item.warehouse_id}, spec={item.spec_id}, batch_sum={batch_sum}, locked={locked}, available={available_qty}, stock_out={stock_out_qty}, purchase={purchase_qty}")

                item.purchase_qty = purchase_qty

                # 生成待出库单
                if stock_out_qty > 0:
                    warehouse = item.warehouse
                    warehouse_name = warehouse.name if warehouse else ""
                    spec = item.spec
                    product_code = spec.product.product_code if spec and spec.product else ""
                    spec_code = spec.spec_code if spec else ""

                    try:
                        await pending_outbound_service.create_pending_outbound(
                            sales_order_id=order.id,
                            sales_order_no=order.order_no,
                            sales_order_item_id=item.id,
                            row_no=item.row_no,
                            warehouse_id=item.warehouse_id,
                            warehouse_name=warehouse_name,
                            spec_id=item.spec_id,
                            product_code=product_code,
                            spec_code=spec_code,
                            locked_qty=stock_out_qty,
                            outbound_type="order_outbound",
                            province=deliver_data["province"],
                            city=deliver_data["city"],
                            address=deliver_data["address"],
                            recipient_name=deliver_data["recipient_name"],
                            recipient_phone=deliver_data["recipient_phone"]
                        )
                    except Exception as e:
                        logger.error(f"创建待出库单失败: order={order.order_no}, item={item.id}, error={e}")

            await item.save()

        # 更新订单状态
        await self.update_order_status(
            order_id=order.id,
            status_types=["push"],
            operator=operator
        )

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

        # 计算订单总金额（运费不计税）
        tax_rate = data.get("tax_rate", 0.13)
        freight_amt = float(data.get("freight_amt", 0) or 0)
        totals = self._calculate_order_totals(items_data, tax_rate, freight_amt)

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
            freight_amt=freight_amt,
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
                spec_id=self._parse_int_field(item.get("spec_id")),
                product_code=item.get("product_code"),  # 保留快照
                spec_code=item.get("spec_code"),  # 保留快照
                warehouse_id=self._parse_int_field(item.get("warehouse_id")),
                qty=item.get("qty"),
                price=item.get("price"),
                discount=item.get("discount", 1.0),
                discounted_price=item.get("discounted_price"),
                amt=item.get("amt"),
                shipping_method=self._parse_shipping_method(item.get("shipping_method")),
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

        # 创建开票信息
        invoice_info = data.get("invoice_info", {})
        if invoice_info:
            await SalesInvoiceInfo.create(
                sales_order=order,
                invoice_title=invoice_info.get("invoice_title"),
                invoice_type=invoice_info.get("invoice_type"),
                tax_number=invoice_info.get("tax_number"),
                bank_name=invoice_info.get("bank_name"),
                bank_account=invoice_info.get("bank_account"),
                address=invoice_info.get("address"),
                phone=invoice_info.get("phone"),
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

        # 如果自动审核，触发审核后处理（生成待出库单等）
        if auto_approve:
            # 需要重新查询订单以 prefetch_related items
            order = await SalesOrder.filter(id=order.id).prefetch_related("items").first()
            await self._process_audit_pass(order, current_user.get("username", "system"))

        logger.info(f"销售订单创建成功: {order_no}")
        return {"order_no": order_no, "id": order.id}

    # ============ 查询订单 ============

    async def get_order_by_no(self, order_no: str) -> Optional[Dict[str, Any]]:
        """根据订单号获取订单详情"""
        order = await SalesOrder.filter(order_no=order_no).prefetch_related(
            "items",
            "deliver_infos",
            "invoice_infos"
        ).first()
        if not order:
            return None

        # 对每个明细使用 select_related 获取关联数据
        items_data = []
        for item in order.items:
            # 使用 select_related 获取 spec 和 warehouse
            item_with_relations = await SalesOrderItem.filter(id=item.id).select_related(
                "spec__product__brand",
                "warehouse"
            ).first()
            if item_with_relations:
                items_data.append(await item_with_relations.to_dict())
            else:
                items_data.append(await item.to_dict())

        result = order.to_dict()
        result["items"] = items_data
        # deliver_infos 已通过 prefetch_related 预加载
        result["deliver_info"] = order.deliver_infos[0].to_dict() if order.deliver_infos else {}
        # invoice_infos 已通过 prefetch_related 预加载
        result["invoice_info"] = order.invoice_infos[0].to_dict() if order.invoice_infos else {}

        # 批量获取品牌采购员信息
        brand_ids = list(set(item.get("brand_id") for item in items_data if item.get("brand_id")))
        brand_purchasers = {}
        if brand_ids:
            from models_mysql.product import Brand
            brands = await Brand.filter(id__in=brand_ids).all()
            for brand in brands:
                if brand.purchaser_id:
                    brand_purchasers[str(brand.id)] = {
                        "purchaser_id": brand.purchaser_id,
                        "purchaser_name": brand.purchaser_name
                    }
        result["brand_purchasers"] = brand_purchasers

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

        # 获取每个订单的成本、利润和商品明细
        result = []
        for order in orders:
            order_dict = order.to_dict()

            # 计算成本和利润（含税销售额 - 含税成本）
            cost_amt = await self._calculate_cost_amt(order.id)
            order_dict["cost_amt"] = cost_amt
            order_dict["profit_amt"] = round(float(order.total_tax_amt) - cost_amt, 2)

            # 获取商品明细（用于展开行）
            items = await SalesOrderItem.filter(sales_order_id=order.id).select_related(
                "spec__product__brand",
                "warehouse"
            ).order_by("row_no")
            order_dict["items"] = [await item.to_dict() for item in items]

            result.append(order_dict)

        return result, total

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
                    spec_id=self._parse_int_field(item.get("spec_id")),
                    product_code=item.get("product_code"),  # 保留快照
                    spec_code=item.get("spec_code"),  # 保留快照
                    warehouse_id=self._parse_int_field(item.get("warehouse_id")),
                    qty=item.get("qty"),
                    price=item.get("price"),
                    discount=item.get("discount", 1.0),
                    discounted_price=calc["discounted_price"],
                    amt=calc["amt"],
                    shipping_method=self._parse_shipping_method(item.get("shipping_method")),
                )

        # 更新发货信息
        if "deliver_info" in data:
            deliver_info = data["deliver_info"]
            # 删除旧发货信息
            await SalesDeliverInfo.filter(sales_order=order).delete()
            # 创建新发货信息
            if deliver_info:
                await SalesDeliverInfo.create(
                    sales_order=order,
                    addr=deliver_info.get("addr"),
                    province=deliver_info.get("province"),
                    city=deliver_info.get("city"),
                    person_name=deliver_info.get("person_name"),
                    person_tel=deliver_info.get("person_tel"),
                )

        # 更新开票信息
        if "invoice_info" in data:
            invoice_info = data["invoice_info"]
            # 删除旧开票信息
            await SalesInvoiceInfo.filter(sales_order=order).delete()
            # 创建新开票信息
            if invoice_info:
                await SalesInvoiceInfo.create(
                    sales_order=order,
                    invoice_title=invoice_info.get("invoice_title"),
                    invoice_type=invoice_info.get("invoice_type"),
                    tax_number=invoice_info.get("tax_number"),
                    bank_name=invoice_info.get("bank_name"),
                    bank_account=invoice_info.get("bank_account"),
                    address=invoice_info.get("address"),
                    phone=invoice_info.get("phone"),
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
        """提交审核（draft → audited，跳过 pending）"""
        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        # 检查是否可以从当前状态流转到 audited
        if order.order_status != OrderStatus.DRAFT:
            raise ValueError(f"只有草稿状态的订单可以提交审核，当前状态: {order.order_status.value}")

        old_status = order.order_status
        order.order_status = OrderStatus.AUDITED
        await order.save()

        # 审核通过后处理
        await self._process_audit_pass(order, operator)

        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=old_status.value,
            new_value=OrderStatus.AUDITED.value,
            operator=operator,
            remark="提交审核（直接审核通过）",
        )

        logger.info(f"销售订单提交审核成功: {order_no}, {old_status.value} → audited")
        return True

    async def approve_order(self, order_no: str, operator: str = "system") -> bool:
        """审核通过（pending → audited）"""
        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if order.order_status != OrderStatus.PENDING:
            raise ValueError(f"订单状态不允许从 {order.order_status.value} 变更为 audited")

        old_status = order.order_status
        order.order_status = OrderStatus.AUDITED
        await order.save()

        # 审核通过后处理
        await self._process_audit_pass(order, operator)

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

    async def check_and_auto_complete(self, order_no: str, operator: str = "system") -> bool:
        """检查并触发订单自动完成

        当发货、收货、财务、开票状态均为最终状态时，自动将订单状态更新为 completed。
        最终状态条件：
        - delivery_status = full
        - receive_status = full
        - finance_status = reconciled
        - invoice_status = full
        """
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            logger.warning(f"检查自动完成失败: 订单不存在 {order_no}")
            return False

        # 已完成或已取消的订单不再处理
        if order.order_status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            return False

        # 检查是否满足自动完成条件
        is_ready = (
            order.delivery_status == DeliveryStatus.FULL and
            order.receive_status == ReceiveStatus.FULL and
            order.finance_status == FinanceStatus.RECONCILED and
            order.invoice_status == InvoiceStatus.FULL
        )

        if not is_ready:
            logger.debug(f"订单 {order_no} 不满足自动完成条件: "
                         f"delivery={order.delivery_status.value}, "
                         f"receive={order.receive_status.value}, "
                         f"finance={order.finance_status.value}, "
                         f"invoice={order.invoice_status.value}")
            return False

        # 满足条件，自动完成
        old_status = order.order_status
        order.order_status = OrderStatus.COMPLETED
        await order.save()

        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=old_status.value,
            new_value=OrderStatus.COMPLETED.value,
            operator=operator,
            remark="自动完成（发货、收货、财务、开票均为最终状态）",
        )

        logger.info(f"销售订单自动完成: {order_no}, {old_status.value} → completed")
        return True

    async def test_update_status(
        self,
        order_no: str,
        delivery_status: Optional[str] = None,
        receive_status: Optional[str] = None,
        finance_status: Optional[str] = None,
        invoice_status: Optional[str] = None,
        operator: str = "system"
    ) -> dict:
        """测试用：手动修改订单业务状态

        注意：此接口仅用于测试自动完成机制，后续版本删除。
        """
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        updates = []

        if delivery_status:
            order.delivery_status = DeliveryStatus(delivery_status)
            updates.append(f"delivery_status: {delivery_status}")

        if receive_status:
            order.receive_status = ReceiveStatus(receive_status)
            updates.append(f"receive_status: {receive_status}")

        if finance_status:
            order.finance_status = FinanceStatus(finance_status)
            updates.append(f"finance_status: {finance_status}")

        if invoice_status:
            order.invoice_status = InvoiceStatus(invoice_status)
            updates.append(f"invoice_status: {invoice_status}")

        await order.save()

        logger.info(f"测试状态修改: {order_no}, {', '.join(updates)}, operator={operator}")

        # 检查是否触发自动完成
        auto_completed = await self.check_and_auto_complete(order_no, operator)

        # 重新获取订单返回最新状态
        order = await SalesOrder.filter(order_no=order_no).first()
        return {
            "order_no": order_no,
            "delivery_status": order.delivery_status.value,
            "receive_status": order.receive_status.value,
            "finance_status": order.finance_status.value,
            "invoice_status": order.invoice_status.value,
            "order_status": order.order_status.value,
            "auto_completed": auto_completed
        }

    # ============ 下推采购相关 ============

    async def push_to_purchase(
        self,
        order_no: str,
        item_row_nos: List[int],
        current_user: Dict = None
    ) -> List[Dict]:
        """下推采购：将选中的销售订单明细生成采购单"""
        from services.purchase_order_service_mysql import purchase_order_service_mysql

        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if order.order_status != OrderStatus.AUDITED:
            raise ValueError("只有已审核订单可以下推采购")

        # 筛选待下推明细
        selected_items = []
        for item in order.items:
            if item.row_no in item_row_nos:
                if item.pushed_qty >= item.purchase_qty:
                    raise ValueError(f"行 {item.row_no} 已全部下推")
                selected_items.append(item)

        if not selected_items:
            raise ValueError("没有待下推的明细")

        # 预加载关联数据
        item_ids = [item.id for item in selected_items]
        selected_items = list(await SalesOrderItem.filter(id__in=item_ids).select_related(
            "spec__product__brand",
            "warehouse"
        ).all())

        # 生成采购单
        operator = current_user.get("username", "system") if current_user else "system"
        generated_orders = await purchase_order_service_mysql.create_from_sales_order(
            order, selected_items, current_user
        )

        # 更新明细的 pushed_qty
        for item in selected_items:
            item.pushed_qty = item.purchase_qty
            await item.save()

        # 更新订单下推状态
        await self.update_order_status(
            order_id=order.id,
            status_types=["push"],
            operator=operator
        )

        logger.info(f"销售订单 {order_no} 下推采购成功，生成 {len(generated_orders)} 张采购单")
        return generated_orders

    async def check_can_revoke(self, order_no: str) -> Dict[str, Any]:
        """检查订单是否可以撤销审核"""
        from models_mysql.purchase_order import PurchaseOrder, PurchaseStatus

        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if order.order_status != OrderStatus.AUDITED:
            return {"can_revoke": False, "reason": "只有已审核订单可以撤销"}

        # 检查待出库单
        pendings = await PendingOutboundOrder.filter(sales_order_no=order_no).all()
        for p in pendings:
            if p.status not in [PendingOutboundStatus.PENDING, PendingOutboundStatus.CANCELLED]:
                return {"can_revoke": False, "reason": "存在已出库的待出库单"}

        # 检查采购单
        purchase_orders = await PurchaseOrder.filter(source_sale_order_no=order_no).all()
        for po in purchase_orders:
            if po.purchase_status != PurchaseStatus.PENDING_REVIEW:
                return {"can_revoke": False, "reason": "存在已处理的采购单"}

        return {"can_revoke": True, "reason": ""}

    async def revoke_audit(self, order_no: str, operator: str = "system") -> bool:
        """撤销审核"""
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.purchase_order import PurchaseOrder, PurchaseOrderItem

        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        if order.order_status != OrderStatus.AUDITED:
            raise ValueError("只有已审核订单可以撤销")

        # 检查是否可撤销
        check_result = await self.check_can_revoke(order_no)
        if not check_result["can_revoke"]:
            raise ValueError(check_result["reason"])

        # 取消待出库单并释放库存
        await pending_outbound_service.cancel_pending_outbounds(order_no, operator)

        # 删除采购单
        purchase_orders = await PurchaseOrder.filter(source_sale_order_no=order_no).all()
        for po in purchase_orders:
            await PurchaseOrderItem.filter(purchase_order_id=po.id).delete()
            await po.delete()

        # 清空明细的采购数量
        for item in order.items:
            item.purchase_qty = 0
            item.pushed_qty = 0
            await item.save()

        # 清空下推状态，回退到草稿
        order.push_status = None
        order.order_status = OrderStatus.DRAFT
        await order.save()

        await OrderStatusFlow.create(
            order_no=order_no,
            order_type="sales",
            field="order_status",
            old_value=OrderStatus.AUDITED.value,
            new_value=OrderStatus.DRAFT.value,
            operator=operator,
            remark="撤销审核",
        )

        logger.info(f"销售订单撤销审核: {order_no}")
        return True

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

        # 更新明细的 pushed_qty
        for item in order.items:
            if item.row_no in pushed_row_nos:
                # 累加已下推数量（这里假设每次下推的数量为 purchase_qty）
                item.pushed_qty = item.purchase_qty
                await item.save()

        # 重新计算订单下推状态
        order.push_status = await self._calculate_push_status(order.id)
        await order.save()

        logger.info(f"销售订单下推状态更新: {order_no} -> {order.push_status.value}")
        return True

    async def reset_push_status(self, order_no: str, row_nos: List[int], operator: str = "system") -> bool:
        """重置下推状态（采购单撤销时使用）"""
        order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        # 重置明细的 pushed_qty
        for item in order.items:
            if item.row_no in row_nos:
                item.pushed_qty = 0
                await item.save()

        # 重新计算订单下推状态
        result = await self.update_order_status(
            order_id=order.id,
            status_types=["push"],
            operator=operator
        )

        logger.info(f"销售订单下推状态重置: {order_no} -> {result['updated']['push']['new']}")
        return True

    # ============ 成本明细管理 ============

    async def create_cost_item(
        self,
        order_no: str,
        data: Dict[str, Any],
        current_user: Dict = None
    ) -> Dict[str, Any]:
        """手动创建成本明细"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        current_user = current_user or {}
        cost_item = await SalesOrderCostItem.create(
            sales_order_id=order.id,
            cost_type=data.get("cost_type"),
            amount=data.get("amount"),
            source_type=CostSourceType.MANUAL,
            remark=data.get("remark"),
            creator_id=current_user.get("id"),
            creator_name=current_user.get("full_name") or current_user.get("username"),
        )

        logger.info(f"销售单 {order_no} 创建成本明细: {cost_item.id}")
        return cost_item.to_dict()

    async def create_cost_item_from_purchase(
        self,
        sales_order_id: int,
        purchase_order_id: int,
        purchase_no: str,
        amount: float,
        cost_type: str = "purchase",
        remark: str = None,
        current_user: Dict = None
    ) -> Optional[Dict[str, Any]]:
        """从采购单创建成本明细（采购单审核通过时调用）"""
        # 检查是否已存在相同类型的成本明细
        existing = await SalesOrderCostItem.filter(
            purchase_order_id=purchase_order_id,
            cost_type=cost_type
        ).first()
        if existing:
            logger.info(f"采购单 {purchase_no} {cost_type} 成本明细已存在，跳过创建")
            return None

        current_user = current_user or {}
        cost_item = await SalesOrderCostItem.create(
            sales_order_id=sales_order_id,
            cost_type=cost_type,
            amount=amount,
            source_type=CostSourceType.PURCHASE_ORDER,
            source_no=purchase_no,
            purchase_order_id=purchase_order_id,
            remark=remark,
            creator_id=current_user.get("id"),
            creator_name=current_user.get("full_name") or current_user.get("username"),
        )

        logger.info(f"销售单 {sales_order_id} 从采购单 {purchase_no} 创建 {cost_type} 成本明细")
        return cost_item.to_dict()

    async def list_cost_items(self, order_no: str) -> List[Dict[str, Any]]:
        """获取销售单成本明细列表"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        items = await SalesOrderCostItem.filter(
            sales_order_id=order.id
        ).order_by("-created_at")

        return [item.to_dict() for item in items]

    async def delete_cost_item(self, order_no: str, item_id: int) -> bool:
        """删除成本明细（仅 manual 类型可删除）"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        cost_item = await SalesOrderCostItem.filter(
            id=item_id,
            sales_order_id=order.id
        ).first()
        if not cost_item:
            raise ValueError("成本明细不存在")

        if cost_item.source_type == CostSourceType.PURCHASE_ORDER:
            raise ValueError("采购成本不可手动删除")

        await cost_item.delete()
        logger.info(f"销售单 {order_no} 删除成本明细: {item_id}")
        return True

    async def update_finance_status(self, order_no: str, finance_status: str) -> bool:
        """更新财务状态"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        order.finance_status = FinanceStatus(finance_status)
        await order.save()

        logger.info(f"销售单 {order_no} 财务状态更新为: {finance_status}")
        return True


# 创建服务实例
sales_order_service_mysql = SalesOrderService()