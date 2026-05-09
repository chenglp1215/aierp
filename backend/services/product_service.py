from typing import Optional, Dict, Any, List
import random
import string
import logging
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from .base_service import BaseService
from models.product import Brand, Category, ProductSpec, Product
from validators.product_validator import (
    PRODUCT_CREATE_CONFIG,
    PRODUCT_UPDATE_CONFIG,
    PRODUCT_SPEC_CREATE_CONFIG,
    PRODUCT_SPEC_UPDATE_CONFIG,
    BRAND_CREATE_CONFIG,
    BRAND_UPDATE_CONFIG,
    CATEGORY_CREATE_CONFIG,
    CATEGORY_UPDATE_CONFIG,
)

logger = logging.getLogger(__name__)

class BrandService(BaseService):
    def __init__(self):
        super().__init__("product_brands")
        self.models = Brand

    def validate_brand_create(self, brand_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(brand_data, BRAND_CREATE_CONFIG)

    def validate_brand_update(self, brand_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(brand_data, BRAND_UPDATE_CONFIG)

    async def format(self, brand):
        return brand

    async def format_list(self, brands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [await self.format(brand) for brand in brands]

    async def create_brand(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        valid, errors = self.validate_brand_create(brand_data)
        if not valid:
            raise ValueError(errors)
        name = brand_data.get("name")
        existing = await self.find_one({"name": name})
        if existing:
            raise ValueError("品牌名称已存在")
        brand_data["id"] = await self.create(brand_data)
        brand_data.pop("_id", None)
        return brand_data

    async def update_brand(self, id: str, brand_data: Dict[str, Any]) -> bool:
        valid, errors = self.validate_brand_update(brand_data)
        if not valid:
            raise ValueError(errors)
        name = brand_data.get("name")
        existing = await self.find_one({"name": name})
        if existing and existing["id"] != id:
            raise ValueError("品牌名称已存在")
        return await self.update(id, brand_data)

    async def get_brand_by_id(self, id: str) -> Dict[str, Any]:
        try:
            brand = await self.find_one({"_id": ObjectId(id)})
        except InvalidId:
            raise ValueError("品牌ID格式无效")
        if brand is None:
            raise ValueError("品牌不存在")
        return await self.format(brand)  

    async def get_brand_by_keyword(self, keyword: str, page: int = 1, page_size: int = 20) -> tuple[List[Dict[str, Any]], int]:
        # 模糊查询品牌名称，品牌描述
        if keyword:
            query = {"$or": [{"name": {"$regex": keyword}}, {"description": {"$regex": keyword}}]}
        else:
            query = {}
        brands = await self.find_many(query, limit=page_size, skip=(page - 1) * page_size)
        total = await self.count(query)
        return await self.format_list(brands), total

    async def get_brand_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        brands = await self.find_many({"_id": {"$in": [ObjectId(id) for id in ids]}}, limit=len(ids))
        return await self.format_list(brands)

    async def get_brand_name(self, brand_id: str) -> Optional[str]:
        try:
            brand = await self.find_one({"_id": ObjectId(brand_id)})
        except (InvalidId, Exception):
            return None
        if brand is None:
            return None
        return brand.get("name", None)

    async def get_all_brands(self) -> List[Dict[str, Any]]:
        # 注意：获取所有品牌时，建议在生产环境中限制返回数量，避免性能问题
        return await self.format_list(await self.find_many(filters={}, limit=10000))


    async def delete_brand(self, id: str) -> bool:
        # 检查品牌下是否有商品 在方法体内部延迟引用product_service
        from .product_service import product_service
        product = await product_service.find_one({"brand_id": str(id)})
        if product:
            raise ValueError("该品牌下有商品，不能删除")
        return await self.delete(id)


class CategoryService(BaseService):
    def __init__(self):
        super().__init__("product_categories")
        self.models = Category  


    async def format(self, category: Dict[str, Any]) -> Dict[str, Any]:
        return category
    
    async def format_list(self, categorys: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [await self.format(category) for category in categorys]

    def validate_category_create(self, category_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(category_data, CATEGORY_CREATE_CONFIG)

    def validate_category_update(self, category_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(category_data, CATEGORY_UPDATE_CONFIG)

    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        valid, errors = self.validate_category_create(category_data)
        if not valid:
            raise ValueError(errors)
        name = category_data.get("name")
        existing = await self.find_one({"name": name})
        if existing:
            raise ValueError("分类名称已存在")
        category_data["id"] = await self.create(category_data)
        category_data.pop("_id", None)
        return category_data

    async def update_category(self, id: str, category_data: Dict[str, Any]) -> bool:
        valid, errors = self.validate_category_update(category_data)
        if not valid:
            raise ValueError(errors)
        name = category_data.get("name")
        existing = await self.find_one({"name": name})
        if existing and existing["id"] != id:
            raise ValueError("分类名称已存在")
        return await self.update(id, category_data)

    async def get_category_by_id(self, id: str, is_formatted: bool = True) -> Dict[str, Any]:
        try:
            category = await self.find_one({"_id": ObjectId(id)})
        except InvalidId:
            raise ValueError("分类ID格式无效")
        if category is None:
            raise ValueError("分类不存在")
        if is_formatted:
            category = await self.format(category)
        category["level"] = await self._calculate_level(category.get("parent_id"))
        category["children"] = await self._get_category_node_children(category["id"])
        return category
        
    async def get_category_by_keyword(self, keyword: str, page: int = 1, page_size: int = 20) -> tuple[List[Dict[str, Any]], int]:
        # 模糊查询分类名称
        if keyword:
            query = {"name": {"$regex": keyword}}
        else:
            query = {}
        categories = await self.find_many(query, limit=page_size, skip=(page - 1) * page_size)
        count = await self.count(query)
        return await self.format_list(categories), count    

    async def get_category_by_ids(self, ids: List[str]) -> List[Dict[str, Any]]:
        categories = await self.find_many({"_id": {"$in": [ObjectId(id) for id in ids]}}, limit=len(ids))
        return await self.format_list(categories)    

    async def get_category_name(self, category_id: str) -> Optional[str]:
        try:
            category = await self.find_one({"_id": ObjectId(category_id)})
        except (InvalidId, Exception):
            return None
        if category is None:
            return None
        return category.get("name", None)

    async def delete_category(self, id: str) -> bool:
        # 检查分类下是否有子分类 在方法体内部延迟引用product_service
        from .product_service import product_service
        children = await self.count({"parent_id": str(id)})
        if children:
            raise ValueError("该分类下有子分类，不能删除")
        product = await product_service.find_one({"category_id": str(id)})
        if product: 
            raise ValueError("该分类下有商品，不能删除")
        return await self.delete(id)

    async def _get_category_node_children(self, category_id: str) -> List[Dict[str, Any]]:
        categorys = await self.find_many({"parent_id": str(category_id)})
        for category in categorys:
            category["level"] = await self._calculate_level(category.get("parent_id"))
            category["children"] = await self._get_category_node_children(category["id"])
        return categorys

    MAX_CATEGORY_LEVEL = 5

    async def _calculate_level(self, parent_id: Optional[str]) -> int:
        if parent_id is None:
            return 1
        level = 1
        current_parent_id = parent_id
        while current_parent_id and level < self.MAX_CATEGORY_LEVEL:
            try:
                parent = await self.find_one({"_id": ObjectId(current_parent_id)})
            except InvalidId:
                break
            if not parent or not parent.get("parent_id"):
                level += 1
                break
            current_parent_id = parent["parent_id"]
            level += 1
        return level

    async def get_category_tree(self) -> List[Dict[str, Any]]:
        root_categories = await self.find_many({"parent_id": None})
        for category in root_categories:
            category["level"] = 1
            category["children"] = await self._get_category_node_children(category["id"])
        return await self.format_list(root_categories)



class ProductSpecService(BaseService):
    def __init__(self):
        super().__init__("product_specs")
        self.models = ProductSpec

    def _generate_spec_code(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"SPEC{date_str}{random_str}"

    async def format(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        from .inventory_service import warehouse_service, stock_service
        spec['stock_status'] = await stock_service.get_stock_status_by_spec_ids([spec.get("spec_id")]).get(spec.get("spec_id"), [])
        return spec
    
    async def format_list(self, specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        from .inventory_service import warehouse_service, stock_service
        stock_status_map = await stock_service.get_stock_status_by_spec_ids([spec.get("spec_id") for spec in specs])
        for spec in specs:
            spec['stock_status'] = stock_status_map.get(spec.get("spec_id"), [])
        return specs

    def validate_spec_create(self, spec_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(spec_data, PRODUCT_SPEC_CREATE_CONFIG)

    def validate_spec_update(self, spec_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(spec_data, PRODUCT_SPEC_UPDATE_CONFIG)

    async def create_spec(self, spec_data: Dict[str, Any]) -> Dict[str, Any]:
        valid, errors = self.validate_spec_create(spec_data)
        if not valid:
            raise ValueError(errors)
        if not spec_data.get("spec_code"):
            spec_data['spec_code'] = self._generate_spec_code()
        spec_data["id"] = await self.create(spec_data)
        spec_data.pop("_id", None)
        return spec_data

    async def update_spec(self, id: str, spec_data: Dict[str, Any]) -> bool:
        valid, errors = self.validate_spec_update(spec_data)
        if not valid:
            raise ValueError(errors)
        return await self.update(id, spec_data)

    async def get_spec_by_code(self, spec_code: str, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        spec = await self.find_one({"spec_code": spec_code})
        if is_formatted:
            return await self.format(spec)
        return spec

    async def get_spec_by_id(self, id: str, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        spec = await self.get_by_id(id)
        if is_formatted:
            return await self.format(spec)
        return spec 

    async def get_spec_by_keyword(self, keyword: str, page: int = 1, page_size: int = 20, is_formatted: bool = False) -> tuple[List[Dict[str, Any]], int]:
        # 模糊查询商品规格编码，商品规格名称，商品规格包装，商品规格销售规格
        filters = {}
        if keyword:
            filters["$or"] = [
                {"spec_code": {"$regex": keyword, "$options": "i"}},
            ]
        specs = await self.find_many(filters, limit=page_size, skip=(page - 1) * page_size)
        total = await self.count(filters)
        if is_formatted:
            return await self.format_list(specs), total
        return specs, total

    async def get_spec_by_codes(self, spec_codes: List[str], is_formatted: bool = False) -> List[Dict[str, Any]]:
        specs = await self.find_many({"spec_code": {"$in": spec_codes}}, limit=10000)
        if is_formatted:
            return await self.format_list(specs)
        return specs    
        
    async def get_spec_by_ids(self, ids: List[str], is_formatted: bool = False) -> List[Dict[str, Any]]:
        specs = await self.find_many({"_id": {"$in": [ObjectId(id) for id in ids]}}, limit=len(ids))
        if is_formatted:
            return await self.format_list(specs)
        return specs    
    
    async def get_spec_by_product_id(self, product_id: str, is_formatted: bool = False) -> List[Dict[str, Any]]:
        specs = await self.find_many({"product_id": str(product_id)})
        if is_formatted:
            return await self.format_list(specs)
        return specs    

    async def get_spec_by_product_ids(self, product_ids: List[str], is_formatted: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        if not product_ids:
            return {}
        product_id_sepc_map = {}
        for each in product_ids:
            product_id_sepc_map[each] = []  
        specs = await self.find_many({"product_id": {"$in": [str(id) for id in product_ids]}}, limit=10000)
        if is_formatted:
            specs = await self.format_list(specs) 
        for spec in specs:
            product_id_sepc_map[str(spec["product_id"])].append(spec)
        return product_id_sepc_map  

    async def _get_stock_by_spec_id(self, spec_id: str) -> Optional[Dict[str, Any]]:
        # todo: 从库存表中查询库存
        return {}

    async def _get_stock_by_spec_ids(self, spec_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        # todo: 从库存表中查询库存
        return {}

    async def list_specs(self, page: int = 1, page_size: int = 20, product_id: Optional[str] = None) -> tuple[List[Dict[str, Any]], int]:
        specs = await self.find_many({"product_id": str(product_id)}, limit=page_size, skip=(page - 1) * page_size)
        total = await self.count({"product_id": str(product_id)})
        return specs, total

    async def delete_spec(self, id: str) -> bool:
        return await self.delete(id)


class ProductService(BaseService):
    def __init__(self):
        super().__init__("products")
        self.models = Product
        self.spec_service = ProductSpecService()
        self.brand_service = BrandService()
        self.category_service = CategoryService()

    def _generate_product_code(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"PROD{date_str}{random_str}"

    def validate_product_create(self, product_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(product_data, PRODUCT_CREATE_CONFIG)

    def validate_product_update(self, product_data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(product_data, PRODUCT_UPDATE_CONFIG)

    async def format(self, product: Dict[str, Any]) -> Dict[str, Any]:
        product["specs"] = await self.spec_service.get_spec_by_product_id(product["id"], is_formatted=True)
        return product

    async def format_list(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        specs_maps = await self.spec_service.get_spec_by_product_ids([p["id"] for p in products], is_formatted=True)
        for product in products:
            product["specs"] = specs_maps.get(str(product["id"]), [])
        return products

    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        valid, errors = self.validate_product_create(product_data)
        if not valid:
            raise ValueError(errors)
        if not product_data.get("product_code"):
            product_data['product_code'] = self._generate_product_code()
        if brand := await self.brand_service.get_brand_name(product_data.get("brand_id")):
            product_data['brand_name'] = brand
        else:
            raise ValueError("品牌不存在")
        if category := await self.category_service.get_category_name(product_data.get("category_id")):
            product_data['category_name'] = category
        else:
            raise ValueError("分类不存在")
        product_data["id"] = await self.create(product_data)
        product_data.pop("_id", None)

        if "specs" in product_data and product_data["specs"]:
            for each in product_data["specs"]:
                each["product_id"] = product_data["id"]
                await self.spec_service.create_spec(each)

        return product_data

    async def update_product(self, id: str, product_data: Dict[str, Any]) -> bool:
        valid, errors = self.validate_product_update(product_data)
        if not valid:
            raise ValueError(errors)
        if "brand_id" in product_data and product_data["brand_id"]:
            brand_name = await self.brand_service.get_brand_name(product_data["brand_id"])
            if not brand_name:
                raise ValueError("品牌不存在")
            product_data["brand_name"] = brand_name
        if "category_id" in product_data and product_data["category_id"]:
            category_name = await self.category_service.get_category_name(product_data["category_id"])
            if not category_name:
                raise ValueError("分类不存在")
            product_data["category_name"] = category_name
        update_result = await self.update(id, product_data)
        return update_result

    async def get_product_by_code(self, product_code: str, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        product = await self.find_one({"product_code": product_code})
        if not product:
            raise ValueError("商品不存在")
        if is_formatted:
            return await self.format(product)
        return product

    async def get_product_by_id(self, id: str, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        product = await self.get_by_id(id)
        if not product:
            raise ValueError("商品不存在")
        if is_formatted:
            return await self.format(product)
        return product

    async def get_product_by_keyword(self, keyword: str, page: int = 1, page_size: int = 20, is_formatted: bool = False) -> List[Dict[str, Any]]:
        products = await self.find_many({"$or": [
            {"product_code": {"$regex": keyword, "$options": "i"}},
            {"name": {"$regex": keyword, "$options": "i"}}
        ]}, limit=page_size, skip=(page - 1) * page_size)
        if is_formatted:
            products = await self.format_list(products)
        return products

    async def get_product_by_ids(self, ids: List[str], is_formatted: bool = False) -> List[Dict[str, Any]]:
        products = await self.find_many({"_id": {"$in": [ObjectId(id) for id in ids]}}, limit=len(ids))
        if is_formatted:
            products = await self.format_list(products) 
        return products

    async def list_products(self, 
        brand_id: Optional[str] = None,
        category_id: Optional[str] = None, 
        keyword: Optional[str] = None,
        page: int = 1, 
        page_size: int = 20, 
        is_formatted: bool = True
     ) -> tuple[List[Dict[str, Any]], int]:
        query = {}
        if brand_id:
            query["brand_id"] = brand_id
        if category_id:
            query["category_id"] = category_id
        if keyword:
            query["$or"] = [
                {"product_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ]
        total = await self.count(query)
        products = await self.find_many(query, limit=page_size, skip=(page - 1) * page_size)
        if is_formatted:
            products = await self.format_list(products)
        return products, total

    async def delete_product(self, id: str) -> bool:
        await self.spec_service.delete_many({"product_id": str(id)})
        return await self.delete(id)


product_service = ProductService()
product_spec_service = ProductSpecService()
brand_service = BrandService()
category_service = CategoryService()