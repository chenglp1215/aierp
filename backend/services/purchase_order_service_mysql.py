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
from models_mysql.sales_order import SalesOrder, SalesOrderItem, ShippingMethod
from models_mysql.order_status_flow import OrderStatusFlow

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
                purchase_status=PurchaseStatus.DRAFT,
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
                new_value=PurchaseStatus.DRAFT.value,
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

        if order.purchase_status != PurchaseStatus.DRAFT:
            raise ValueError("只有草稿状态的采购单可以审核")

        old_status = order.purchase_status
        order.purchase_status = PurchaseStatus.AUDITED
        await order.save()

        await OrderStatusFlow.create(
            order_no=purchase_no,
            order_type="purchase",
            field="purchase_status",
            old_value=old_status.value,
            new_value=PurchaseStatus.AUDITED.value,
            operator=operator,
            remark="审核通过",
        )

        logger.info(f"采购单审核通过: {purchase_no}")
        return True

    async def recall_order(self, purchase_no: str, operator: str = "system") -> bool:
        """撤销采购单"""
        order = await PurchaseOrder.filter(purchase_no=purchase_no).prefetch_related("items").first()
        if not order:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if order.purchase_status not in [PurchaseStatus.DRAFT, PurchaseStatus.AUDITED]:
            raise ValueError("只有草稿或已审核状态的采购单可以撤销")

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
            remark="采购单撤销",
        )

        # 删除采购单
        await order.delete()

        logger.info(f"采购单撤销成功: {purchase_no}")
        return True


# 创建服务实例
purchase_order_service_mysql = PurchaseOrderService()