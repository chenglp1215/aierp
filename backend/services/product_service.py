from typing import Optional, Dict, Any, List
import random
import string
import logging
from bson import ObjectId
from datetime import datetime

from .base_service import BaseService
from models.product import ProductCreate, ProductUpdate, ProductSpecCreate, ProductSpecUpdate
from services.category_service import category_service
from services.brand_service import brand_service
from validators.customer_validator import (
    PRODUCT_CREATE_CONFIG,
    PRODUCT_UPDATE_CONFIG,
    PRODUCT_SPEC_CREATE_CONFIG,
    PRODUCT_SPEC_UPDATE_CONFIG,
)

logger = logging.getLogger(__name__)


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
        if "_id" in data:
            data.pop("_id")
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

    async def _batch_get_stock_info(self, spec_ids: List[str]) -> Dict[str, Dict]:
        if not spec_ids:
            return {}

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
        return {s["_id"]: s for s in stock_data}

    async def get_specs_by_product_id(self, product_id: str) -> List[Dict[str, Any]]:
        items = await self.find_many({"product_id": product_id})
        return await self._enrich_stock_status(items)

    async def delete_spec(self, id: str) -> bool:
        return await self.delete(id)

    async def toggle_spec_active(self, id: str, is_active: bool) -> bool:
        return await self.update(id, {"is_active": is_active})

    async def search_specs(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索规格，支持规格编码、包装、商品名称、商品编码模糊匹配"""
        spec_cursor = self.collection.find({
            "$or": [
                {"spec_code": {"$regex": keyword, "$options": "i"}},
                {"packaging": {"$regex": keyword, "$options": "i"}}
            ]
        }).limit(limit)
        specs = await spec_cursor.to_list(length=limit)

        product_cursor = self.db["products"].find({
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"product_code": {"$regex": keyword, "$options": "i"}}
            ]
        }).limit(limit)
        products = await product_cursor.to_list(length=limit)

        if not products:
            # 规格直接匹配但无商品匹配，需补充商品信息
            missing_product_ids = set()
            for spec in specs:
                pid = spec.get("product_id")
                if pid:
                    missing_product_ids.add(pid)
            product_map = {}
            if missing_product_ids:
                cursor = self.db["products"].find({"_id": {"$in": [ObjectId(pid) for pid in missing_product_ids]}})
                for p in await cursor.to_list(length=len(missing_product_ids)):
                    product_map[str(p["_id"])] = p
            for spec in specs:
                spec["id"] = str(spec.pop("_id"))
                pid = spec.get("product_id")
                if pid and pid in product_map:
                    spec["product_name"] = product_map[pid].get("name", "")
                    spec["product_code"] = product_map[pid].get("product_code", "")
                    spec["brand_name"] = product_map[pid].get("brand_name", "")
                else:
                    spec["product_name"] = ""
                    spec["product_code"] = ""
                    spec["brand_name"] = ""
            return specs

        product_ids = [str(p["_id"]) for p in products]
        product_map = {str(p["_id"]): p for p in products}

        product_spec_cursor = self.collection.find({
            "product_id": {"$in": product_ids}
        }).limit(limit)
        product_specs = await product_spec_cursor.to_list(length=limit)

        all_specs = specs.copy()
        spec_ids = set(str(s.get("_id")) for s in all_specs)
        for spec in product_specs:
            sid = str(spec["_id"])
            if sid not in spec_ids:
                all_specs.append(spec)
                spec_ids.add(sid)

        # 补充未在 product_map 中的商品信息
        missing_product_ids = set()
        for spec in all_specs:
            pid = spec.get("product_id")
            if pid and pid not in product_map:
                missing_product_ids.add(pid)
        if missing_product_ids:
            cursor = self.db["products"].find({"_id": {"$in": [ObjectId(pid) for pid in missing_product_ids]}})
            for p in await cursor.to_list(length=len(missing_product_ids)):
                product_map[str(p["_id"])] = p

        for spec in all_specs:
            spec["id"] = str(spec.pop("_id"))
            product_id = spec.get("product_id")
            if product_id and product_id in product_map:
                product = product_map[product_id]
                spec["product_name"] = product.get("name", "")
                spec["product_code"] = product.get("product_code", "")
                spec["brand_name"] = product.get("brand_name", "")
            else:
                spec["product_name"] = ""
                spec["product_code"] = ""
                spec["brand_name"] = ""

        return all_specs[:limit]


class ProductService(BaseService):
    def __init__(self):
        super().__init__("products")
        self.spec_service = ProductSpecService()
        self.category_service = category_service

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
        specs_data = data.pop("specs", []) or []
        if specs_data:
            spec_codes = [s.get("spec_code") for s in specs_data if s.get("spec_code")]
            if len(spec_codes) != len(set(spec_codes)):
                raise ValueError("同一商品下的规格编号不能重复")
        if not data.get("product_code"):
            data["product_code"] = self._generate_product_code()
        data["id"] = await self.create(data)
        created_specs = []
        for spec_data in specs_data:
            spec_data["product_id"] = data["id"]
            spec_create = ProductSpecCreate(**spec_data)
            spec = await self.spec_service.create_spec(spec_create)
            created_specs.append(spec)
        data["specs"] = created_specs
        if "_id" in data:
            data.pop("_id")
        return data

    async def update_product(self, id: str, product_data: ProductUpdate) -> bool:
        from pydantic import ValidationError
        data = product_data.model_dump(exclude_unset=True)
        specs_data = data.pop("specs", None)

        success = await self.update(id, data)
        if not success:
            return False

        if specs_data is not None:
            spec_codes = [s.get("spec_code") for s in specs_data if s.get("spec_code")]
            if len(spec_codes) != len(set(spec_codes)):
                raise ValueError("同一商品下的规格编号不能重复")

            logger.info(f"Updating specs for product {id}: specs_count={len(specs_data)}")
            try:
                existing_specs = await self.spec_service.get_specs_by_product_id(id)
                existing_spec_ids = {s["id"] for s in existing_specs}
                logger.info(f"Existing spec ids: {existing_spec_ids}")
                submitted_spec_ids = set()

                for spec_data in specs_data:
                    spec_id = spec_data.pop("id", None)
                    logger.info(f"Processing spec: id={spec_id}, data_keys={list(spec_data.keys())}")
                    if spec_id and spec_id in existing_spec_ids:
                        await self.spec_service.update_spec(spec_id, ProductSpecUpdate(**spec_data))
                        submitted_spec_ids.add(spec_id)
                        logger.info(f"Updated spec {spec_id}")
                    else:
                        spec_data["product_id"] = id
                        spec = await self.spec_service.create_spec(ProductSpecCreate(**spec_data))
                        logger.info(f"Created new spec: id={spec['id']}")
                        submitted_spec_ids.add(spec["id"])

                for existing_spec in existing_specs:
                    if existing_spec["id"] not in submitted_spec_ids:
                        await self.spec_service.delete_spec(existing_spec["id"])
                        logger.info(f"Deleted spec {existing_spec['id']}")
            except (ValidationError, ValueError):
                raise
            except Exception as e:
                logger.error(f"Error updating specs: {e}", exc_info=True)
                raise

        return True

    async def get_product_by_code(self, product_code: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"product_code": product_code})

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        brand_id: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if keyword:
            filters["$or"] = [
                {"product_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ]
        if brand_id:
            filters["brand_id"] = brand_id
        if category_id:
            filters["category_id"] = category_id

        skip = (page - 1) * page_size
        total = await self.count(filters)

        cursor = self.collection.find(filters).sort("created_at", -1).skip(skip).limit(page_size)
        products = await cursor.to_list(length=page_size)

        for p in products:
            p["id"] = str(p.pop("_id"))

        if not products:
            return {"total": total, "page": page, "page_size": page_size, "items": []}

        product_ids = [p["id"] for p in products]
        all_specs = await self.spec_service.find_many({"product_id": {"$in": product_ids}})

        spec_ids = [s["id"] for s in all_specs if s.get("id")]
        stock_map = await self.spec_service._batch_get_stock_info(spec_ids)

        specs_map: Dict[str, List] = {}
        for spec in all_specs:
            sid = spec.get("id")
            stock_info = stock_map.get(sid)
            if stock_info:
                spec["stock_quantity"] = stock_info["total_quantity"]
                spec["stock_status"] = stock_info["min_status"]
            else:
                spec["stock_quantity"] = 0
                spec["stock_status"] = "out_of_stock"

            pid = spec.get("product_id")
            if pid not in specs_map:
                specs_map[pid] = []
            specs_map[pid].append(spec)

        category_ids = list(set([p.get("category_id") for p in products if p.get("category_id")]))
        logger.info(f"Category ids to fetch: {category_ids}")
        category_map = await self._get_categories_map(category_ids)
        logger.info(f"【Category map】: {len(category_map)}")

        brand_ids = list(set([p.get("brand_id") for p in products if p.get("brand_id")]))
        brand_map = await self._get_brands_map(brand_ids)

        for product in products:
            product["specs"] = specs_map.get(product["id"], [])
            product["category_name"] = category_map.get(product.get("category_id"), None)
            product["brand_name"] = brand_map.get(product.get("brand_id"), None)
        return {"total": total, "page": page, "page_size": page_size, "items": products}

    async def _get_categories_map(self, category_ids: List[str]) -> Dict[str, str]:
        if not category_ids:
            return {}
        category_list = await self.category_service.find_many({"_id": {"$in": [ObjectId(cid) for cid in category_ids]}})
        result = {}
        for doc in category_list:
            result[str(doc["id"])] = doc.get("name", "")
        return result

    async def _get_brands_map(self, brand_ids: List[str]) -> Dict[str, str]:
        if not brand_ids:
            return {}
        brand_list = await brand_service.find_many({"_id": {"$in": [ObjectId(bid) for bid in brand_ids]}})
        result = {}
        for doc in brand_list:
            result[str(doc["id"])] = doc.get("name", "")
        return result

    async def get_product_with_specs(self, product_id: str) -> Optional[Dict[str, Any]]:
        product = await self.get_by_id(product_id)
        if not product:
            return None
        specs = await self.spec_service.get_specs_by_product_id(product_id)
        product["specs"] = specs
        if product.get("category_id"):
            category_map = await self._get_categories_map([product.get("category_id")])
            product["category_name"] = category_map.get(product.get("category_id"))
        else:
            product["category_name"] = None
        if product.get("brand_id"):
            brand_map = await self._get_brands_map([product.get("brand_id")])
            product["brand_name"] = brand_map.get(product.get("brand_id"))
        else:
            product["brand_name"] = None
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
            {"$addFields": {
                "warehouse_id_obj": {"$toObjectId": "$warehouse_id"}
            }},
            {"$lookup": {
                "from": "warehouses",
                "localField": "warehouse_id_obj",
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
            if item.get("category_id"):
                category_map = await self._get_categories_map([item.get("category_id")])
                item["category_name"] = category_map.get(item.get("category_id"))
            else:
                item["category_name"] = None
            if item.get("brand_id"):
                brand_map = await self._get_brands_map([item.get("brand_id")])
                item["brand_name"] = brand_map.get(item.get("brand_id"))
            else:
                item["brand_name"] = None

        return items


product_service = ProductService()
product_spec_service = ProductSpecService()
