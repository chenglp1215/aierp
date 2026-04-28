from typing import Optional, Dict, Any, List
import random
import string
import logging

from .base_service import BaseService
from models.inventory import (
    WarehouseCreate, WarehouseUpdate, WarehouseStatus,
    StockCreate, StockUpdate, StockStatus
)
from validators.customer_validator import (
    WAREHOUSE_CREATE_CONFIG,
    WAREHOUSE_UPDATE_CONFIG,
    STOCK_CREATE_CONFIG,
    STOCK_UPDATE_CONFIG,
)

logger = logging.getLogger(__name__)

class WarehouseService(BaseService):
    def __init__(self):
        super().__init__("warehouses")
        self.logger = logging.getLogger(__name__)

    def _generate_warehouse_code(self) -> str:
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"WH{date_str}{random_str}"

    def validate_warehouse_create(self, warehouse_data: WarehouseCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(warehouse_data.model_dump(), WAREHOUSE_CREATE_CONFIG)

    def validate_warehouse_update(self, warehouse_data: WarehouseUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(warehouse_data.model_dump(exclude_unset=True), WAREHOUSE_UPDATE_CONFIG)

    async def create_warehouse(self, warehouse_data: WarehouseCreate) -> Dict[str, Any]:
        data = warehouse_data.model_dump()
        if not data.get("warehouse_code"):
            data["warehouse_code"] = self._generate_warehouse_code()
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
            print(f"[DEBUG] Updating warehouse: filter={filter_query}, data={data}")
            result = await self.collection.update_one(
                filter_query,
                {"$set": data}
            )
            print(f"[DEBUG] Update result: matched={result.matched_count}, modified={result.modified_count}")
            return result.matched_count > 0
        except Exception as e:
            print(f"[ERROR] Update warehouse failed: {e}")
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


async def _enrich_stock_items(items: list, db) -> list:
    from bson import ObjectId

    if not items:
        return items

    product_ids = [ObjectId(item["product_id"]) for item in items if item.get("product_id")]
    warehouse_ids = [ObjectId(item["warehouse_id"]) for item in items if item.get("warehouse_id")]

    product_map = {}
    if product_ids:
        products = await db["products"].find({"_id": {"$in": product_ids}}).to_list(length=None)
        for p in products:
            product_map[str(p["_id"])] = {"code": p.get("product_code", ""), "name": p.get("name", "")}

    warehouse_map = {}
    if warehouse_ids:
        warehouses = await db["warehouses"].find({"_id": {"$in": warehouse_ids}}).to_list(length=None)
        for w in warehouses:
            warehouse_map[str(w["_id"])] = {"code": w.get("warehouse_code", ""), "name": w.get("name", "")}

    for item in items:
        if item.get("product_id"):
            item["product_id"] = str(item["product_id"])
        if item.get("warehouse_id"):
            item["warehouse_id"] = str(item["warehouse_id"])

        product_id = item.get("product_id")
        if product_id and product_id in product_map:
            item["product_code"] = product_map[product_id]["code"]
            item["product_name"] = product_map[product_id]["name"]
        else:
            item["product_code"] = ""
            item["product_name"] = ""

        warehouse_id = item.get("warehouse_id")
        if warehouse_id and warehouse_id in warehouse_map:
            item["warehouse_code"] = warehouse_map[warehouse_id]["code"]
            item["warehouse_name"] = warehouse_map[warehouse_id]["name"]
        else:
            item["warehouse_code"] = ""
            item["warehouse_name"] = ""

    return items


class StockService(BaseService):
    def __init__(self):
        super().__init__("stocks")

    def validate_stock_create(self, stock_data: StockCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(stock_data.model_dump(), STOCK_CREATE_CONFIG)

    def validate_stock_update(self, stock_data: StockUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(stock_data.model_dump(exclude_unset=True), STOCK_UPDATE_CONFIG)

    async def create_stock(self, stock_data: StockCreate) -> Dict[str, Any]:
        data = stock_data.model_dump()
        data["status"] = StockStatus.NORMAL.value
        _id = await self.create(data)
        data["id"] = _id
        return data

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
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if warehouse_id:
            filters["warehouse_id"] = warehouse_id
        if product_id:
            filters["product_id"] = product_id
        if status:
            filters["status"] = status
        if keyword:
            product_cursor = self.db["products"].find({
                "$or": [
                    {"name": {"$regex": keyword, "$options": "i"}},
                    {"product_code": {"$regex": keyword, "$options": "i"}}
                ]
            })
            matched_products = await product_cursor.to_list(length=None)
            matched_product_ids = [str(p["_id"]) for p in matched_products]
            if matched_product_ids:
                filters["product_id"] = {"$in": matched_product_ids}
            else:
                filters["product_id"] = "___no_match___"

        result = await self.list(page, page_size, filters, "created_at", -1)
        result["items"] = await _enrich_stock_items(result.get("items", []), self.db)
        return result

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

    async def adjust_stock_by_id(
        self,
        id: str,
        quantity_change: float,
        is_add: bool = True
    ) -> Optional[Dict[str, Any]]:
        stock = await self.get_by_id(id)
        if not stock:
            return None
        new_quantity = stock["quantity"] + quantity_change if is_add else stock["quantity"] - quantity_change
        if new_quantity < 0:
            new_quantity = 0
        await self.update_quantity(id, new_quantity)
        return await self.get_stock_by_id(id)

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
                {"product_id": {"$regex": keyword, "$options": "i"}},
                {"warehouse_id": {"$regex": keyword, "$options": "i"}}
            ]
        }
        cursor = self.collection.find(filters).limit(limit)
        items = await cursor.to_list(length=limit)
        return _enrich_stock_items(items, self.db)


warehouse_service = WarehouseService()
stock_service = StockService()
