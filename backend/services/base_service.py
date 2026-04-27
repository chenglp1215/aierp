from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseService:
    """基础服务类，提供通用的 CRUD 操作"""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    @property
    def db(self):
        from app.database import db
        return db.get_mongo_db()

    @property
    def collection(self):
        return self.db[self.collection_name]

    async def create(self, data: Dict[str, Any]) -> str:
        """创建文档"""
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取文档"""
        from bson import ObjectId
        try:
            doc = await self.collection.find_one({"_id": ObjectId(id)})
            if doc:
                doc["id"] = str(doc.pop("_id"))
            return doc
        except Exception as e:
            logger.error(f"Error getting document by id: {e}")
            return None

    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """更新文档"""
        from bson import ObjectId
        data["updated_at"] = datetime.now()
        data.pop("id", None)
        data.pop("_id", None)
        data.pop("created_at", None)
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False

    async def delete(self, id: str) -> bool:
        """删除文档"""
        from bson import ObjectId
        try:
            result = await self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_field: str = "created_at",
        sort_order: int = -1
    ) -> Dict[str, Any]:
        """分页列表查询"""
        filters = filters or {}
        skip = (page - 1) * page_size

        cursor = self.collection.find(filters).sort(sort_field, sort_order)
        total = await self.collection.count_documents(filters)
        items = await cursor.skip(skip).limit(page_size).to_list(length=page_size)

        for item in items:
            item["id"] = str(item.pop("_id"))

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }

    async def find_one(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档"""
        doc = await self.collection.find_one(filters)
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计文档数量"""
        filters = filters or {}
        return await self.collection.count_documents(filters)
