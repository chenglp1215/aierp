from typing import Optional, Dict, Any
from datetime import datetime
import random
import string

from .base_service import BaseService
from models.sales_order import (
    SalesOrderCreate,
    SalesOrderUpdate,
    OrderStatus,
    PaymentStatus,
    DeliveryType
)


class SalesOrderService(BaseService):
    """销售订单服务"""

    def __init__(self):
        super().__init__("sales_orders")

    def _generate_order_no(self) -> str:
        """生成订单编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"SO{date_str}{random_str}"

    def _calculate_amounts(self, items: list, discount_ratio: float = 100) -> Dict[str, float]:
        """计算订单金额"""
        total_amount = sum(item.get("subtotal", 0) for item in items)
        discount_amount = total_amount * (100 - discount_ratio) / 100
        final_amount = total_amount - discount_amount
        return {
            "total_amount": round(total_amount, 2),
            "discount_amount": round(discount_amount, 2),
            "final_amount": round(final_amount, 2)
        }

    async def _deduct_inventory(self, order_id: str, items: list, warehouse_id: str) -> bool:
        """扣减库存"""
        from services.inventory_service import stock_service
        adjustments = []
        for item in items:
            adjustments.append({
                "product_id": item.get("product_id"),
                "warehouse_id": warehouse_id,
                "quantity": item.get("quantity"),
                "is_add": False
            })
        result = await stock_service.batch_adjust_stocks(adjustments)
        return len(result.get("failed", [])) == 0

    async def _create_procurement_order(self, order_id: str, items: list, supplier_id: str, supplier_name: str) -> Optional[str]:
        """创建采购单"""
        from services.procurement_order_service import procurement_order_service
        from models.procurement_order import ProcurementOrderCreate, ProcurementOrderItem

        procurement_items = []
        for item in items:
            procurement_items.append(ProcurementOrderItem(
                product_id=item.get("product_id"),
                product_name=item.get("product_name"),
                product_code=item.get("product_code"),
                quantity=item.get("quantity"),
                unit_price=item.get("unit_price"),
                subtotal=item.get("subtotal")
            ))

        procurement_data = ProcurementOrderCreate(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            items=procurement_items
        )
        return await procurement_order_service.create_procurement_order(procurement_data, order_id)

    async def create_order(self, order_data: SalesOrderCreate) -> tuple:
        """创建销售订单，返回(order_no, db_id)"""
        data = order_data.model_dump()
        data["order_no"] = self._generate_order_no()

        items = data.get("items", [])
        discount_ratio = data.get("discount_ratio", 100)
        amounts = self._calculate_amounts(items, discount_ratio)
        data.update(amounts)

        data["status"] = OrderStatus.PENDING.value
        data["payment_status"] = PaymentStatus.UNPAID.value

        db_id = await self.create(data)
        return data["order_no"], db_id

    async def confirm_order(self, order_no: str, supplier_id: Optional[str] = None, supplier_name: Optional[str] = None) -> Dict[str, Any]:
        """确认订单并处理发货"""
        order = await self.get_order_by_no(order_no)
        if not order:
            return {"success": False, "message": "订单不存在"}

        if order.get("status") != OrderStatus.PENDING.value:
            return {"success": False, "message": "只有待确认的订单可以确认"}

        db_id = order.get("id")
        delivery_type = order.get("delivery_type")

        if delivery_type == DeliveryType.INVENTORY.value:
            warehouse_id = order.get("warehouse_id")
            if not warehouse_id:
                return {"success": False, "message": "库存发货必须选择仓库"}

            success = await self._deduct_inventory(db_id, order.get("items", []), warehouse_id)
            if not success:
                return {"success": False, "message": "库存扣减失败"}

        elif delivery_type == DeliveryType.DIRECT.value:
            if not supplier_id or not supplier_name:
                return {"success": False, "message": "采购直发必须提供供应商信息"}

            procurement_order_id = await self._create_procurement_order(
                db_id,
                order.get("items", []),
                supplier_id,
                supplier_name
            )
            if not procurement_order_id:
                return {"success": False, "message": "采购单创建失败"}

            await self.update_by_order_no(order_no, {"procurement_order_id": procurement_order_id})

        await self.update_status_by_order_no(order_no, OrderStatus.CONFIRMED)
        return {"success": True, "message": "订单确认成功"}

    async def update_order(self, order_no: str, order_data: SalesOrderUpdate) -> bool:
        """更新销售订单"""
        data = order_data.model_dump(exclude_unset=True)

        if "items" in data:
            discount_ratio = data.get("discount_ratio", 100)
            amounts = self._calculate_amounts(data["items"], discount_ratio)
            data.update(amounts)

        return await self.update_by_order_no(order_no, data)

    async def update_by_order_no(self, order_no: str, data: Dict[str, Any]) -> bool:
        """根据订单号更新订单"""
        result = await self.collection.update_one(
            {"order_no": order_no},
            {"$set": {**data, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    async def get_order_by_no(self, order_no: str) -> Optional[Dict[str, Any]]:
        """根据订单编号获取订单"""
        return await self.find_one({"order_no": order_no})

    async def list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        warehouse_name: Optional[str] = None,
        product_name: Optional[str] = None,
        product_id: Optional[str] = None,
        order_no: Optional[str] = None,
    ) -> Dict[str, Any]:
        """分页查询订单列表"""
        filters = {}

        if status:
            filters["status"] = status
        if customer_id:
            filters["customer_id"] = customer_id
        if customer_name:
            filters["customer_name"] = customer_name
        if warehouse_id:
            filters["warehouse_id"] = warehouse_id
        if warehouse_name:
            filters["warehouse_name"] = warehouse_name
        if product_name:
            filters["items__product_name"] = product_name
        if product_id:
            filters["items__product_id"] = product_id
        if order_no:
            filters["order_no"] = order_no
        return await self.list(page, page_size, filters, "created_at", -1)

    async def update_status_by_order_no(self, order_no: str, status: OrderStatus) -> bool:
        """根据订单号更新订单状态"""
        return await self.update_by_order_no(order_no, {"status": status.value})

    async def update_payment_status_by_order_no(self, order_no: str, payment_status: PaymentStatus) -> bool:
        """根据订单号更新付款状态"""
        return await self.update_by_order_no(order_no, {"payment_status": payment_status.value})

    async def delete_by_order_no(self, order_no: str) -> bool:
        """根据订单号删除订单"""
        result = await self.collection.delete_one({"order_no": order_no})
        return result.deleted_count > 0


sales_order_service = SalesOrderService()
