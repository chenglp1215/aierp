# Product MySQL 重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 product 模块从 MongoDB 迁移到 MySQL，创建 Tortoise ORM 模型和服务层

**Architecture:** 创建 MySQL 数据模型（Brand、Category、Product、ProductSpec），重写服务层使用 Tortoise ORM，路由层保持 API 兼容

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL, Pydantic V2

---

## 文件结构

| 文件 | 操作 | 负责内容 |
|------|------|----------|
| `backend/models_mysql/product.py` | 创建 | Brand、Category、Product、ProductSpec 模型 |
| `backend/models_mysql/__init__.py` | 修改 | 导出新模型 |
| `backend/services/product_service_mysql.py` | 创建 | MySQL 版本服务层 |
| `backend/app/routers/product.py` | 修改 | 切换到 MySQL 服务层 |
| `backend/scripts/init_db_sync.py` | 修改 | 添加商品模块表初始化 |

---

### Task 1: 创建 Brand 模型

**Files:**
- Create: `backend/models_mysql/product.py`

- [ ] **Step 1: 创建 product.py 文件并添加 Brand 模型**

创建 `backend/models_mysql/product.py` 文件：

```python
"""
商品模块 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class Brand(Model):
    """品牌模型"""
    id = fields.IntField(pk=True, description="品牌ID")
    name = fields.CharField(max_length=100, unique=True, description="品牌名称")
    logo_url = fields.CharField(max_length=500, null=True, description="品牌Logo")
    description = fields.CharField(max_length=500, null=True, description="品牌描述")
    purchaser_id = fields.IntField(null=True, description="采购人员ID")
    purchaser_name = fields.CharField(max_length=100, null=True, description="采购人员名称")
    is_active = fields.BooleanField(default=True, description="是否有效")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "brands"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        """转换为字典格式（兼容 API 响应）"""
        return {
            "id": self.id,
            "name": self.name,
            "logo_url": self.logo_url,
            "description": self.description,
            "purchaser_id": self.purchaser_id,
            "purchaser_name": self.purchaser_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 验证模型语法**

Run: `cd backend && python -c "from models_mysql.product import Brand; print('Brand model OK')"`
Expected: 输出 "Brand model OK"

---

### Task 2: 创建 Category 模型

**Files:**
- Modify: `backend/models_mysql/product.py`

- [ ] **Step 1: 在 product.py 中添加 Category 模型**

在 `Brand` 模型后添加：

```python
class Category(Model):
    """分类模型（支持树形结构）"""
    id = fields.IntField(pk=True, description="分类ID")
    name = fields.CharField(max_length=100, unique=True, description="分类名称")
    parent: fields.ForeignKeyNullableRelation["Category"] = fields.ForeignKeyField(
        "models.Category", null=True, related_name="children", description="父分类"
    )
    tax_code = fields.CharField(max_length=50, null=True, description="税务编码")
    sort_order = fields.IntField(default=0, description="排序")
    is_shop_display = fields.BooleanField(default=True, description="是否商城展示")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "categories"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name

    async def get_level(self) -> int:
        """计算分类层级"""
        level = 1
        parent = await self.parent
        while parent is not None:
            level += 1
            parent = await parent.parent
        return level

    async def get_children_recursive(self) -> list:
        """递归获取所有子分类"""
        children = await self.children.all()
        result = []
        for child in children:
            child_dict = child.to_dict()
            child_dict["level"] = await child.get_level()
            child_dict["children"] = await child.get_children_recursive()
            result.append(child_dict)
        return result

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "tax_code": self.tax_code,
            "sort_order": self.sort_order,
            "is_shop_display": self.is_shop_display,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 验证模型语法**

Run: `cd backend && python -c "from models_mysql.product import Brand, Category; print('Brand, Category models OK')"`
Expected: 输出 "Brand, Category models OK"

---

### Task 3: 创建 Product 模型

**Files:**
- Modify: `backend/models_mysql/product.py`

- [ ] **Step 1: 在 product.py 中添加 Product 模型**

在 `Category` 模型后添加：

