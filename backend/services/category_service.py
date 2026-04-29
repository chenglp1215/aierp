from typing import Optional, Dict, Any, List
import logging
from bson import ObjectId
from datetime import datetime

from .base_service import BaseService
from models.category import CategoryCreate, CategoryUpdate, CategoryTreeNode

logger = logging.getLogger(__name__)


class CategoryService(BaseService):
    def __init__(self):
        super().__init__("categories")

    async def _get_level(self, parent_id: Optional[str]) -> int:
        if not parent_id:
            return 1
        parent = await self.find_one({"_id": ObjectId(parent_id)})
        if not parent:
            return 1
        return parent.get("level", 1) + 1

    async def _get_parent(self, parent_id: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"_id": ObjectId(parent_id)})

    async def _get_children_count(self, parent_id: str) -> int:
        return await self.count({"parent_id": parent_id})

    async def _get_all_children(self, category_id: str) -> List[Dict[str, Any]]:
        children = []
        queue = [category_id]
        while queue:
            current_id = queue.pop(0)
            cursor = self.collection.find({"parent_id": current_id})
            async for child in cursor:
                child["id"] = str(child.pop("_id"))
                queue.append(child["id"])
                children.append(child)
        return children

    async def create_category(self, category_data: CategoryCreate) -> Dict[str, Any]:
        data = category_data.model_dump()
        level = await self._get_level(data.get("parent_id"))
        if level > 3:
            raise ValueError("分类最多支持三级")
        if data.get("parent_id"):
            parent = await self._get_parent(data["parent_id"])
            if not parent:
                raise ValueError("父分类不存在")
            if parent.get("level", 1) >= 3:
                raise ValueError("分类最多支持三级")
        data["level"] = level
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()
        data.pop("id", None)
        for key in ["parent_id"]:
            if data.get(key):
                data[key] = str(data[key])
        result = await self.collection.insert_one(data)
        data["id"] = str(result.inserted_id)
        from models.category import Category
        return Category(**data).model_dump(mode='json')

    async def update_category(self, id: str, category_data: CategoryUpdate) -> bool:
        data = category_data.model_dump(exclude_unset=True)
        if not data:
            return True
        if "parent_id" in data:
            if data["parent_id"] == id:
                raise ValueError("不能将自己设为父分类")
            if data["parent_id"]:
                parent = await self._get_parent(data["parent_id"])
                if not parent:
                    raise ValueError("父分类不存在")
                current = await self.get_by_id(id)
                if current:
                    current_level = current.get("level", 1)
                    new_parent_level = parent.get("level", 1)
                    if new_parent_level >= 3:
                        raise ValueError("分类最多支持三级")
                    children = await self._get_all_children(id)
                    for child in children:
                        child_level = child.get("level", 1)
                        level_diff = child_level - current_level
                        new_level = new_parent_level + 1 + level_diff
                        if new_level > 3:
                            raise ValueError("该操作会导致子分类超过三级限制")
                level = parent.get("level", 1) + 1
                data["level"] = level
            else:
                data["level"] = 1
        data["updated_at"] = datetime.now()
        result = await self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        return result.modified_count > 0 or result.matched_count > 0

    async def delete_category(self, id: str) -> bool:
        children_count = await self._get_children_count(id)
        if children_count > 0:
            raise ValueError("该分类下存在子分类，无法删除")
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def get_category_tree(self) -> List[Dict[str, Any]]:
        all_categories = []
        cursor = self.collection.find({}).sort("sort_order", 1)
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            all_categories.append(doc)
        return await self._build_tree(all_categories)

    async def _build_tree(self, categories: List[Dict[str, Any]], parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        tree = []
        for cat in categories:
            if cat.get("parent_id") == parent_id:
                node = {
                    "id": cat["id"],
                    "name": cat["name"],
                    "parent_id": cat.get("parent_id"),
                    "tax_code": cat.get("tax_code"),
                    "sort_order": cat.get("sort_order", 0),
                    "is_shop_display": cat.get("is_shop_display", True),
                    "level": cat.get("level", 1),
                    "children": []
                }
                children = await self._build_tree(categories, cat["id"])
                node["children"] = children
                tree.append(node)
        return tree

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        doc = await super().get_by_id(id)
        return doc

    async def list_categories(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if keyword:
            filters["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"tax_code": {"$regex": keyword, "$options": "i"}}
            ]
        if parent_id is not None:
            if parent_id == "":
                filters["parent_id"] = None
            else:
                filters["parent_id"] = parent_id
        skip = (page - 1) * page_size
        total = await self.count(filters)
        cursor = self.collection.find(filters).sort("sort_order", 1).skip(skip).limit(page_size)
        items = []
        async for doc in cursor:
            doc_id = doc.pop("_id")
            doc["id"] = str(doc_id)
            if doc.get("parent_id") and hasattr(doc["parent_id"], '__str__'):
                doc["parent_id"] = str(doc["parent_id"])
            items.append(doc)
        return {"total": total, "page": page, "page_size": page_size, "items": items}

    async def get_all_as_tree_nodes(self) -> List[Dict[str, Any]]:
        return await self.get_category_tree()


category_service = CategoryService()
