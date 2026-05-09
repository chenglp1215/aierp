from typing import Optional, Dict, Any, List
from bson import ObjectId
import random
import string
import logging
from datetime import datetime

from .base_service import BaseService
from models.inventory import ( WarehouseStatus, Stock, Warehouse, InboundBatch, OutboundBatch)
from validators.inventory_validator import (
    WAREHOUSE_CREATE_CONFIG,
    WAREHOUSE_UPDATE_CONFIG,
    STOCK_CREATE_CONFIG,
    STOCK_UPDATE_CONFIG,
    INBOUND_BATCH_CREATE_CONFIG,
    INBOUND_BATCH_UPDATE_CONFIG,
    OUTBOUND_BATCH_CREATE_CONFIG,
    OUTBOUND_BATCH_UPDATE_CONFIG,
)

logger = logging.getLogger(__name__)


def _generate_code(prefix: str) -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{date_str}{random_str}"


class WarehouseService(BaseService):
    def __init__(self):
        super().__init__("inventory_warehouses")
        self.logger = logging.getLogger(__name__)
        self.models = Warehouse

    def validate_warehouse_create(self, warehouse_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(warehouse_data, WAREHOUSE_CREATE_CONFIG)

    def validate_warehouse_update(self, warehouse_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(warehouse_data, WAREHOUSE_UPDATE_CONFIG)

    def format(self, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        return warehouse_data   

    def format_list(self, warehouse_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.format(warehouse) for warehouse in warehouse_list]

    async def create_warehouse(self, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        is_valid, errors = self.validate_warehouse_create(warehouse_data)
        if not is_valid:
            raise ValueError(errors)
        if not warehouse_data.get("warehouse_code"):
            warehouse_data["warehouse_code"] = _generate_code("WH")
        if not warehouse_data.get("status"):
            warehouse_data["status"] = WarehouseStatus.ACTIVE.value
        warehouse_data['id'] = await self.create(warehouse_data)
        if "_id" in warehouse_data:
            warehouse_data.pop("_id")
        return warehouse_data

    async def update_warehouse(self, warehouse_id: str, warehouse_data: Dict[str, Any]) -> bool:
        is_valid, errors = self.validate_warehouse_update(warehouse_data)
        if not is_valid:
            raise ValueError(errors)
        warehouse_data.pop("updated_at", None)
        warehouse_data.pop("created_at", None)
        warehouse_data.pop("warehouse_code", None)
        warehouse_data.pop("id", None)
        warehouse = await self.get_by_id(warehouse_id)
        if not warehouse:
            raise ValueError("仓库不存在")
        return await self.update(warehouse_id, warehouse_data)

    async def get_warehouse_by_code(self, warehouse_code: str, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        warehouse = await self.find_one({"warehouse_code": warehouse_code})
        if is_formatted:
            return self.format(warehouse)
        return warehouse

    async def get_warehouse_by_id(self, warehouse_id: str, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        warehouse = await self.get_by_id(warehouse_id)
        if is_formatted:
            return self.format(warehouse)
        return warehouse
    
    async def get_warehouse_by_ids(self, warehouse_ids: List[str], is_formatted: bool = False) -> List[Dict[str, Any]]:
        warehouse_list = await self.find_many({"_id": {"$in": [ObjectId(id) for id in warehouse_ids]}})
        if is_formatted:
            return self.format_list(warehouse_list)
        return warehouse_list

    async def list_warehouses(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        is_formatted: bool = True
    ) -> tuple[List[Dict[str, Any]], int]:
        filters = self._build_warehouse_filters(status, keyword)
        warehouse_list = await self.find_many(filters, limit=page_size, skip=(page - 1) * page_size)
        total = await self.count(filters)
        if is_formatted:
            warehouse_list = self.format_list(warehouse_list)
        return warehouse_list, total

    def _build_warehouse_filters(self, status: Optional[str], keyword: Optional[str]) -> dict:
        filters = {}
        if status:
            filters["status"] = status
        if keyword:
            filters["$or"] = [
                {"warehouse_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
            ]
        return filters


class StockService(BaseService):
    def __init__(self):
        super().__init__("inventory_stocks")
        self.logger = logging.getLogger(__name__)
        self.models = Stock

    async def format(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化库存数据
        """
        from .product_service import product_service, product_spec_service
        stock_data['product_info'] = await self._safe_get_product(stock_data.get('product_id'))
        stock_data['spec_info'] = await self._safe_get_spec(stock_data.get('spec_id'))
        stock_data['warehouse_info'] = await self._safe_get_warehouse(stock_data.get('warehouse_id'))
        return stock_data   

    async def _safe_get_product(self, product_id: Optional[str]) -> Dict[str, Any]:
        from .product_service import product_service
        try:
            return await product_service.get_product_by_id(product_id, is_formatted=False) or {}
        except Exception:
            return {}

    async def _safe_get_spec(self, spec_id: Optional[str]) -> Dict[str, Any]:
        from .product_service import product_spec_service
        try:
            return await product_spec_service.get_spec_by_id(spec_id, is_formatted=False) or {}
        except Exception:
            return {}

    async def _safe_get_warehouse(self, warehouse_id: Optional[str]) -> Dict[str, Any]:
        try:
            return await warehouse_service.get_warehouse_by_id(warehouse_id, is_formatted=False) or {}
        except Exception:
            return {}

    async def get_stock_status_by_spec_ids(self, spec_ids: List[str]) -> Dict[str, Any]:
        """
        获取库存状态, 查询指定spec_id的规格的库存状态， 返回各个仓库的库存状态
        返回格式:
        {
            "spec_id": [
                {
                    "warehouse_id": "xxx",
                    "warehouse_name": "仓库名",
                    "quantity": 100
                }
            ]
        }
        """
        if not spec_ids:
            return {}
        stocks = await self.find_many({"spec_id": {"$in": spec_ids}})
        result: Dict[str, List[Dict[str, Any]]] = {}
        for stock in stocks:
            spec_id = stock.get('spec_id')
            warehouse_id = stock.get('warehouse_id')
            warehouse_name = stock.get('warehouse_name')
            if not spec_id:
                continue
            if spec_id not in result:
                result[spec_id] = []
            result[spec_id].append({
                "warehouse_id": warehouse_id or "",
                "warehouse_name": warehouse_name or "",
                "quantity": stock.get('quantity', 0)
            })
        return result

    async def format_list(self, stock_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化库存列表
        """
        product_info = await self._batch_fetch_products(stock_list)
        spec_info = await self._batch_fetch_specs(stock_list)
        warehouse_info = await self._batch_fetch_warehouses(stock_list)
        for stock in stock_list:
            stock['product_info'] = product_info.get(stock['product_id'], {})
            stock['spec_info'] = spec_info.get(stock['spec_id'], {})
            stock['warehouse_info'] = warehouse_info.get(stock['warehouse_id'], {})
        return stock_list

    async def _batch_fetch_products(self, stock_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        from .product_service import product_service
        product_ids = list(set([stock['product_id'] for stock in stock_list if stock.get('product_id')]))
        if not product_ids:
            return {}
        try:
            products = await product_service.get_product_by_ids(product_ids, is_formatted=False)
            return {p['id']: p for p in products}
        except Exception:
            return {}

    async def _batch_fetch_specs(self, stock_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        from .product_service import product_spec_service
        spec_ids = list(set([stock['spec_id'] for stock in stock_list if stock.get('spec_id')]))
        if not spec_ids:
            return {}
        try:
            specs = await product_spec_service.get_spec_by_ids(spec_ids, is_formatted=False)
            return {s['id']: s for s in specs}
        except Exception:
            return {}

    async def _batch_fetch_warehouses(self, stock_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        warehouse_ids = list(set([stock['warehouse_id'] for stock in stock_list if stock.get('warehouse_id')]))
        if not warehouse_ids:
            return {}
        try:
            warehouses = await warehouse_service.get_warehouse_by_ids(warehouse_ids, is_formatted=False)
            return {w['id']: w for w in warehouses}
        except Exception:
            return {}

    def validate_stock_create(self, stock_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(stock_data, STOCK_CREATE_CONFIG)

    def validate_stock_update(self, stock_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(stock_data, STOCK_UPDATE_CONFIG)

    async def create_stock(self, stock_data: Dict[str, Any]) -> str:
        """
        创建库存
        """
        is_valid, errors = self.validate_stock_create(stock_data)
        if not is_valid:
            raise ValueError(errors)
        return await self.create(stock_data)

    async def update_stock(self, id: str, stock_data: Dict[str, Any]) -> bool:
        """
        手动盘库，支持只能更新
        quantity:
        min_stock:
        max_stock: 
        """
        # 过滤出可更新的字段
        stock_data = {k: v for k, v in stock_data.items() if k in  ["quantity", "min_stock", "max_stock"]}
        is_valid, errors = self.validate_stock_update(stock_data)
        if not is_valid:
            raise ValueError(errors)
        stock = await self.get_by_id(id)
        if not stock:
            raise ValueError("库存不存在")
        return await self.update(id, stock_data)

    async def get_stock_by_id(self, id: str, is_formatted: bool = True) -> Optional[Dict[str, Any]]:
        item = await self.get_by_id(id)
        if not item:
            return None
        if is_formatted:
            return await self.format(item)
        return item

    async def get_or_create_stock_by_inbound(self, inbound: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        product_id = inbound["product_id"]
        spec_id = inbound["spec_id"]
        warehouse_id = inbound["warehouse_id"]
        stock = await self.find_one({"product_id": product_id, "spec_id": spec_id, "warehouse_id": warehouse_id})
        if not stock:
            stock_data = {
                "product_code": inbound["product_code"],
                "product_name": inbound["product_name"],
                "spec_code": inbound["spec_code"],
                "product_id": product_id,
                "spec_id": spec_id,
                "warehouse_id": warehouse_id,
                "quantity": inbound["quantity"],
                "min_stock": 0,
                "max_stock": 0,
                "status": "normal",
            }
            stock_id = await self.create_stock(stock_data)
            stock_data['id'] = stock_id
            stock_data['_id'] = stock_id
            return stock_data, False
        stock_data = await self.format(stock)
        return stock_data, True

    async def list_stocks(
        self,
        page: int = 1,
        page_size: int = 20,
        warehouse_id: Optional[str] = None,
        product_id: Optional[str] = None,
        spec_id: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        is_formatted: bool = True
    ) -> tuple[List[Dict[str, Any]], int]:
        filters = {}
        if warehouse_id:
            filters["warehouse_id"] = warehouse_id
        if status:
            filters["status"] = status

        if product_id:
            filters["product_id"] = product_id
        if spec_id:
            filters["spec_id"] = spec_id
        if keyword:
            filters["$or"] = [
                {"product_code": {"$regex": keyword, "$options": "i"}},
                {"product_name": {"$regex": keyword, "$options": "i"}},
                {"spec_code": {"$regex": keyword, "$options": "i"}}
            ]
        result = await self.find_many(filters, limit=page_size, skip=(page - 1) * page_size, sort={"created_at": -1})
        total = await self.count(filters)
        if is_formatted:
            result = await self.format_list(result)
        return result, total

class InboundBatchService(BaseService):
    def __init__(self):
        super().__init__("inventory_inbound_batches")
        self.logger = logging.getLogger(__name__)
        self.models = InboundBatch

    def validate_inbound_create(self, inbound: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(inbound, INBOUND_BATCH_CREATE_CONFIG)

    def validate_inbound_update(self, inbound: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(inbound, INBOUND_BATCH_UPDATE_CONFIG)

    async def format(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return item

    async def format_list(self, item_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [await self.format(item) for item in item_list]

    async def create_inbound(self, item: Dict[str, Any]) -> Dict[str, Any]:
        is_valid, errors = self.validate_inbound_create(item)
        if not is_valid:
            raise ValueError(errors)
        stock, is_existing = await stock_service.get_or_create_stock_by_inbound(item)
        item["stock_id"] = stock["id"]
        if is_existing:
            await self._add_stock_quantity(stock, item["quantity"])
        item["id"] = await self.create(item)
        item.pop("_id", None)
        return item

    async def _add_stock_quantity(self, stock: Dict[str, Any], quantity: int) -> None:
        await stock_service.collection.update_one(
            {"_id": ObjectId(stock["id"])},
            {"$inc": {"quantity": quantity}}
        )

    async def update_inbound(self, id: str, item: Dict[str, Any]) -> bool:
        is_valid, errors = self.validate_inbound_update(item)
        if not is_valid:
            raise ValueError(errors)
        return await self.update(id, item)

    async def get_inbounds_by_stock_id(self, stock_id: str, page: int = 1, page_size: int = 20, is_formatted: bool = True) -> tuple[List[Dict[str, Any]], int]:
        query = self._build_batch_query(stock_id)
        item_list = await self.find_many(
            query, 
            limit=page_size, 
            skip=(page - 1) * page_size, 
            sort={"created_at": -1}
        )
        total = await self.count(query)
        if is_formatted:
            item_list = await self.format_list(item_list)
        return item_list, total

    @staticmethod
    def _build_batch_query(stock_id: Optional[str]) -> dict:
        query = {}
        if stock_id:
            query["stock_id"] = stock_id
        return query


class OutboundBatchService(BaseService):
    def __init__(self):
        super().__init__("inventory_outbound_batches")
        self.logger = logging.getLogger(__name__)
        self.models = OutboundBatch

    def validate_outbound_create(self, outbound: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(outbound, OUTBOUND_BATCH_CREATE_CONFIG)

    def validate_outbound_update(self, outbound: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(outbound, OUTBOUND_BATCH_UPDATE_CONFIG)

    async def format(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return item

    async def format_list(self, item_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [await self.format(item) for item in item_list]

    async def create_outbound(self, item: Dict[str, Any]) -> Dict[str, Any]:
        is_valid, errors = self.validate_outbound_create(item)
        if not is_valid:
            raise ValueError(errors)
        stock = await stock_service.get_stock_by_id(item["stock_id"], is_formatted=False)
        if not stock:
            raise ValueError(f"库存记录不存在: {item['stock_id']}")
        await self._deduct_stock_quantity(stock, item["quantity"])
        item["id"] = await self.create(item)
        item.pop("_id", None)
        return item

    async def _deduct_stock_quantity(self, stock: Dict[str, Any], quantity: int) -> None:
        if stock["quantity"] < quantity:
            raise ValueError(
                f"库存不足，当前库存: {stock['quantity']}，出库数量: {quantity}"
            )
        stock_id = stock.get("id")
        if not stock_id:
            raise ValueError("库存记录缺少标识")
        await stock_service.collection.update_one(
            {"_id": ObjectId(stock_id) if isinstance(stock_id, str) else stock_id},
            {"$inc": {"quantity": -quantity}}
        )

    async def update_outbound(self, id: str, item: Dict[str, Any]) -> bool:
        is_valid, errors = self.validate_outbound_update(item)
        if not is_valid:
            raise ValueError(errors)
        return await self.update(id, item)
    
    async def get_outbounds_by_stock_id(self, stock_id: str, page: int = 1, page_size: int = 20, is_formatted: bool = True) -> tuple[List[Dict[str, Any]], int]:
        query = self._build_batch_query(stock_id)
        item_list = await self.find_many(
            query, 
            limit=page_size, 
            skip=(page - 1) * page_size, 
            sort={"created_at": -1}
        )
        total = await self.count(query)
        if is_formatted:
            item_list = await self.format_list(item_list)
        return item_list, total

    @staticmethod
    def _build_batch_query(stock_id: Optional[str]) -> dict:
        query = {}
        if stock_id:
            query["stock_id"] = stock_id
        return query


warehouse_service = WarehouseService()
stock_service = StockService()
inbound_batch_service = InboundBatchService()
outbound_batch_service = OutboundBatchService()
