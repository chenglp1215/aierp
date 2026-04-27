from typing import Optional, Dict, Any
import random
import string

from .base_service import BaseService
from models.product import ProductCreate, ProductUpdate, ProductStatus


class ProductService(BaseService):
    """商品管理服务"""

    def __init__(self):
        super().__init__("products")

    def _generate_product_code(self) -> str:
        """生成商品编号"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"PROD{date_str}{random_str}"

    async def create_product(self, product_data: ProductCreate) -> str:
        """创建商品"""
        data = product_data.model_dump()
        if not data.get("product_code"):
            data["product_code"] = self._generate_product_code()
        data["status"] = ProductStatus.ACTIVE.value
        return await self.create(data)

    async def update_product(self, id: str, product_data: ProductUpdate) -> bool:
        """更新商品信息"""
        data = product_data.model_dump(exclude_unset=True)
        return await self.update(id, data)

    async def get_product_by_code(self, product_code: str) -> Optional[Dict[str, Any]]:
        """根据商品编号获取商品"""
        return await self.find_one({"product_code": product_code})

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询商品列表"""
        filters = {}

        if status:
            filters["status"] = status
        if keyword:
            filters["$or"] = [
                {"product_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
                {"brand": {"$regex": keyword, "$options": "i"}}
            ]

        return await self.list(page, page_size, filters, "created_at", -1)

    async def get_product_stats(self) -> Dict[str, Any]:
        """获取商品统计信息"""
        total = await self.count({"status": ProductStatus.ACTIVE.value})
        active_count = await self.count({"status": ProductStatus.ACTIVE.value})
        inactive_count = await self.count({"status": ProductStatus.INACTIVE.value})

        return {
            "total": total,
            "active_count": active_count,
            "inactive_count": inactive_count
        }

    async def update_status(self, id: str, status: ProductStatus) -> bool:
        """更新商品状态"""
        return await self.update(id, {"status": status.value})

    async def search_products(self, keyword: str, limit: int = 10) -> list:
        """搜索商品"""
        filters = {
            "status": ProductStatus.ACTIVE.value,
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"product_code": {"$regex": keyword, "$options": "i"}},
                {"brand": {"$regex": keyword, "$options": "i"}}
            ]
        }

        cursor = self.collection.find(filters).limit(limit)
        items = await cursor.to_list(length=limit)

        for item in items:
            item["id"] = str(item.pop("_id"))

        return items


product_service = ProductService()
