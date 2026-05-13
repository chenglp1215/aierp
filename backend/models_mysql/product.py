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
