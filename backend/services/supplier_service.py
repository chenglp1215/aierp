"""
供应商管理 - 服务层
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from bson import ObjectId
from models.supplier import Supplier

from .base_service import BaseService
from validators.supplier_validator import (
    SUPPLIER_CREATE_CONFIG,
    SUPPLIER_UPDATE_CONFIG,
    validate_supplier_brands,
)

logger = logging.getLogger(__name__)


class SupplierService(BaseService):
    """供应商服务类"""

    def __init__(self):
        super().__init__("suppliers")
        self.model = Supplier

    async def format(self, supplier: Dict[str, Any]) -> Dict[str, Any]:
        """格式化供应商数据"""
        return supplier

    async def format_list(self, suppliers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化供应商列表"""
        return [await self.format(s) for s in suppliers]

    def validate_supplier_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """校验创建供应商数据"""
        return self.validate_data(data, SUPPLIER_CREATE_CONFIG)

    def validate_supplier_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """校验更新供应商数据"""
        return self.validate_data(data, SUPPLIER_UPDATE_CONFIG)

    async def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建供应商"""
        valid, errors = self.validate_supplier_create(supplier_data)
        if not valid:
            raise ValueError(errors)

        is_valid, msg = validate_supplier_brands(supplier_data.get("supplied_brands", []))
        if not is_valid:
            raise ValueError(msg)

        supplier_data["id"] = await self.create(supplier_data)
        supplier_data.pop("_id", None)
        return supplier_data

    async def update_supplier(self, id: str, supplier_data: Dict[str, Any]) -> bool:
        """更新供应商"""
        valid, errors = self.validate_supplier_update(supplier_data)
        if not valid:
            raise ValueError(errors)

        if supplier_data.get("supplied_brands") is not None:
            is_valid, msg = validate_supplier_brands(supplier_data["supplied_brands"])
            if not is_valid:
                raise ValueError(msg)

        return await self.update(id, supplier_data)

    async def delete_supplier(self, id: str) -> bool:
        """删除供应商"""
        purchase_count = await self.db["purchaseOrders"].count_documents(
            {"supplier_id": id}
        )
        if purchase_count > 0:
            raise ValueError(f"该供应商下存在 {purchase_count} 个采购单，无法删除")
        return await self.delete(id)

    async def get_supplier_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取供应商"""
        supplier = await self.get_by_id(id)
        if not supplier:
            raise ValueError("供应商不存在")
        return await self.format(supplier)

    async def get_supplier_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取供应商"""
        return await self.find_one({"name": name})

    async def list_suppliers(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
        brand_ids: Optional[List[str]] = None,
        _: dict = None
    ) -> Dict[str, Any]:
        """分页查询供应商列表"""
        filters = {}
        if keyword:
            filters["name"] = {"$regex": keyword, "$options": "i"}
        if is_active is not None:
            filters["is_active"] = is_active
        if brand_ids:
            filters["supplied_brands.brand_id"] = {"$in": brand_ids}

        result = await self.list(
            page=page,
            page_size=page_size,
            filters=filters,
            sort_field="created_at",
            sort_order=-1
        )
        result["items"] = await self.format_list(result["items"])
        return result

    async def get_all_suppliers(
        self,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """获取所有供应商"""
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        items = await self.find_many(filters, sort={"name": 1})
        return await self.format_list(items)

    async def toggle_supplier_active(self, id: str, is_active: bool) -> bool:
        """切换供应商激活状态"""
        success = await self.update(id, {"is_active": is_active})
        if not success:
            raise ValueError("供应商不存在或更新失败")
        return success

    async def check_name_unique(
        self,
        name: str,
        exclude_id: Optional[str] = None
    ) -> bool:
        """检查供应商名称是否唯一"""
        return await self.validate_unique("name", name, exclude_id)

    async def get_suppliers_by_brand_id(self, brand_id: str) -> List[Dict[str, Any]]:
        """根据品牌ID获取供应商列表"""
        items = await self.find_many({
            "supplied_brands.brand_id": brand_id,
            "is_active": True
        }, sort={"name": 1})
        return await self.format_list(items)


supplier_service = SupplierService()