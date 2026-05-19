"""
采购单管理 - 服务层 (MySQL)
"""
import logging
import random
import string
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal

from tortoise.expressions import Q

from models_mysql.purchase_order import (
    PurchaseOrder, PurchaseOrderItem,
    PurchaseType, PurchaseStatus, InStatus, PayStatus
)
from models_mysql.sales_order import SalesOrder, SalesOrderItem, OrderStatus, ShippingMethod
from models_mysql.supplier import Supplier, SupplierBrand
from models_mysql.order_status_flow import OrderStatusFlow
from services.sales_order_service_mysql import sales_order_service_mysql as sales_order_service

logger = logging.getLogger(__name__)


class PurchaseOrderService:
    """采购单服务"""

    def _generate_purchase_no(self) -> str:
        """生成采购单号: PO + 日期 + 4位随机数"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"PO{date_str}{random_str}"

    def _calculate_item_amount(self, qty: int, price: Decimal, discount: Decimal) -> Decimal:
        """计算明细金额"""
        return round(float(qty) * float(price) * float(discount), 2)

    # ============ 创建采购单 ============

    async def create_from_sales_order(
        self,
        sales_order: SalesOrder,
        selected_items: List[SalesOrderItem],
        current_user: Dict = None
    ) -> List[Dict[str, Any]]:
        """从销售订单选中商品生成采购单（按品牌分组）"""
        generated_orders = []
        current_user = current_user or {}

        # 按品牌分组（通过关联链获取品牌）
        items_by_brand: Dict[int, List[SalesOrderItem]] = {}
        for item in selected_items:
            # 通过 spec -> product -> brand 获取品牌ID
            brand_id = 0
            if item.spec_id:
                try:
                    spec = item.spec
                    if spec and hasattr(spec, 'product') and spec.product:
                        product = spec.product
                        if hasattr(product, 'brand') and product.brand:
                            brand_id = product.brand.id or 0
                except (TypeError, AttributeError):
                    pass
            if brand_id not in items_by_brand:
                items_by_brand[brand_id] = []
            items_by_brand[brand_id].append(item)

        # 为每个品牌创建采购单
        for brand_id, items in items_by_brand.items():
            purchase_no = self._generate_purchase_no()

            # 确定采购类型
            purchase_type = PurchaseType.DIRECT
            if items and items[0].shipping_method == ShippingMethod.WAREHOUSE:
                purchase_type = PurchaseType.WAREHOUSE

            # 计算总金额
            total_amt = sum(self._calculate_item_amount(
                item.qty, item.price, Decimal(str(item.discount))
            ) for item in items)

            # 创建采购单主表（使用 brand_id 外键，不再传入 brand_name）
            purchase_order = await PurchaseOrder.create(
                purchase_no=purchase_no,
                purchase_type=purchase_type,
                source_sale_order_id=sales_order.id,
                source_sale_order_no=sales_order.order_no,
                brand_id=brand_id or None,
                purchase_status=PurchaseStatus.PENDING_REVIEW,
                total_amt=total_amt,
                tax_rate=sales_order.tax_rate,
                tax_amt=round(total_amt * float(sales_order.tax_rate), 2),
                total_tax_amt=round(total_amt * (1 + float(sales_order.tax_rate)), 2),
                expect_arrive_date=sales_order.expect_deliver_date,
                settle_type=sales_order.settle_type,
                remark=f"由销售订单 {sales_order.order_no} 下推生成",
                creator_id=current_user.get("id"),
            )

            # 创建明细（通过关联链获取 product_id 和 brand_id）
            for idx, item in enumerate(items, 1):
                amt = self._calculate_item_amount(item.qty, item.price, Decimal(str(item.discount)))

                # 通过关联链获取 product_id 和 brand_id
                product_id = None
                brand_id = None
                if item.spec_id:
                    try:
                        spec = item.spec
                        if spec and hasattr(spec, 'product') and spec.product:
                            product_id = spec.product.id
                            if hasattr(spec.product, 'brand') and spec.product.brand:
                                brand_id = spec.product.brand.id
                    except (TypeError, AttributeError):
                        pass

                await PurchaseOrderItem.create(
                    purchase_order=purchase_order,
                    row_no=idx,
                    spec_id=item.spec_id,
                    product_id=product_id,
                    brand_id=brand_id,
                    warehouse_id=item.warehouse_id,
                    purchase_qty=item.qty,
                    purchase_price=item.price,
                    discount=item.discount,
                    amt=amt,
                    source_sale_row_no=item.row_no,
                    shipping_method=item.shipping_method.value if item.shipping_method else None,
                )

            # 记录状态流转
            await OrderStatusFlow.create(
                order_no=purchase_no,
                order_type="purchase",
                field="purchase_status",
                old_value=None,
                new_value=PurchaseStatus.PENDING_REVIEW.value,
                operator=current_user.get("username", "system"),
                remark="从销售订单下推创建",
            )

            generated_orders.append({
                "purchase_no": purchase_no,
                "id": purchase_order.id,
                "brand_id": brand_id,
                "items_count": len(items),
            })

            logger.info(f"采购单创建成功: {purchase_no}")

        return generated_orders

    # ============ 查询采购单 ============

    async def get_order_by_no(self, purchase_no: str) -> Optional[Dict[str, Any]]:
        """根据采购单号获取详情"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).prefetch_related("items").first()
        if not order:
            return None

        # 对每个明细使用 select_related 获取关联数据
        items_data = []
        for item in order.items:
            # 使用 select_related 获取 spec 和 warehouse
            item_with_relations = await PurchaseOrderItem.filter(id=item.id).select_related(
                "spec__product__brand",
                "warehouse"
            ).first()
            if item_with_relations:
                items_data.append(await item_with_relations.to_dict())
            else:
                items_data.append(await item.to_dict())

        result = await order.to_dict()
        result["items"] = items_data
        return result

    async def list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        purchase_status: str = None,
        brand_id: int = None,
        source_sale_order_no: str = None,
    ) -> Tuple[List[Dict], int]:
        """获取采购单列表"""
        query = PurchaseOrder.all()

        if purchase_status:
            query = query.filter(purchase_status=purchase_status)
        if brand_id:
            query = query.filter(brand_id=brand_id)
        if source_sale_order_no:
            query = query.filter(source_sale_order_no__contains=source_sale_order_no)

        total = await query.count()
        orders = await query.offset((page - 1) * page_size).limit(page_size)

        # 使用 await 获取每个订单的 to_dict 结果
        return [await order.to_dict() for order in orders], total

    # ============ 状态操作 ============

    async def approve_order(self, purchase_no: str, operator: str = "system") -> bool:
        """审核通过"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if order.purchase_status != PurchaseStatus.PENDING_REVIEW:
            raise ValueError("只有待审核状态的采购单可以审核")

        old_status = order.purchase_status
        order.purchase_status = PurchaseStatus.READY_PURCHASE
        await order.save()

        await OrderStatusFlow.create(
            order_no=purchase_no,
            order_type="purchase",
            field="purchase_status",
            old_value=old_status.value,
            new_value=PurchaseStatus.READY_PURCHASE.value,
            operator=operator,
            remark="审核通过",
        )

        logger.info(f"采购单审核通过: {purchase_no}")
        return True

    async def recall_order(self, purchase_no: str, operator: str = "system") -> bool:
        """撤销采购单（仅限待审核状态）"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if order.purchase_status != PurchaseStatus.PENDING_REVIEW:
            raise ValueError("只有待审核状态的采购单可以撤回")

        # 获取关联的销售订单和行号
        source_sale_order_no = order.source_sale_order_no
        source_row_nos = [item.source_sale_row_no for item in order.items if item.source_sale_row_no]

        # 重置销售订单商品的下推状态
        if source_sale_order_no and source_row_nos:
            from services.sales_order_service_mysql import sales_order_service_mysql
            await sales_order_service_mysql.reset_push_status(
                source_sale_order_no, source_row_nos, operator
            )

        # 记录状态流转
        await OrderStatusFlow.create(
            order_no=purchase_no,
            order_type="purchase",
            field="purchase_status",
            old_value=order.purchase_status.value,
            new_value=PurchaseStatus.CANCELLED.value,
            operator=operator,
            remark="采购单撤回",
        )

        # 删除采购单
        await order.delete()

        logger.info(f"采购单撤销成功: {purchase_no}")
        return True

    # ============ 供应商选择 ============

    async def get_available_suppliers(self, purchase_no: str) -> List[Dict[str, Any]]:
        """获取采购单可选供应商列表（根据品牌筛选）"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if not order.brand_id:
            return []

        # 查询有该品牌供应资格的供应商
        supplier_brands = await SupplierBrand.filter(
            brand_id=order.brand_id
        ).select_related("supplier").all()

        suppliers = []
        for sb in supplier_brands:
            supplier = sb.supplier
            if supplier and supplier.is_active:
                suppliers.append({
                    "id": supplier.id,
                    "name": supplier.name,
                    "contact_person": supplier.contact_person,
                    "contact_phone": supplier.contact_phone,
                    "discount": float(sb.discount),
                    "is_priority": sb.is_priority,
                })

        # 按优先级和折扣排序
        suppliers.sort(key=lambda x: (-x["is_priority"], x["discount"]))

        return suppliers

    async def update_supplier(
        self,
        purchase_no: str,
        supplier_id: int,
        operator: str = "system"
    ) -> bool:
        """选择/修改供应商"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        # 检查状态是否允许修改供应商
        if order.purchase_status not in [PurchaseStatus.PENDING_REVIEW, PurchaseStatus.READY_PURCHASE]:
            raise ValueError("只有待审核或准备采购状态可以修改供应商")

        # 获取供应商信息
        supplier = await Supplier.filter(id=supplier_id).first()
        if not supplier:
            raise ValueError(f"供应商不存在: {supplier_id}")

        # 更新供应商信息
        order.supplier_id = supplier_id
        order.supplier_name = supplier.name
        await order.save()

        logger.info(f"采购单 {purchase_no} 供应商更新为: {supplier.name}")
        return True

    # ============ 物流信息 ============

    async def update_logistics(
        self,
        purchase_no: str,
        logistics_company: str = None,
        logistics_no: str = None,
        source_purchase_order_id: str = None,
        expect_arrive_date: date = None,
        operator: str = "system"
    ) -> bool:
        """更新物流信息"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        # 检查状态是否允许修改物流信息
        if order.purchase_status not in [PurchaseStatus.PENDING_REVIEW, PurchaseStatus.READY_PURCHASE]:
            raise ValueError("只有待审核或准备采购状态可以修改物流信息")

        # 更新物流信息
        if logistics_company:
            order.logistics_company = logistics_company
        if logistics_no:
            order.logistics_no = logistics_no
        if source_purchase_order_id:
            order.source_purchase_order_id = source_purchase_order_id
        if expect_arrive_date:
            order.expect_arrive_date = expect_arrive_date

        await order.save()

        logger.info(f"采购单 {purchase_no} 物流信息更新")
        return True

    # ============ 状态流转 ============

    async def start_purchase(self, purchase_no: str, operator: str = "system") -> bool:
        """开始采购（准备采购→采购中）"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if order.purchase_status != PurchaseStatus.READY_PURCHASE:
            raise ValueError("只有准备采购状态的采购单可以开始采购")

        old_status = order.purchase_status
        order.purchase_status = PurchaseStatus.PURCHASING
        await order.save()

        await OrderStatusFlow.create(
            order_no=purchase_no,
            order_type="purchase",
            field="purchase_status",
            old_value=old_status.value,
            new_value=PurchaseStatus.PURCHASING.value,
            operator=operator,
            remark="开始采购",
        )

        logger.info(f"采购单开始采购: {purchase_no}")
        return True

    async def complete_order(self, purchase_no: str, operator: str = "system") -> bool:
        """采购完成（采购中→采购完成）"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if order.purchase_status != PurchaseStatus.PURCHASING:
            raise ValueError("只有采购中状态的采购单可以完成")

        old_status = order.purchase_status
        order.purchase_status = PurchaseStatus.COMPLETED
        await order.save()

        await OrderStatusFlow.create(
            order_no=purchase_no,
            order_type="purchase",
            field="purchase_status",
            old_value=old_status.value,
            new_value=PurchaseStatus.COMPLETED.value,
            operator=operator,
            remark="采购完成",
        )

        logger.info(f"采购单采购完成: {purchase_no}")
        return True

    async def rollback_order(self, purchase_no: str, operator: str = "system") -> bool:
        """状态回退"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        # 采购完成状态不可回退
        if order.purchase_status == PurchaseStatus.COMPLETED:
            raise ValueError("采购完成状态不可回退")

        # 确定回退目标状态
        rollback_map = {
            PurchaseStatus.READY_PURCHASE: PurchaseStatus.PENDING_REVIEW,
            PurchaseStatus.PURCHASING: PurchaseStatus.READY_PURCHASE,
        }

        target_status = rollback_map.get(order.purchase_status)
        if not target_status:
            raise ValueError(f"当前状态 {order.purchase_status.value} 不支持回退")

        old_status = order.purchase_status
        order.purchase_status = target_status

        # 回退到待审核时，清空物流信息和供应商信息
        if target_status == PurchaseStatus.PENDING_REVIEW:
            order.logistics_company = None
            order.logistics_no = None
            order.source_purchase_order_id = None
            order.supplier_id = None
            order.supplier_name = None

        await order.save()

        await OrderStatusFlow.create(
            order_no=purchase_no,
            order_type="purchase",
            field="purchase_status",
            old_value=old_status.value,
            new_value=target_status.value,
            operator=operator,
            remark=f"状态回退: {old_status.value} -> {target_status.value}",
        )

        logger.info(f"采购单状态回退: {purchase_no}, {old_status.value} -> {target_status.value}")
        return True

    # ============ 关联销售单信息 ============

    async def get_source_sales_order_info(self, purchase_no: str) -> Optional[Dict[str, Any]]:
        """获取关联销售单简要信息"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if not order.source_sale_order_id:
            return None

        sales_order = await SalesOrder.filter(id=order.source_sale_order_id).first()
        if not sales_order:
            return None

        return {
            "order_no": sales_order.order_no,
            "order_date": sales_order.order_date.isoformat() if sales_order.order_date else None,
            "customer_name": sales_order.customer_name,
            "total_amt": float(sales_order.total_amt),
            "order_status": sales_order.order_status.value if sales_order.order_status else None,
        }

    async def complete_payment(
        self,
        purchase_no: str,
        current_user: Dict = None
    ) -> Dict[str, Any]:
        """付款完成 - 更新付款状态并创建成本明细"""
        purchase = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not purchase:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if purchase.pay_status == PayStatus.FULL:
            return {"message": "采购单已付款完成，无需重复操作"}

        # 更新付款状态
        purchase.pay_status = PayStatus.FULL
        await purchase.save()

        # 创建成本明细（如果有关联销售单）
        cost_item_created = False
        if purchase.source_sale_order_id:
            result = await sales_order_service.create_cost_item_from_purchase(
                sales_order_id=purchase.source_sale_order_id,
                purchase_order_id=purchase.id,
                purchase_no=purchase_no,
                amount=float(purchase.total_amt),
                current_user=current_user
            )
            cost_item_created = result is not None

        logger.info(f"采购单 {purchase_no} 付款完成")
        return {
            "purchase_no": purchase_no,
            "pay_status": PayStatus.FULL.value,
            "cost_item_created": cost_item_created
        }


# 创建服务实例
purchase_order_service_mysql = PurchaseOrderService()