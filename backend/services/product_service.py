from typing import Optional, Dict, Any, List
import random
import string
from bson import ObjectId
from datetime import datetime

from .base_service import BaseService
from models.product import ProductCreate, ProductUpdate, ProductSpecCreate, ProductSpecUpdate
from validators.customer_validator import (
    PRODUCT_CREATE_CONFIG,
    PRODUCT_UPDATE_CONFIG,
    PRODUCT_SPEC_CREATE_CONFIG,
    PRODUCT_SPEC_UPDATE_CONFIG,
)


class ProductSpecService(BaseService):
    def __init__(self):
        super().__init__("product_specs")

    def _generate_spec_code(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"SPEC{date_str}{random_str}"

    def validate_spec_create(self, spec_data: ProductSpecCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(spec_data.model_dump(), PRODUCT_SPEC_CREATE_CONFIG)

    def validate_spec_update(self, spec_data: ProductSpecUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(spec_data.model_dump(exclude_unset=True), PRODUCT_SPEC_UPDATE_CONFIG)

    async def create_spec(self, spec_data: ProductSpecCreate) -> Dict[str, Any]:
        data = spec_data.model_dump()
        if not data.get("spec_code"):
            data["spec_code"] = self._generate_spec_code()
        data["id"] = await self.create(data)
        return data

    async def update_spec(self, id: str, spec_data: ProductSpecUpdate) -> bool:
        data = spec_data.model_dump(exclude_unset=True)
        return await self.update(id, data)

    async def get_spec_by_code(self, spec_code: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"spec_code": spec_code})

    async def list_specs(
        self,
        page: int = 1,
        page_size: int = 20,
        product_id: Optional[str] = None,
        keyword: Optional[str] = None,
        product_keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if product_id:
            filters["product_id"] = product_id
        if keyword:
            filters["spec_code"] = {"$regex": keyword, "$options": "i"}
        if product_keyword:
            product = await self.db["products"].find_one({"product_code": {"$regex": product_keyword, "$options": "i"}})
            if product:
                filters["product_id"] = str(product["_id"])

        result = await self.list(page, page_size, filters, "created_at", -1)
        result["items"] = await self._enrich_stock_status(result.get("items", []))
        return result

    async def _enrich_stock_status(self, items: List[Dict]) -> List[Dict]:
        if not items:
            return items

        spec_ids = [item["id"] for item in items if item.get("id")]

        pipeline = [
            {"$match": {"spec_id": {"$in": spec_ids}}},
            {"$group": {
                "_id": "$spec_id",
                "total_quantity": {"$sum": "$quantity"},
                "min_status": {"$min": "$status"}
            }}
        ]

        cursor = self.db["stocks"].aggregate(pipeline)
        stock_data = await cursor.to_list(length=None)
        stock_map = {s["_id"]: s for s in stock_data}

        for item in items:
            sid = item.get("id")
            stock_info = stock_map.get(sid)
            if stock_info:
                item["stock_quantity"] = stock_info["total_quantity"]
                item["stock_status"] = stock_info["min_status"]
            else:
                item["stock_quantity"] = 0
                item["stock_status"] = "out_of_stock"

        return items

    async def get_specs_by_product_id(self, product_id: str) -> List[Dict[str, Any]]:
        items = await self.find_many({"product_id": product_id})
        return await self._enrich_stock_status(items)

    async def delete_spec(self, id: str) -> bool:
        return await self.delete(id)

    async def toggle_spec_active(self, id: str, is_active: bool) -> bool:
        return await self.update(id, {"is_active": is_active})


class ProductService(BaseService):
    def __init__(self):
        super().__init__("products")
        self.spec_service = ProductSpecService()

    def _generate_product_code(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"PROD{date_str}{random_str}"

    def validate_product_create(self, product_data: ProductCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(product_data.model_dump(), PRODUCT_CREATE_CONFIG)

    def validate_product_update(self, product_data: ProductUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(product_data.model_dump(exclude_unset=True), PRODUCT_UPDATE_CONFIG)

    async def create_product(self, product_data: ProductCreate) -> Dict[str, Any]:
        data = product_data.model_dump()
        if not data.get("product_code"):
            data["product_code"] = self._generate_product_code()
        data["id"] = await self.create(data)
        return data

    async def update_product(self, id: str, product_data: ProductUpdate) -> bool:
        data = product_data.model_dump(exclude_unset=True)
        return await self.update(id, data)

    async def get_product_by_code(self, product_code: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"product_code": product_code})

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if keyword:
            filters["$or"] = [
                {"product_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ]

        result = await self.list(page, page_size, filters, "created_at", -1)
        items = result.get("items", [])

        for item in items:
            specs = await self.spec_service.get_specs_by_product_id(item["id"])
            item["specs"] = specs

        result["items"] = items
        return result

    async def get_product_with_specs(self, product_id: str) -> Optional[Dict[str, Any]]:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        specs = await self.spec_service.get_specs_by_product_id(product_id)
        product["specs"] = specs
        return product

    async def get_product_stats(self) -> Dict[str, Any]:
        total = await self.count({})

        cursor = self.db["stocks"].aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$quantity"}}}
        ])
        stock_data = await cursor.to_list(length=None)
        total_stock = stock_data[0]["total"] if stock_data else 0

        spec_total = await self.spec_service.count({})

        return {"total": total, "total_stock": total_stock, "total_specs": spec_total}

    async def get_product_stock_detail(self, spec_id: str) -> Dict[str, Any]:
        pipeline = [
            {"$match": {"spec_id": spec_id}},
            {"$lookup": {
                "from": "warehouses",
                "localField": "warehouse_id",
                "foreignField": "_id",
                "as": "warehouse_info"
            }},
            {"$unwind": {
                "path": "$warehouse_info",
                "preserveNullAndEmptyArrays": True
            }},
            {"$project": {
                "id": {"$toString": "$_id"},
                "spec_id": 1,
                "warehouse_id": {"$toString": "$warehouse_id"},
                "warehouse_code": "$warehouse_info.warehouse_code",
                "warehouse_name": "$warehouse_info.name",
                "quantity": 1,
                "min_stock": 1,
                "max_stock": 1,
                "status": 1
            }}
        ]
        cursor = self.db["stocks"].aggregate(pipeline)
        items = await cursor.to_list(length=None)
        for item in items:
            for key, value in item.items():
                if isinstance(value, ObjectId):
                    item[key] = str(value)
        return items

    async def search_products(self, keyword: str, limit: int = 10) -> list:
        filters = {
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"product_code": {"$regex": keyword, "$options": "i"}}
            ]
        }

        cursor = self.collection.find(filters).limit(limit)
        items = await cursor.to_list(length=limit)

        for item in items:
            item["id"] = str(item.pop("_id"))
            specs = await self.spec_service.get_specs_by_product_id(item["id"])
            item["specs"] = specs

        return items


product_service = ProductService()
product_spec_service = ProductSpecService()
