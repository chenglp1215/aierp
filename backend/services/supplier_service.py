"""
供应商管理 - 服务层
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from bson import ObjectId

from .base_service import BaseService
from models.supplier import SupplierCreate, SupplierUpdate

logger = logging.getLogger(__name__)


class SupplierService(BaseService):
    """供应商服务类"""

    def __init__(self):
        super().__init__("suppliers")

    async def create_supplier(self, supplier_data: SupplierCreate) -> Dict[str, Any]:
        """创建供应商"""
        data = supplier_data.model_dump()
        data.pop("id", None)
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()
        result = await self.collection.insert_one(data)
        data["id"] = str(result.inserted_id)
        from models.supplier import Supplier
        return Supplier(**data).model_dump(mode='json')

    async def update_supplier(self, id: str, supplier_data: SupplierUpdate) -> bool:
        """更新供应商"""
        data = supplier_data.model_dump(exclude_unset=True)
        if not data:
            return True
        data["updated_at"] = datetime.now()
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0 or result.matched_count > 0

    async def delete_supplier(self, id: str) -> bool:
        """删除供应商"""
        # 检查是否有采购单关联此供应商
        purchase_count = await self.db["purchaseOrders"].count_documents(
            {"supplier_id": id}
        )
        if purchase_count > 0:
            raise ValueError(f"该供应商下存在 {purchase_count} 个采购单，无法删除")
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def get_supplier_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取供应商"""
        return await self.get_by_id(id)

    async def get_supplier_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取供应商"""
        return await self.find_one({"name": name})

    async def list_suppliers(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """分页查询供应商列表"""
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

    async def get_all_suppliers(
        self,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """获取所有供应商（用于下拉选择等）"""
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

    async def toggle_supplier_active(self, id: str, is_active: bool) -> bool:
        """切换供应商激活状态"""
        return await self.update(id, {"is_active": is_active})

    async def check_name_unique(
        self,
        name: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """检查供应商名称是否唯一"""
        filters = {"name": name}
        if exclude_id:
            try:
                filters["_id"] = {"$ne": ObjectId(exclude_id)}
            except Exception:
                pass
        exists = await self.collection.find_one(filters)
        return not exists

    async def get_suppliers_by_brand_id(self, brand_id: str) -> List[Dict[str, Any]]:
        """根据品牌ID获取供应商列表"""
        cursor = self.collection.find({
            "supplied_brands.brand_id": brand_id,
            "is_active": True
        }).sort("name", 1)
        items = []
        async for doc in cursor:
            doc_id = doc.pop("_id")
            doc["id"] = str(doc_id)
            items.append(doc)
        return items


supplier_service = SupplierService()
