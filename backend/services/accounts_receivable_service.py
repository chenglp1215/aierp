from typing import Optional, Dict, Any
from datetime import datetime
import random
import string

from .base_service import BaseService
from models.accounts_receivable import (
    ReceivableCreate,
    ReceivableUpdate,
    ReceivableRecordCreate,
    ReceivableStatus,
    PaymentMethod
)


class AccountsReceivableService(BaseService):
    """应收款单服务"""

    def __init__(self):
        super().__init__("accounts_receivable")

    def _generate_receivable_no(self) -> str:
        """生成应收单编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"AR{date_str}{random_str}"

    async def create_receivable(
        self,
        receivable_data: ReceivableCreate
    ) -> str:
        """创建应收单"""
        data = receivable_data.model_dump()
        data["receivable_no"] = self._generate_receivable_no()
        data["status"] = ReceivableStatus.UNPAID.value
        data["records"] = []

        return await self.create(data)

    async def record_payment(
        self,
        id: str,
        record_data: ReceivableRecordCreate
    ) -> bool:
        """记录收款"""
        receivable = await self.get_by_id(id)
        if not receivable:
            return False

        record = record_data.model_dump()
        record["payment_date"] = datetime.now()

        paid_amount = receivable.get("paid_amount", 0) + record["amount"]
        total_amount = receivable.get("total_amount", 0)

        if paid_amount >= total_amount:
            status = ReceivableStatus.PAID.value
        elif paid_amount > 0:
            status = ReceivableStatus.PARTIAL.value
        else:
            status = ReceivableStatus.UNPAID.value

        return await self.update(id, {
            "paid_amount": paid_amount,
            "status": status,
            "$push": {"records": record}
        })

    async def update_receivable(
        self,
        id: str,
        receivable_data: ReceivableUpdate
    ) -> bool:
        """更新应收单"""
        data = receivable_data.model_dump(exclude_unset=True)
        return await self.update(id, data)

    async def get_by_sales_order_id(
        self,
        sales_order_id: str
    ) -> Optional[Dict[str, Any]]:
        """根据销售订单ID获取应收单"""
        return await self.find_one({"sales_order_id": sales_order_id})

    async def list_receivables(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询应收单列表"""
        filters = {}

        if status:
            filters["status"] = status
        if customer_id:
            filters["customer_id"] = customer_id
        if keyword:
            filters["$or"] = [
                {"receivable_no": {"$regex": keyword, "$options": "i"}},
                {"customer_name": {"$regex": keyword, "$options": "i"}}
            ]

        return await self.list(page, page_size, filters, "created_at", -1)

    async def update_status(
        self,
        id: str,
        status: ReceivableStatus
    ) -> bool:
        """更新应收单状态"""
        return await self.update(id, {"status": status.value})


accounts_receivable_service = AccountsReceivableService()
