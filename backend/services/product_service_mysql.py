"""
商品模块服务层 - MySQL 版本
"""
import random
import string
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from tortoise.expressions import Q

from models_mysql.product import Brand, Category, Product, ProductSpec

logger = logging.getLogger(__name__)


class BrandService:
    """品牌服务"""

    def _generate_brand_code(self) -> str:
        """生成品牌编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"BRAND{date_str}{random_str}"

    async def create_brand(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建品牌"""
        name = brand_data.get("name")
        if not name:
            raise ValueError("品牌名称不能为空")

        # 检查名称唯一性
        existing = await Brand.filter(name=name).first()
        if existing:
            raise ValueError("品牌名称已存在")

        # 验证运费不能为负数
        default_freight = brand_data.get("default_freight", 0)
        # 处理空字符串，转换为 0
        if default_freight == "" or default_freight is None:
            default_freight = 0
        else:
            default_freight = float(default_freight)
        if default_freight < 0:
            raise ValueError("运费不能为负数")

        brand = await Brand.create(
            name=name,
            logo_url=brand_data.get("logo_url") or None,
            description=brand_data.get("description") or None,
            purchaser_id=brand_data.get("purchaser_id") if brand_data.get("purchaser_id") else None,
            purchaser_name=brand_data.get("purchaser_name") or None,
            is_active=brand_data.get("is_active", True),
            default_freight=default_freight if default_freight is not None else 0,
        )
        return brand.to_dict()

    async def update_brand(self, brand_id: int, brand_data: Dict[str, Any]) -> bool:
        """更新品牌"""
        brand = await Brand.get_or_none(id=brand_id)
        if not brand:
            raise ValueError("品牌不存在")

        # 检查名称唯一性
        name = brand_data.get("name")
        if name and name != brand.name:
            existing = await Brand.filter(name=name).exclude(id=brand_id).first()
            if existing:
                raise ValueError("品牌名称已存在")
            brand.name = name

        if "logo_url" in brand_data:
            brand.logo_url = brand_data["logo_url"]
        if "description" in brand_data:
            brand.description = brand_data["description"]
        if "purchaser_id" in brand_data:
            purchaser_id = brand_data["purchaser_id"]
            brand.purchaser_id = purchaser_id if purchaser_id else None
        if "purchaser_name" in brand_data:
            brand.purchaser_name = brand_data["purchaser_name"] or None
        if "is_active" in brand_data:
            brand.is_active = brand_data["is_active"]
        if "default_freight" in brand_data:
            # 验证运费不能为负数
            default_freight = brand_data["default_freight"]
            # 处理空字符串，转换为 0
            if default_freight == "" or default_freight is None:
                default_freight = 0
            else:
                default_freight = float(default_freight)
            if default_freight < 0:
                raise ValueError("运费不能为负数")
            brand.default_freight = default_freight

        await brand.save()
        return True

    async def get_brand_by_id(self, brand_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取品牌"""
        brand = await Brand.get_or_none(id=brand_id)
        if not brand:
            raise ValueError("品牌不存在")
        return brand.to_dict()

    async def get_brand_by_keyword(
        self, keyword: Optional[str] = None, page: int = 1, page_size: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """根据关键词搜索品牌"""
        query = Brand.all()
        if keyword:
            query = query.filter(Q(name__contains=keyword) | Q(description__contains=keyword))

        total = await query.count()
        brands = await query.offset((page - 1) * page_size).limit(page_size)
        return [b.to_dict() for b in brands], total

    async def get_all_brands(self) -> List[Dict[str, Any]]:
        """获取所有品牌"""
        brands = await Brand.filter(is_active=True).all()
        return [b.to_dict() for b in brands]

    async def get_brand_name(self, brand_id: int) -> Optional[str]:
        """获取品牌名称"""
        brand = await Brand.get_or_none(id=brand_id)
        return brand.name if brand else None

    async def get_brand_by_ids(self, brand_ids: List[int]) -> List[Dict[str, Any]]:
        """根据ID列表获取品牌"""
        brands = await Brand.filter(id__in=brand_ids).all()
        return [b.to_dict() for b in brands]

    async def delete_brand(self, brand_id: int) -> bool:
        """删除品牌"""
        brand = await Brand.get_or_none(id=brand_id)
        if not brand:
            raise ValueError("品牌不存在")

        # 检查是否有关联商品
        product_count = await Product.filter(brand_id=brand_id).count()
        if product_count > 0:
            raise ValueError("该品牌下有商品，不能删除")

        await brand.delete()
        return True


class CategoryService:
    """分类服务"""

    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建分类"""
        name = category_data.get("name")
        if not name:
            raise ValueError("分类名称不能为空")

        # 检查名称唯一性
        existing = await Category.filter(name=name).first()
        if existing:
            raise ValueError("分类名称已存在")

        parent_id = category_data.get("parent_id")
        category = await Category.create(
            name=name,
            parent_id=parent_id,
            tax_code=category_data.get("tax_code"),
            sort_order=category_data.get("sort_order", 0),
            is_shop_display=category_data.get("is_shop_display", True),
        )
        result = category.to_dict()
        result["level"] = await category.get_level()
        result["children"] = []
        return result

    async def update_category(self, category_id: int, category_data: Dict[str, Any]) -> bool:
        """更新分类"""
        category = await Category.get_or_none(id=category_id)
        if not category:
            raise ValueError("分类不存在")

        # 检查名称唯一性
        name = category_data.get("name")
        if name and name != category.name:
            existing = await Category.filter(name=name).exclude(id=category_id).first()
            if existing:
                raise ValueError("分类名称已存在")
            category.name = name

        if "parent_id" in category_data:
            # 不能将自己设为自己的父级
            if category_data["parent_id"] == category_id:
                raise ValueError("不能将自己设为父分类")
            category.parent_id = category_data["parent_id"]
        if "tax_code" in category_data:
            category.tax_code = category_data["tax_code"]
        if "sort_order" in category_data:
            category.sort_order = category_data["sort_order"]
        if "is_shop_display" in category_data:
            category.is_shop_display = category_data["is_shop_display"]

        await category.save()
        return True

    async def get_category_by_id(self, category_id: int, is_formatted: bool = True) -> Optional[Dict[str, Any]]:
        """根据ID获取分类"""
        category = await Category.get_or_none(id=category_id)
        if not category:
            raise ValueError("分类不存在")

        result = category.to_dict()
        if is_formatted:
            result["level"] = await category.get_level()
            result["children"] = await category.get_children_recursive()
        return result

    async def get_category_tree(self) -> List[Dict[str, Any]]:
        """获取分类树"""
        # 获取所有顶级分类
        root_categories = await Category.filter(parent_id=None).order_by("sort_order", "id").all()
        result = []
        for category in root_categories:
            cat_dict = category.to_dict()
            cat_dict["level"] = 1
            cat_dict["children"] = await category.get_children_recursive()
            result.append(cat_dict)
        return result

    async def get_category_name(self, category_id: int) -> Optional[str]:
        """获取分类名称"""
        category = await Category.get_or_none(id=category_id)
        return category.name if category else None

    async def delete_category(self, category_id: int) -> bool:
        """删除分类"""
        category = await Category.get_or_none(id=category_id)
        if not category:
            raise ValueError("分类不存在")

        # 检查是否有子分类
        child_count = await Category.filter(parent_id=category_id).count()
        if child_count > 0:
            raise ValueError("该分类下有子分类，不能删除")

        # 检查是否有商品
        product_count = await Product.filter(category_id=category_id).count()
        if product_count > 0:
            raise ValueError("该分类下有商品，不能删除")

        await category.delete()
        return True


class ProductSpecService:
    """商品规格服务"""

    def _generate_spec_code(self) -> str:
        """生成规格编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"SPEC{date_str}{random_str}"

    async def create_spec(self, spec_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建规格"""
        product_id = spec_data.get("product_id")
        if not product_id:
            raise ValueError("商品ID不能为空")

        # 验证商品存在
        product = await Product.get_or_none(id=int(product_id))
        if not product:
            raise ValueError("商品不存在")

        # 生成规格编号
        spec_code = spec_data.get("spec_code") or self._generate_spec_code()

        # 检查编号唯一性
        existing = await ProductSpec.filter(spec_code=spec_code).first()
        if existing:
            raise ValueError("规格编号已存在")

        spec = await ProductSpec.create(
            product_id=int(product_id),
            spec_code=spec_code,
            packaging=spec_data.get("packaging"),
            sales_spec=spec_data.get("sales_spec"),
            price=float(spec_data.get("price", 0)),
            cas_number=spec_data.get("cas_number"),
            is_active=spec_data.get("is_active", True),
        )
        return await spec.to_dict()

    async def update_spec(self, spec_id: int, spec_data: Dict[str, Any]) -> bool:
        """更新规格"""
        spec = await ProductSpec.get_or_none(id=spec_id)
        if not spec:
            raise ValueError("规格不存在")

        if "packaging" in spec_data:
            spec.packaging = spec_data["packaging"]
        if "sales_spec" in spec_data:
            spec.sales_spec = spec_data["sales_spec"]
        if "price" in spec_data:
            spec.price = float(spec_data["price"])
        if "cas_number" in spec_data:
            spec.cas_number = spec_data["cas_number"]
        if "is_active" in spec_data:
            spec.is_active = spec_data["is_active"]

        await spec.save()
        return True

    async def get_spec_by_id(self, spec_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取规格"""
        spec = await ProductSpec.get_or_none(id=spec_id)
        if not spec:
            raise ValueError("规格不存在")
        return await spec.to_dict()

    async def get_spec_by_product_id(self, product_id: int, is_formatted: bool = False) -> List[Dict[str, Any]]:
        """根据商品ID获取规格列表"""
        specs = await ProductSpec.filter(product_id=product_id).all()
        if is_formatted:
            return [await s.to_dict() for s in specs]
        return [s.to_dict() for s in specs]

    async def get_spec_by_product_ids(self, product_ids: List[int], is_formatted: bool = False) -> Dict[int, List[Dict[str, Any]]]:
        """根据商品ID列表获取规格映射"""
        specs = await ProductSpec.filter(product_id__in=product_ids).all()
        result = {pid: [] for pid in product_ids}
        for spec in specs:
            result[spec.product_id].append(await spec.to_dict())
        return result

    async def get_spec_by_ids(self, spec_ids: List[int], is_formatted: bool = False) -> List[Dict[str, Any]]:
        """根据ID列表获取规格"""
        specs = await ProductSpec.filter(id__in=spec_ids).all()
        return [await s.to_dict() for s in specs]

    async def get_spec_by_codes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """根据编号列表获取规格"""
        specs = await ProductSpec.filter(spec_code__in=codes).all()
        return [await s.to_dict() for s in specs]

    async def get_spec_by_keyword(
        self, keyword: str, page: int = 1, page_size: int = 20, is_formatted: bool = False
    ) -> tuple[List[Dict[str, Any]], int]:
        """根据关键词搜索规格"""
        query = ProductSpec.filter(spec_code__contains=keyword)
        total = await query.count()
        specs = await query.offset((page - 1) * page_size).limit(page_size)
        if is_formatted:
            return [await s.to_dict() for s in specs], total
        return [s.to_dict() for s in specs], total

    async def delete_spec(self, spec_id: int) -> bool:
        """删除规格"""
        spec = await ProductSpec.get_or_none(id=spec_id)
        if not spec:
            raise ValueError("规格不存在")
        await spec.delete()
        return True


class ProductService:
    """商品服务"""

    def _generate_product_code(self) -> str:
        """生成商品编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"PROD{date_str}{random_str}"

    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建商品"""
        name = product_data.get("name")
        if not name:
            raise ValueError("商品名称不能为空")

        # 验证品牌
        brand_id = product_data.get("brand_id")
        if not brand_id:
            raise ValueError("品牌ID不能为空")
        brand_name = await brand_service.get_brand_name(int(brand_id))
        if not brand_name:
            raise ValueError("品牌不存在")

        # 验证分类
        category_id = product_data.get("category_id")
        if not category_id:
            raise ValueError("分类ID不能为空")
        category_name = await category_service.get_category_name(int(category_id))
        if not category_name:
            raise ValueError("分类不存在")

        # 生成商品编号
        product_code = product_data.get("product_code") or self._generate_product_code()

        # 检查编号唯一性
        existing = await Product.filter(product_code=product_code).first()
        if existing:
            raise ValueError("商品编号已存在")

        product = await Product.create(
            product_code=product_code,
            name=name,
            image_url=product_data.get("image_url"),
            brand_id=int(brand_id),
            category_id=int(category_id),
            tax_code=product_data.get("tax_code"),
            is_active=product_data.get("is_active", True),
        )

        # 创建规格
        specs = product_data.get("specs", [])
        for spec_data in specs:
            spec_data["product_id"] = product.id
            await product_spec_service.create_spec(spec_data)

        return await product.to_dict(include_specs=True)

    async def update_product(self, product_id: int, product_data: Dict[str, Any]) -> bool:
        """更新商品"""
        product = await Product.get_or_none(id=product_id)
        if not product:
            raise ValueError("商品不存在")

        # 验证品牌
        if "brand_id" in product_data:
            brand_name = await brand_service.get_brand_name(int(product_data["brand_id"]))
            if not brand_name:
                raise ValueError("品牌不存在")
            product.brand_id = int(product_data["brand_id"])

        # 验证分类
        if "category_id" in product_data:
            category_name = await category_service.get_category_name(int(product_data["category_id"]))
            if not category_name:
                raise ValueError("分类不存在")
            product.category_id = int(product_data["category_id"])

        if "name" in product_data:
            product.name = product_data["name"]
        if "image_url" in product_data:
            product.image_url = product_data["image_url"]
        if "tax_code" in product_data:
            product.tax_code = product_data["tax_code"]
        if "is_active" in product_data:
            product.is_active = product_data["is_active"]

        await product.save()
        return True

    async def get_product_by_id(self, product_id: int, is_formatted: bool = False) -> Optional[Dict[str, Any]]:
        """根据ID获取商品"""
        product = await Product.get_or_none(id=product_id)
        if not product:
            raise ValueError("商品不存在")
        return await product.to_dict(include_specs=is_formatted)

    async def get_product_by_ids(self, product_ids: List[int]) -> List[Dict[str, Any]]:
        """根据ID列表获取商品"""
        products = await Product.filter(id__in=product_ids).all()
        return [await p.to_dict() for p in products]

    async def get_product_by_codes(self, codes: List[str]) -> List[Dict[str, Any]]:
        """根据编号列表获取商品"""
        products = await Product.filter(product_code__in=codes).all()
        return [await p.to_dict() for p in products]

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        brand_id: Optional[int] = None,
        category_id: Optional[int] = None,
        is_formatted: bool = True,
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取商品列表"""
        query = Product.all()

        if brand_id:
            query = query.filter(brand_id=int(brand_id))
        if category_id:
            query = query.filter(category_id=int(category_id))
        if keyword:
            query = query.filter(Q(product_code__contains=keyword) | Q(name__contains=keyword))

        total = await query.count()
        products = await query.offset((page - 1) * page_size).limit(page_size)

        if is_formatted:
            return [await p.to_dict(include_specs=True) for p in products], total
        return [p.to_dict() for p in products], total

    async def delete_product(self, product_id: int) -> bool:
        """删除商品"""
        product = await Product.get_or_none(id=product_id)
        if not product:
            raise ValueError("商品不存在")

        # 删除关联规格
        await ProductSpec.filter(product_id=product_id).delete()

        await product.delete()
        return True


# 创建服务实例
brand_service = BrandService()
category_service = CategoryService()
product_spec_service = ProductSpecService()
product_service = ProductService()