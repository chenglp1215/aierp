from typing import Optional, Dict, Any
from datetime import datetime
import random
import string

from .base_service import BaseService
from models.procurement_order import (
    ProcurementOrderCreate,
    ProcurementOrderUpdate,
    ProcurementOrderStatus
)


class ProcurementOrderService(BaseService):
    """采购订单服务"""

    def __init__(self):
        super().__init__("procurement_orders")

    def _generate_procurement_no(self) -> str:
        """生成采购单编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"PO{date_str}{random_str}"

    def _calculate_total(self, items: list) -> float:
        """计算采购总金额"""
        return sum(item.get("subtotal", 0) for item in items)

    async def create_procurement_order(
        self,
        order_data: ProcurementOrderCreate,
        sales_order_id: Optional[str] = None
    ) -> str:
        """创建采购订单"""
        data = order_data.model_dump()
        data["procurement_no"] = self._generate_procurement_no()

        items = data.get("items", [])
        data["total_amount"] = self._calculate_total(items)

        data["status"] = ProcurementOrderStatus.PENDING.value
        data["sales_order_id"] = sales_order_id

        return await self.create(data)

    async def update_procurement_order(
        self,
        id: str,
        order_data: ProcurementOrderUpdate
    ) -> bool:
        """更新采购订单"""
        data = order_data.model_dump(exclude_unset=True)

        if "items" in data:
            data["total_amount"] = self._calculate_total(data["items"])

        return await self.update(id, data)

    async def get_by_sales_order_id(
        self,
        sales_order_id: str
    ) -> Optional[Dict[str, Any]]:
        """根据销售订单ID获取采购单"""
        return await self.find_one({"sales_order_id": sales_order_id})

    async def list_procurement_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询采购单列表"""
        filters = {}

        if status:
            filters["status"] = status
        if supplier_id:
            filters["supplier_id"] = supplier_id
        if keyword:
            filters["$or"] = [
                {"procurement_no": {"$regex": keyword, "$options": "i"}},
                {"supplier_name": {"$regex": keyword, "$options": "i"}}
            ]

        return await self.list(page, page_size, filters, "created_at", -1)

    async def update_status(
        self,
        id: str,
        status: ProcurementOrderStatus
    ) -> bool:
        """更新采购单状态"""
        return await self.update(id, {"status": status.value})


procurement_order_service = ProcurementOrderService()