```python
class Product(Model):
    """商品模型"""
    id = fields.IntField(pk=True, description="商品ID")
    product_code = fields.CharField(max_length=50, unique=True, description="商品编号")
    name = fields.CharField(max_length=200, description="商品名称")
    image_url = fields.CharField(max_length=500, null=True, description="商品图片")
    brand: fields.ForeignKeyRelation[Brand] = fields.ForeignKeyField(
        "models.Brand", related_name="products", description="品牌"
    )
    category: fields.ForeignKeyRelation[Category] = fields.ForeignKeyField(
        "models.Category", related_name="products", description="分类"
    )
    tax_code = fields.CharField(max_length=50, null=True, description="税务编码")
    is_active = fields.BooleanField(default=True, description="是否有效")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "products"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product_code}: {self.name}"

    async def to_dict(self, include_specs: bool = False):
        """转换为字典格式"""
        brand = await self.brand
        category = await self.category
        result = {
            "id": self.id,
            "product_code": self.product_code,
            "name": self.name,
            "image_url": self.image_url,
            "brand_id": self.brand_id,
            "brand_name": brand.name if brand else None,
            "category_id": self.category_id,
            "category_name": category.name if category else None,
            "tax_code": self.tax_code,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_specs:
            specs = await self.specs.all()
            result["specs"] = [await spec.to_dict() for spec in specs]
        return result
```

- [ ] **Step 2: 验证模型语法**

Run: `cd backend && python -c "from models_mysql.product import Brand, Category, Product; print('Brand, Category, Product models OK')"`
Expected: 输出 "Brand, Category, Product models OK"

---

### Task 4: 创建 ProductSpec 模型

**Files:**
- Modify: `backend/models_mysql/product.py`

- [ ] **Step 1: 在 product.py 中添加 ProductSpec 模型**

在 `Product` 模型后添加：

```python
class ProductSpec(Model):
    """商品规格模型"""
    id = fields.IntField(pk=True, description="规格ID")
    product: fields.ForeignKeyRelation[Product] = fields.ForeignKeyField(
        "models.Product", related_name="specs", description="商品"
    )
    spec_code = fields.CharField(max_length=50, unique=True, description="规格编号")
    packaging = fields.CharField(max_length=100, null=True, description="包装")
    sales_spec = fields.CharField(max_length=100, null=True, description="销售规格")
    price = fields.FloatField(description="价格")
    cas_number = fields.CharField(max_length=50, null=True, description="CAS号")
    is_active = fields.BooleanField(default=True, description="是否有效")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "product_specs"
        ordering = ["id"]

    def __str__(self):
        return f"{self.spec_code}: {self.packaging or ''}"

    async def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "spec_code": self.spec_code,
            "packaging": self.packaging,
            "sales_spec": self.sales_spec,
            "price": self.price,
            "cas_number": self.cas_number,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 验证模型语法**

Run: `cd backend && python -c "from models_mysql.product import Brand, Category, Product, ProductSpec; print('All models OK')"`
Expected: 输出 "All models OK"

---

### Task 5: 导出模型

**Files:**
- Modify: `backend/models_mysql/__init__.py`

- [ ] **Step 1: 更新 __init__.py 导出新模型**

将 `backend/models_mysql/__init__.py` 修改为：

```python
"""
MySQL ORM 模型（Tortoise ORM）
"""
from .auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType
from .product import Brand, Category, Product, ProductSpec

__all__ = [
    "User",
    "Role",
    "Permission",
    "UserStatus",
    "RoleStatus",
    "PermissionType",
    "Brand",
    "Category",
    "Product",
    "ProductSpec",
]
```

- [ ] **Step 2: 验证导入**

Run: `cd backend && python -c "from models_mysql import Brand, Category, Product, ProductSpec; print('Import OK')"`
Expected: 输出 "Import OK"

- [ ] **Step 3: 提交模型创建**

```bash
git add backend/models_mysql/product.py backend/models_mysql/__init__.py
git commit -m "feat: 创建商品模块 MySQL 模型

- Brand 模型（brands 表）
- Category 模型（categories 表，支持树形结构）
- Product 模型（products 表）
- ProductSpec 模型（product_specs 表）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: 创建 BrandService 服务

**Files:**
- Create: `backend/services/product_service_mysql.py`

- [ ] **Step 1: 创建服务文件并添加 BrandService**

