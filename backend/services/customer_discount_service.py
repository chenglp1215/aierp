"""
客户折扣管理 - 服务层
"""
from typing import Optional, Dict, Any, List

from .base_service import BaseService
from models.customer_discount import (
    CustomerDiscount,
    CustomerDiscountCreate,
    CustomerDiscountUpdate,
)


class CustomerDiscountService(BaseService):
    """客户折扣服务类"""

    def __init__(self):
        super().__init__("customer_discounts")

    def _generate_id(self, prefix: str = "DIS") -> str:
        """生成ID"""
        import uuid
        return f"{prefix}{uuid.uuid4().hex[:12].upper()}"

    async def create_discount(
        self, discount_data: CustomerDiscountCreate
    ) -> CustomerDiscount:
        """创建客户折扣"""
        data = discount_data.model_dump()
        data["id"] = self._generate_id("DIS")
        discount_id = await self.create(data)
        return await self.get_by_id(discount_id)

    async def update_discount(
        self, discount_id: str, discount_data: CustomerDiscountUpdate
    ) -> bool:
        """更新客户折扣"""
        data = discount_data.model_dump(exclude_unset=True)
        if not data:
            return True
        return await self.update(discount_id, data)

    async def get_by_id(self, discount_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取折扣"""
        return await super().get_by_id(discount_id)

    async def delete_discount(self, discount_id: str) -> bool:
        """删除折扣"""
        return await self.delete(discount_id)

    async def list_discounts(
        self,
        page: int = 1,
        page_size: int = 20,
        customer_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """获取客户折扣列表"""
        filters = {}

        if customer_id:
            filters["customer_id"] = customer_id
        if brand_id:
            filters["brand_id"] = brand_id
        if is_active is not None:
            filters["is_active"] = is_active

        result = await self.list(page, page_size, filters, "created_at", -1)
        
        # 获取品牌名称
        if result.get("items"):
            # TODO: brand_service 已迁移至 services.product_service，需更新导入路径
            from services.brand_service import brand_service
            brand_ids = [item.get("brand_id") for item in result["items"] if item.get("brand_id")]
            if brand_ids:
                brands = await brand_service.get_brands_by_ids(brand_ids)
                brand_map = {brand["id"]: brand.get("name", "") for brand in brands}
                for item in result["items"]:
                    item["brand_name"] = brand_map.get(item.get("brand_id"), "")
        
        return result

    async def get_discount_by_customer_and_brand(
        self, customer_id: str, brand_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定客户和品牌的折扣"""
        return await self.find_one({
            "customer_id": customer_id,
            "brand_id": brand_id
        })

    async def toggle_discount_status(
        self, discount_id: str, is_active: bool
    ) -> bool:
        """切换折扣状态"""
        return await self.update(discount_id, {"is_active": is_active})

    async def check_duplicate(
        self, customer_id: str, brand_id: str, exclude_id: Optional[str] = None
    ) -> bool:
        """检查是否存在重复的折扣配置"""
        filters = {
            "customer_id": customer_id,
            "brand_id": brand_id
        }
        if exclude_id:
            from bson import ObjectId
            try:
                filters["_id"] = {"$ne": ObjectId(exclude_id)}
            except Exception:
                pass
        exists = await self.collection.find_one(filters)
        return exists is not None


customer_discount_service = CustomerDiscountService()
