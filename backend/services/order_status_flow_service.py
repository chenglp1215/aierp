"""
订单状态流转记录服务
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from bson import ObjectId

from .base_service import BaseService

logger = logging.getLogger(__name__)


class OrderStatusFlowService(BaseService):
    """订单状态流转记录服务"""

    def __init__(self):
        super().__init__("order_status_flows")

    async def create_flow_record(
        self,
        order_no: str,
        field: str,
        old_value: Optional[str],
        new_value: str,
        operator: str = "system",
        remark: Optional[str] = None
    ) -> str:
        """创建流转记录"""
        data = {
            "order_no": order_no,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "operator": operator,
            "operate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "remark": remark
        }
        record_id = await self.create(data)
        return record_id

    async def get_flows_by_order_no(self, order_no: str) -> List[Dict[str, Any]]:
        """根据订单号获取流转记录（按时间正序）"""
        cursor = self.collection.find({"order_no": order_no}).sort("operate_time", 1)
        records = await cursor.to_list(length=None)
        for record in records:
            record["id"] = str(record.pop("_id"))
        return records

    async def get_flows_by_order_no_paged(
        self,
        order_no: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """根据订单号分页获取流转记录"""
        filters = {"order_no": order_no}
        skip = (page - 1) * page_size
        total = await self.collection.count_documents(filters)
        cursor = self.collection.find(filters).sort("operate_time", 1).skip(skip).limit(page_size)
        records = await cursor.to_list(length=page_size)
        for record in records:
            record["id"] = str(record.pop("_id"))
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": records
        }

    async def delete_flows_by_order_no(self, order_no: str) -> int:
        """删除指定订单的所有流转记录"""
        result = await self.collection.delete_many({"order_no": order_no})
        return result.deleted_count


order_status_flow_service = OrderStatusFlowService()