创建 `backend/services/product_service_mysql.py` 文件：

```python
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

        brand = await Brand.create(
            name=name,
            logo_url=brand_data.get("logo_url"),
            description=brand_data.get("description"),
            purchaser_id=brand_data.get("purchaser_id"),
            purchaser_name=brand_data.get("purchaser_name"),
            is_active=brand_data.get("is_active", True),
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
            brand.purchaser_id = brand_data["purchaser_id"]
        if "purchaser_name" in brand_data:
            brand.purchaser_name = brand_data["purchaser_name"]
        if "is_active" in brand_data:
            brand.is_active = brand_data["is_active"]

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


brand_service = BrandService()
```

- [ ] **Step 2: 验证语法**

Run: `cd backend && python -c "from services.product_service_mysql import brand_service; print('BrandService OK')"`
Expected: 输出 "BrandService OK"

---

### Task 7: 创建 CategoryService 服务

**Files:**
- Modify: `backend/services/product_service_mysql.py`

- [ ] **Step 1: 在服务文件中添加 CategoryService**

在 `BrandService` 类后添加：

```python
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


category_service = CategoryService()
```

- [ ] **Step 2: 验证语法**

Run: `cd backend && python -c "from services.product_service_mysql import brand_service, category_service; print('BrandService, CategoryService OK')"`
Expected: 输出 "BrandService, CategoryService OK"

---

### Task 8: 创建 ProductService 服务

**Files:**
- Modify: `backend/services/product_service_mysql.py`

- [ ] **Step 1: 在服务文件中添加 ProductService**

在 `CategoryService` 类后添加：

```python
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


product_service = ProductService()
```

- [ ] **Step 2: 验证语法**

Run: `cd backend && python -c "from services.product_service_mysql import brand_service, category_service, product_service; print('ProductService OK')"`
Expected: 输出 "ProductService OK"

---

### Task 9: 创建 ProductSpecService 服务

**Files:**
- Modify: `backend/services/product_service_mysql.py`

- [ ] **Step 1: 在服务文件中添加 ProductSpecService**

在 `ProductService` 类后添加：

```python
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


product_spec_service = ProductSpecService()
```

- [ ] **Step 2: 验证语法**

Run: `cd backend && python -c "from services.product_service_mysql import brand_service, category_service, product_service, product_spec_service; print('All services OK')"`
Expected: 输出 "All services OK"

- [ ] **Step 3: 提交服务层创建**

```bash
git add backend/services/product_service_mysql.py
git commit -m "feat: 创建商品模块 MySQL 服务层

- BrandService: 品牌服务
- CategoryService: 分类服务（支持树形查询）
- ProductService: 商品服务
- ProductSpecService: 商品规格服务

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 10: 修改路由使用 MySQL 服务

**Files:**
- Modify: `backend/app/routers/product.py`

- [ ] **Step 1: 修改导入语句**

将 `backend/app/routers/product.py` 的导入语句从：

```python
from services.product_service import product_service, product_spec_service, brand_service, category_service
```

修改为：

```python
from services.product_service_mysql import product_service, product_spec_service, brand_service, category_service
```

- [ ] **Step 2: 添加 ID 类型转换辅助函数**

在导入语句后添加：

```python
def to_int_id(id_str: str) -> int:
    """将字符串 ID 转换为整数 ID"""
    try:
        return int(id_str)
    except (ValueError, TypeError):
        raise ValueError("无效的ID格式")
