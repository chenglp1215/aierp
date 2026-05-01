from typing import Optional, Dict, Any, List
import logging
from bson import ObjectId
from datetime import datetime

from .base_service import BaseService
from models.product import BrandCreate, BrandUpdate

logger = logging.getLogger(__name__)


class BrandService(BaseService):
    def __init__(self):
        super().__init__("brands")

    async def create_brand(self, brand_data: BrandCreate) -> Dict[str, Any]:
        data = brand_data.model_dump()
        data.pop("id", None)
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()
        result = await self.collection.insert_one(data)
        data["id"] = str(result.inserted_id)
        from models.product import Brand
        return Brand(**data).model_dump(mode='json')

    async def update_brand(self, id: str, brand_data: BrandUpdate) -> bool:
        data = brand_data.model_dump(exclude_unset=True)
        if not data:
            return True
        data["updated_at"] = datetime.now()
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def delete_brand(self, id: str) -> bool:
        product_count = await self.db["products"].count_documents({"brand_id": id})
        if product_count > 0:
            raise ValueError(f"该品牌下存在 {product_count} 个商品，无法删除")
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def get_brand_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.get_by_id(id)

    async def get_brand_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"name": name})

    async def list_brands(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        filters = {}
        if keyword:
            filters["name"] = {"$regex": keyword, "$options": "i"}
        if is_active is not None:
            filters["is_active"] = is_active
        skip = (page - 1) * page_size
        total = await self.count(filters)
        cursor = self.collection.find(filters).sort("created_at", -1).skip(skip).limit(page_size)
        items = []
        async for doc in cursor:
            doc_id = doc.pop("_id")
            doc["id"] = str(doc_id)
            items.append(doc)
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    async def get_all_brands(
        self,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        cursor = self.collection.find(filters).sort("name", 1)
        items = []
        async for doc in cursor:
            doc_id = doc.pop("_id")
            doc["id"] = str(doc_id)
            items.append(doc)
        return items

    async def get_brands_by_ids(self, brand_ids: List[str]) -> List[Dict[str, Any]]:
        """根据ID列表获取品牌信息"""
        if not brand_ids:
            return []
        
        # 将字符串ID转换为ObjectId
        object_ids = []
        for brand_id in brand_ids:
            try:
                object_ids.append(ObjectId(brand_id))
            except Exception:
                continue
        
        if not object_ids:
            return []
        
        cursor = self.collection.find({"_id": {"$in": object_ids}})
        items = []
        async for doc in cursor:
            doc_id = doc.pop("_id")
            doc["id"] = str(doc_id)
            items.append(doc)
        return items

    async def toggle_brand_active(self, id: str, is_active: bool) -> bool:
        return await self.update(id, {"is_active": is_active})

    async def check_name_unique(
        self,
        name: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        filters = {"name": name}
        if exclude_id:
            try:
                filters["_id"] = {"$ne": ObjectId(exclude_id)}
            except Exception:
                pass
        exists = await self.collection.find_one(filters)
        return not exists


brand_service = BrandService()