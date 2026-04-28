from typing import Optional, Dict, Any, List
from bson import ObjectId
import random
import string
import logging
from datetime import datetime

from .base_service import BaseService
from models.inventory import (
    WarehouseCreate, WarehouseUpdate, WarehouseStatus,
    StockCreate, StockUpdate, StockStatus,
    InboundBatchCreate, OutboundBatchCreate,
    InboundOutboundSummary
)
from validators.customer_validator import (
    WAREHOUSE_CREATE_CONFIG,
    WAREHOUSE_UPDATE_CONFIG,
    STOCK_CREATE_CONFIG,
    STOCK_UPDATE_CONFIG,
)

logger = logging.getLogger(__name__)


def _generate_code(prefix: str) -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{date_str}{random_str}"


class WarehouseService(BaseService):
    def __init__(self):
        super().__init__("warehouses")
        self.logger = logging.getLogger(__name__)

    def validate_warehouse_create(self, warehouse_data: WarehouseCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(warehouse_data.model_dump(), WAREHOUSE_CREATE_CONFIG)

    def validate_warehouse_update(self, warehouse_data: WarehouseUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(warehouse_data.model_dump(exclude_unset=True), WAREHOUSE_UPDATE_CONFIG)

    async def create_warehouse(self, warehouse_data: WarehouseCreate) -> Dict[str, Any]:
        data = warehouse_data.model_dump()
        if not data.get("warehouse_code"):
            data["warehouse_code"] = _generate_code("WH")
        data["status"] = WarehouseStatus.ACTIVE.value
        data['id'] = await self.create(data)
        return data

    async def update_warehouse(self, warehouse_code: str, warehouse_data: WarehouseUpdate) -> bool:
        data = warehouse_data.model_dump(exclude_unset=True)
        data.pop("updated_at", None)
        data.pop("created_at", None)
        data.pop("id", None)
        for key, value in data.items():
            if hasattr(value, 'value'):
                data[key] = value.value
        try:
            filter_query = {"warehouse_code": warehouse_code}
            result = await self.collection.update_one(
                filter_query,
                {"$set": data}
            )
            return result.matched_count > 0
        except Exception as e:
            self.logger.error(f"Error updating warehouse: {e}")
            return False

    async def get_warehouse_by_code(self, warehouse_code: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"warehouse_code": warehouse_code})

    async def list_warehouses(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if status:
            filters["status"] = status
        if keyword:
            filters["$or"] = [
                {"warehouse_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
                {"manager_name": {"$regex": keyword, "$options": "i"}},
                {"manager_id": {"$regex": keyword, "$options": "i"}}
            ]
        return await self.list(page, page_size, filters, "created_at", -1)

    async def update_status(self, warehouse_code: str, status: WarehouseStatus) -> bool:
        return await self.update(warehouse_code, {"status": status.value})

    async def delete_warehouse(self, warehouse_code: str) -> bool:
        return await self.delete(warehouse_code)

    async def search_warehouses(self, keyword: str, limit: int = 10) -> list:
        filters = {
            "status": WarehouseStatus.ACTIVE.value,
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"warehouse_code": {"$regex": keyword, "$options": "i"}},
                {"manager_name": {"$regex": keyword, "$options": "i"}},
                {"manager_id": {"$regex": keyword, "$options": "i"}}
            ]
        }
        cursor = self.collection.find(filters).limit(limit)
        items = await cursor.to_list(length=limit)
        for item in items:
            item["id"] = str(item.pop("_id"))
        return items


class InboundBatchService(BaseService):
    def __init__(self):
        super().__init__("inbound_batches")
        self.logger = logging.getLogger(__name__)

    async def create_inbound_batch(
        self,
        inventory_id: str,
        batch_data: InboundBatchCreate,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> Dict[str, Any]:
        data = batch_data.model_dump()
        data["inventory_id"] = inventory_id
        data["operator_id"] = operator_id
        data["operator_name"] = operator_name
        data["batch_code"] = _generate_code("IN")
        data["id"] = await self.create(data)
        return data

    async def get_inbound_batches_by_inventory(
        self,
        inventory_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        filters = {"inventory_id": inventory_id}
        return await self.list(page, page_size, filters, "created_at", -1)

    async def get_inbound_summary_by_inventory(self, inventory_id: str) -> Dict[str, Any]:
        pipeline = [
            {"$match": {"inventory_id": inventory_id}},
            {"$group": {
                "_id": None,
                "total_inbound": {"$sum": "$quantity"},
                "inbound_count": {"$sum": 1}
            }}
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        if results:
            return {
                "total_inbound": results[0].get("total_inbound", 0),
                "inbound_count": results[0].get("inbound_count", 0)
            }
        return {"total_inbound": 0, "inbound_count": 0}


class OutboundBatchService(BaseService):
    def __init__(self):
        super().__init__("outbound_batches")
        self.logger = logging.getLogger(__name__)

    async def create_outbound_batch(
        self,
        inventory_id: str,
        batch_data: OutboundBatchCreate,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> Dict[str, Any]:
        data = batch_data.model_dump()
        data["inventory_id"] = inventory_id
        data["operator_id"] = operator_id
        data["operator_name"] = operator_name
        data["batch_code"] = _generate_code("OUT")
        data["id"] = await self.create(data)
        return data

    async def get_outbound_batches_by_inventory(
        self,
        inventory_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        filters = {"inventory_id": inventory_id}
        return await self.list(page, page_size, filters, "created_at", -1)

    async def get_outbound_summary_by_inventory(self, inventory_id: str) -> Dict[str, Any]:
        pipeline = [
            {"$match": {"inventory_id": inventory_id}},
            {"$group": {
                "_id": None,
                "total_outbound": {"$sum": "$quantity"},
                "outbound_count": {"$sum": 1}
            }}
        ]
        cursor = self.collection.aggregate(pipeline)
        results = await cursor.to_list(length=1)
        if results:
            return {
                "total_outbound": results[0].get("total_outbound", 0),
                "outbound_count": results[0].get("outbound_count", 0)
            }
        return {"total_outbound": 0, "outbound_count": 0}


async def _enrich_stock_items(items: list, db) -> list:
    if not items:
        return items

    spec_ids = [ObjectId(item["spec_id"]) for item in items if item.get("spec_id")]
    warehouse_ids = [ObjectId(item["warehouse_id"]) for item in items if item.get("warehouse_id")]

    spec_map = {}
    if spec_ids:
        specs = await db["product_specs"].find({"_id": {"$in": spec_ids}}).to_list(length=None)
        product_ids = [ObjectId(s.get("product_id")) for s in specs if s.get("product_id")]
        products = await db["products"].find({"_id": {"$in": product_ids}}).to_list(length=None)
        product_map = {str(p["_id"]): {"code": p.get("product_code", ""), "name": p.get("name", ""), "category": p.get("category", "")}
                      for p in products}

        for s in specs:
            product_id = str(s.get("product_id", ""))
            spec_map[str(s["_id"])] = {
                "spec_id": str(s["_id"]),
                "spec_code": s.get("spec_code", ""),
                "packaging": s.get("packaging", ""),
                "sales_spec": s.get("sales_spec", ""),
                "price": s.get("price", 0),
                "product_id": product_id,
                "product_code": product_map.get(product_id, {}).get("code", ""),
                "product_name": product_map.get(product_id, {}).get("name", ""),
                "category": product_map.get(product_id, {}).get("category", "")
            }

    warehouse_map = {}
    if warehouse_ids:
        logger.info(f"[Stock Enrich] Looking up {len(warehouse_ids)} warehouse IDs")
        warehouses = await db["warehouses"].find({"_id": {"$in": warehouse_ids}}).to_list(length=None)
        logger.info(f"[Stock Enrich] Found {len(warehouses)} warehouses")
        for w in warehouses:
            warehouse_map[str(w["_id"])] = {
                "warehouse_id": str(w["_id"]),
                "warehouse_code": w.get("warehouse_code", ""),
                "warehouse_name": w.get("name", "")
            }
        if len(warehouses) < len(warehouse_ids):
            found_ids = {str(w["_id"]) for w in warehouses}
            missing = [str(oid) for oid in warehouse_ids if str(oid) not in found_ids]
            logger.warning(f"[Stock Enrich] Missing warehouses: {missing}")

    for item in items:
        if item.get("spec_id"):
            item["spec_id"] = str(item["spec_id"])
        if item.get("warehouse_id"):
            item["warehouse_id"] = str(item["warehouse_id"])

        spec_id = item.get("spec_id")
        if spec_id and spec_id in spec_map:
            spec_info = spec_map[spec_id]
            item["spec"] = {
                "spec_id": spec_info["spec_id"],
                "spec_code": spec_info["spec_code"],
                "packaging": spec_info.get("packaging"),
                "sales_spec": spec_info.get("sales_spec"),
                "price": spec_info.get("price")
            }
            item["product"] = {
                "product_id": spec_info["product_id"],
                "product_code": spec_info["product_code"],
                "product_name": spec_info["product_name"],
                "category": spec_info.get("category")
            }
        else:
            item["spec"] = None
            item["product"] = None

        warehouse_id = item.get("warehouse_id")
        if warehouse_id and warehouse_id in warehouse_map:
            item["warehouse"] = warehouse_map[warehouse_id]
        else:
            item["warehouse"] = None

    return items


class StockService(BaseService):
    def __init__(self):
        super().__init__("stocks")

    def validate_stock_create(self, stock_data: StockCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(stock_data.model_dump(), STOCK_CREATE_CONFIG)

    def validate_stock_update(self, stock_data: StockUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(stock_data.model_dump(exclude_unset=True), STOCK_UPDATE_CONFIG)

    async def create_stock(self, stock_data: StockCreate) -> Dict[str, Any]:
        existing = await self.find_one({
            "warehouse_id": stock_data.warehouse_id,
            "spec_id": stock_data.spec_id
        })
        if existing:
            raise ValueError(f"DUPLICATE_STOCK:{existing['id']}")
        data = stock_data.model_dump()
        data["status"] = StockStatus.NORMAL.value
        _id = await self.create(data)
        data["id"] = _id
        return data

    async def find_stock_by_warehouse_and_spec(self, warehouse_id: str, spec_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({
            "warehouse_id": warehouse_id,
            "spec_id": spec_id
        })

    async def update_stock(self, id: str, stock_data: StockUpdate) -> bool:
        data = stock_data.model_dump(exclude_unset=True)
        return await self.update(id, data)

    async def get_stock_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        item = await self.get_by_id(id)
        if item:
            items = await _enrich_stock_items([item], self.db)
            return items[0] if items else None
        return None

    async def list_stocks(
        self,
        page: int = 1,
        page_size: int = 20,
        warehouse_id: Optional[str] = None,
        product_id: Optional[str] = None,
        spec_id: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if warehouse_id:
            filters["warehouse_id"] = warehouse_id
        if status:
            filters["status"] = status

        if product_id:
            spec_ids = await self.db["product_specs"].distinct(
                "_id",
                {"product_id": product_id}
            )
            if spec_ids:
                filters["spec_id"] = {"$in": [str(sid) for sid in spec_ids]}
            else:
                filters["spec_id"] = {"$in": []}

        if spec_id:
            filters["spec_id"] = spec_id

        if keyword:
            filters["$or"] = [
                {"warehouse_id": {"$regex": keyword, "$options": "i"}}
            ]

        result = await self.list(page, page_size, filters, "created_at", -1)
        result["items"] = await _enrich_stock_items(result.get("items", []), self.db)
        return result

    async def inbound(
        self,
        stock_id: str,
        quantity: float,
        remarks: Optional[str] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        stock = await self.get_by_id(stock_id)
        if not stock:
            return None

        batch_service = InboundBatchService()
        batch_data = InboundBatchCreate(quantity=quantity, remarks=remarks)
        await batch_service.create_inbound_batch(stock_id, batch_data, operator_id, operator_name)

        new_quantity = stock["quantity"] + quantity
        await self.update_quantity(stock_id, new_quantity)
        return await self.get_stock_by_id(stock_id)

    async def outbound(
        self,
        stock_id: str,
        quantity: float,
        remarks: Optional[str] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        stock = await self.get_by_id(stock_id)
        if not stock:
            return None

        if stock["quantity"] < quantity:
            raise ValueError("库存不足，无法出库")

        batch_service = OutboundBatchService()
        batch_data = OutboundBatchCreate(quantity=quantity, remarks=remarks)
        await batch_service.create_outbound_batch(stock_id, batch_data, operator_id, operator_name)

        new_quantity = stock["quantity"] - quantity
        await self.update_quantity(stock_id, new_quantity)
        return await self.get_stock_by_id(stock_id)

    async def update_quantity(self, id: str, quantity: float) -> bool:
        status = StockStatus.NORMAL.value
        stock = await self.get_by_id(id)
        if stock:
            min_stock = stock.get("min_stock", 0)
            max_stock = stock.get("max_stock", 0)
            if quantity <= 0:
                status = StockStatus.OUT_OF_STOCK.value
            elif min_stock > 0 and quantity < min_stock:
                status = StockStatus.LOW_STOCK.value
            elif max_stock > 0 and quantity > max_stock:
                status = StockStatus.OVERSTOCK.value
        return await self.update(id, {"quantity": quantity, "status": status})

    async def get_stock_detail(self, stock_id: str) -> Optional[Dict[str, Any]]:
        stock = await self.get_stock_by_id(stock_id)
        if not stock:
            return None

        inbound_service = InboundBatchService()
        outbound_service = OutboundBatchService()

        inbound_result = await inbound_service.get_inbound_batches_by_inventory(stock_id, 1, 100)
        outbound_result = await outbound_service.get_outbound_batches_by_inventory(stock_id, 1, 100)

        inbound_summary = await inbound_service.get_inbound_summary_by_inventory(stock_id)
        outbound_summary = await outbound_service.get_outbound_summary_by_inventory(stock_id)

        stock["inbound_outbound_summary"] = InboundOutboundSummary(
            total_inbound=inbound_summary.get("total_inbound", 0),
            total_outbound=outbound_summary.get("total_outbound", 0),
            inbound_count=inbound_summary.get("inbound_count", 0),
            outbound_count=outbound_summary.get("outbound_count", 0)
        )

        return {
            "stock": stock,
            "inbound_batches": inbound_result.get("items", []),
            "outbound_batches": outbound_result.get("items", [])
        }

    async def get_stock_stats(self) -> Dict[str, Any]:
        total = await self.count({})
        normal = await self.count({"status": StockStatus.NORMAL.value})
        low_stock = await self.count({"status": StockStatus.LOW_STOCK.value})
        out_of_stock = await self.count({"status": StockStatus.OUT_OF_STOCK.value})
        overstock = await self.count({"status": StockStatus.OVERSTOCK.value})
        return {
            "total": total,
            "normal": normal,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "overstock": overstock
        }

    async def search_stocks(self, keyword: str, limit: int = 10) -> list:
        filters = {
            "$or": [
                {"spec_id": {"$regex": keyword, "$options": "i"}},
                {"warehouse_id": {"$regex": keyword, "$options": "i"}}
            ]
        }
        cursor = self.collection.find(filters).limit(limit)
        items = await cursor.to_list(length=limit)
        return await _enrich_stock_items(items, self.db)


warehouse_service = WarehouseService()
stock_service = StockService()
inbound_batch_service = InboundBatchService()
outbound_batch_service = OutboundBatchService()