```

- [ ] **Step 3: 修改所有路由函数使用 to_int_id**

修改所有使用 ID 参数的路由：

```python
@product_router.get("/specs/{spec_id}", response_model=dict)
@wrap_response
async def get_spec(
    spec_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取规格详情"""
    spec = await product_spec_service.get_spec_by_id(to_int_id(spec_id))
    return spec


@product_router.put("/specs/{spec_id}", response_model=dict)
@wrap_response
async def update_spec(
    spec_id: str,
    spec: Dict[str, Any],
    _: dict = Depends(require_permission("product.edit"))
):
    """更新规格信息"""
    await product_spec_service.update_spec(to_int_id(spec_id), spec)
    return "规格更新成功"


@product_router.delete("/specs/{spec_id}", response_model=dict)
@wrap_response
async def delete_spec(
    spec_id: str,
    _: dict = Depends(require_permission("product.delete"))
):
    """删除规格"""
    await product_spec_service.delete_spec(to_int_id(spec_id))
    return "规格删除成功"


@product_router.get("/{product_id}", response_model=dict)
@wrap_response
async def get_product(
    product_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品详情（包含规格列表）"""
    product = await product_service.get_product_by_id(to_int_id(product_id), is_formatted=True)
    return product


@product_router.put("/{product_id}", response_model=dict)
@wrap_response
async def update_product(
    product_id: str,
    product: Dict[str, Any],
    _: dict = Depends(require_permission("product.edit"))
):
    """更新商品信息"""
    await product_service.update_product(to_int_id(product_id), product)
    return "商品更新成功"


@product_router.delete("/{product_id}", response_model=dict)
@wrap_response
async def delete_product(
    product_id: str,
    _: dict = Depends(require_permission("product.delete"))
):
    """删除商品（同时删除关联规格）"""
    await product_service.delete_product(to_int_id(product_id))
    return "商品删除成功"


@product_router.get("/{product_id}/specs", response_model=dict)
@wrap_response
async def list_product_specs(
    product_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品的所有规格"""
    specs = await product_spec_service.get_spec_by_product_id(product_id=to_int_id(product_id), is_formatted=True)
    return {
        "total": len(specs),
        "items": specs
    }


@product_router.post("/{product_id}/specs", response_model=dict)
@wrap_response
async def create_product_spec(
    product_id: str,
    spec: Dict[str, Any],
    _: dict = Depends(require_permission("product.create"))
):
    """为商品创建规格"""
    await product_service.get_product_by_id(to_int_id(product_id))
    spec["product_id"] = to_int_id(product_id)
    spec_data = await product_spec_service.create_spec(spec)
    return spec_data


@brand_router.put("/{brand_id}", response_model=dict)
@wrap_response
async def update_brand(
    brand_id: str,
    brand: Dict[str, Any],
    _: dict = Depends(require_permission("brand.edit"))
):
    """更新品牌"""
    await brand_service.update_brand(to_int_id(brand_id), brand)
    return "品牌更新成功"


@brand_router.get("/{brand_id}", response_model=dict)
@wrap_response
async def get_brand(
    brand_id: str,
    _: dict = Depends(require_permission("brand.view"))
):
    """获取品牌详情"""
    brand = await brand_service.get_brand_by_id(to_int_id(brand_id))
    return brand


@brand_router.delete("/{brand_id}", response_model=dict)
@wrap_response
async def delete_brand(
    brand_id: str,
    _: dict = Depends(require_permission("brand.delete"))
):
    """删除品牌"""
    await brand_service.delete_brand(to_int_id(brand_id))
    return "品牌删除成功"


@category_router.put("/{category_id}", response_model=dict)
@wrap_response
async def update_category(
    category_id: str,
    category: Dict[str, Any],
    _: dict = Depends(require_permission("category.edit"))
):
    """更新分类"""
    await category_service.update_category(to_int_id(category_id), category)
    return "分类更新成功"


@category_router.get("/{category_id}", response_model=dict)
@wrap_response
async def get_category(
    category_id: str,
    _: dict = Depends(require_permission("category.view"))
):
    """获取分类详情"""
    category = await category_service.get_category_by_id(to_int_id(category_id), is_formatted=True)
    return category


@category_router.delete("/{category_id}", response_model=dict)
@wrap_response
async def delete_category(
    category_id: str,
    _: dict = Depends(require_permission("category.delete"))
):
    """删除分类"""
    await category_service.delete_category(to_int_id(category_id))
    return "分类删除成功"
```

- [ ] **Step 4: 验证路由语法**

Run: `cd backend && python -c "from app.routers.product import brand_router, category_router, product_router; print('Routers OK')"`
Expected: 输出 "Routers OK"

- [ ] **Step 5: 提交路由修改**

```bash
git add backend/app/routers/product.py
git commit -m "feat: 切换商品模块路由到 MySQL 服务层

- 修改导入使用 MySQL 服务
- 添加 ID 类型转换函数
- 保持 API 接口兼容

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 11: 更新数据库初始化脚本

**Files:**
- Modify: `backend/scripts/init_db_sync.py`

- [ ] **Step 1: 在 init_db_sync.py 中添加商品模块表初始化**

在文件末尾的 `main()` 函数调用前，添加商品模块表创建函数：

```python
def init_product_tables(conn):
    """初始化商品模块表"""
    cursor = conn.cursor()

    # 创建品牌表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            logo_url VARCHAR(500),
            description VARCHAR(500),
            purchaser_id INT,
            purchaser_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 创建分类表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            parent_id INT,
            tax_code VARCHAR(50),
            sort_order INT DEFAULT 0,
            is_shop_display BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 创建商品表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_code VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(200) NOT NULL,
            image_url VARCHAR(500),
            brand_id INT NOT NULL,
            category_id INT NOT NULL,
            tax_code VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE RESTRICT,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 创建商品规格表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_specs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            spec_code VARCHAR(50) NOT NULL UNIQUE,
            packaging VARCHAR(100),
            sales_spec VARCHAR(100),
            price DOUBLE NOT NULL,
            cas_number VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    conn.commit()
    logger.info("商品模块表初始化成功")
```

- [ ] **Step 2: 在 main 函数中调用新函数**

修改 `main()` 函数，在 `init_admin_user(conn)` 后添加：

```python
def main():
    logger.info("开始初始化 MySQL 数据库数据...")

    try:
        conn = get_connection()

        init_default_permissions(conn)
        init_super_admin_role(conn)
        init_warehouse_admin_role(conn)
        init_purchaser_group_role(conn)
        init_default_user_role(conn)
        init_admin_user(conn)
        init_product_tables(conn)  # 添加这行

        conn.close()
        logger.info("MySQL 数据库初始化完成")

    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
```

- [ ] **Step 3: 运行初始化脚本**

Run: `cd backend && python scripts/init_db_sync.py`
Expected: 输出包含 "商品模块表初始化成功"

- [ ] **Step 4: 验证表结构**

Run: `cd backend && python -c "
import pymysql
from config import settings
conn = pymysql.connect(host=settings.MYSQL_HOST, port=settings.MYSQL_PORT, user=settings.MYSQL_USER, password=settings.MYSQL_PASSWORD, database=settings.MYSQL_DATABASE)
cursor = conn.cursor()
cursor.execute('SHOW TABLES')
for row in cursor.fetchall():
    print(row[0])
conn.close()
"`
Expected: 显示 brands, categories, products, product_specs 表

- [ ] **Step 5: 提交初始化脚本修改**

```bash
git add backend/scripts/init_db_sync.py
git commit -m "feat: 添加商品模块表初始化

- brands 表
- categories 表（支持树形结构）
- products 表
- product_specs 表

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 12: 验证完整功能

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && python main.py &`
Expected: 服务启动成功

- [ ] **Step 2: 测试品牌接口**

Run: `curl -X GET "http://localhost:8000/api/v1/brands/" -H "Authorization: Bearer <token>"`
Expected: 返回空列表或品牌数据

- [ ] **Step 3: 测试分类接口**

Run: `curl -X GET "http://localhost:8000/api/v1/categories/" -H "Authorization: Bearer <token>"`
Expected: 返回空列表或分类树

- [ ] **Step 4: 测试商品接口**

Run: `curl -X GET "http://localhost:8000/api/v1/products/" -H "Authorization: Bearer <token>"`
Expected: 返回空列表或商品数据

---

## 自检清单

**1. Spec 覆盖率:**
- [x] Brand 数据模型 → Task 1
- [x] Category 数据模型（树形结构） → Task 2
- [x] Product 数据模型 → Task 3
- [x] ProductSpec 数据模型 → Task 4
- [x] Brand 服务层 → Task 6
- [x] Category 服务层（树形查询） → Task 7
- [x] Product 服务层 → Task 8
- [x] ProductSpec 服务层 → Task 9
- [x] API 兼容性 → Task 10

**2. 占位符扫描:** 无 TBD、TODO、"implement later" 等占位符

**3. 类型一致性:** 所有 ID 使用 int 类型，路由层进行 string 到 int 转换
