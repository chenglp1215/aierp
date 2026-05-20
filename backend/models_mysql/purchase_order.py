"""
采购单管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model
from enum import Enum

from models_mysql.product import Brand, ProductSpec
from models_mysql.warehouse import Warehouse


class PurchaseType(str, Enum):
    """采购类型"""
    DIRECT = "direct"      # 直运采购
    WAREHOUSE = "warehouse"  # 仓库采购


class PurchaseStatus(str, Enum):
    """采购单主流程状态"""
    PENDING_REVIEW = "pending_review"    # 待审核
    READY_PURCHASE = "ready_purchase"    # 准备采购
    PURCHASING = "purchasing"            # 采购中
    COMPLETED = "completed"              # 采购完成
    CLOSED = "closed"                    # 已关闭
    CANCELLED = "cancelled"              # 已取消


class InStatus(str, Enum):
    """入库/履约状态"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class PayStatus(str, Enum):
    """付款状态"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class PurchaseOrder(Model):
    """采购单主表"""
    id = fields.IntField(pk=True, description="采购单ID")
    purchase_no = fields.CharField(max_length=50, unique=True, description="采购单号")
    purchase_type = fields.CharEnumField(PurchaseType, description="采购类型")
    source_sale_order_id = fields.IntField(null=True, description="关联源销售订单ID")
    source_sale_order_no = fields.CharField(max_length=50, null=True, description="关联源销售订单号")

    # 外键关联 - 替代冗余字段
    brand: fields.ForeignKeyNullableRelation["Brand"] = fields.ForeignKeyField(
        "models.Brand", related_name="purchase_orders", null=True, description="品牌"
    )

    # 保留的字段
    supplier_id = fields.IntField(null=True, description="供应商ID")
    supplier_name = fields.CharField(max_length=200, null=True, description="供应商名称（快照）")
    purchase_user_id = fields.IntField(null=True, description="采购员用户ID")
    purchase_status = fields.CharEnumField(PurchaseStatus, default=PurchaseStatus.PENDING_REVIEW, description="采购单状态")
    in_status = fields.CharEnumField(InStatus, default=InStatus.NONE, description="入库状态")
    pay_status = fields.CharEnumField(PayStatus, default=PayStatus.NONE, description="付款状态")
    total_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="物料不含税总金额")
    freight_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="运费总金额")
    tax_rate = fields.DecimalField(max_digits=5, decimal_places=4, default=0.13, description="税率")
    tax_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="税额")
    total_tax_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="含税总金额")
    expect_arrive_date = fields.DateField(null=True, description="预计到货日期")
    settle_type = fields.CharField(max_length=50, null=True, description="结算方式")
    remark = fields.TextField(null=True, description="备注")
    # 物流信息
    logistics_company = fields.CharField(max_length=100, null=True, description="物流公司")
    logistics_no = fields.CharField(max_length=100, null=True, description="物流单号")
    source_purchase_order_id = fields.CharField(max_length=100, null=True, description="采购源订单ID")
    creator_id = fields.IntField(null=True, description="创建人ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "purchase_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.purchase_no}"

    async def to_dict(self):
        """转换为字典格式，通过关联查询返回品牌名称"""
        brand = None
        if self.brand_id:
            try:
                brand = self.brand
                if brand is None or not hasattr(brand, 'id'):
                    brand = await self.brand
            except TypeError:
                brand = await self.brand

        return {
            "id": self.id,
            "purchase_no": self.purchase_no,
            "purchase_type": self.purchase_type.value if self.purchase_type else None,
            "source_sale_order_id": self.source_sale_order_id,
            "source_sale_order_no": self.source_sale_order_no,
            "brand_id": self.brand_id,
            "brand_name": brand.name if brand else None,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "purchase_user_id": self.purchase_user_id,
            "purchase_status": self.purchase_status.value if self.purchase_status else None,
            "in_status": self.in_status.value if self.in_status else None,
            "pay_status": self.pay_status.value if self.pay_status else None,
            "total_amt": float(self.total_amt),
            "freight_amt": float(self.freight_amt),
            "tax_rate": float(self.tax_rate),
            "tax_amt": float(self.tax_amt),
            "total_tax_amt": float(self.total_tax_amt),
            "expect_arrive_date": self.expect_arrive_date.isoformat() if self.expect_arrive_date else None,
            "settle_type": self.settle_type,
            "remark": self.remark,
            "logistics_company": self.logistics_company,
            "logistics_no": self.logistics_no,
            "source_purchase_order_id": self.source_purchase_order_id,
            "creator_id": self.creator_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PurchaseOrderItem(Model):
    """采购单明细"""
    id = fields.IntField(pk=True, description="明细ID")
    purchase_order = fields.ForeignKeyField("models.PurchaseOrder", related_name="items", on_delete=fields.CASCADE)
    row_no = fields.IntField(description="行号")

    # 外键关联 - spec 关联 product，product 关联 brand
    spec: fields.ForeignKeyNullableRelation["ProductSpec"] = fields.ForeignKeyField(
        "models.ProductSpec", related_name="purchase_order_items", null=True, description="规格"
    )
    warehouse: fields.ForeignKeyNullableRelation["Warehouse"] = fields.ForeignKeyField(
        "models.Warehouse", related_name="purchase_order_items", null=True, description="仓库"
    )

    # 保留的字段（冗余，用于兼容）
    product_id = fields.IntField(null=True, description="商品ID（冗余，通过 spec 获取）")
    brand_id = fields.IntField(null=True, description="品牌ID（冗余，通过 spec 获取）")

    purchase_qty = fields.IntField(description="采购数量")
    purchase_price = fields.DecimalField(max_digits=12, decimal_places=2, description="采购单价")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣系数")
    amt = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="行金额")
    in_qty = fields.IntField(default=0, description="已入库数量")
    return_qty = fields.IntField(default=0, description="已退货数量")
    source_sale_row_no = fields.IntField(null=True, description="关联源销售单明细行号")
    source_sale_order_item_id = fields.IntField(null=True, description="关联销售订单明细ID")
    shipping_method = fields.CharField(max_length=50, null=True, description="发货方式")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "purchase_order_items"
        ordering = ["row_no"]

    async def to_dict(self):
        """转换为字典格式，通过关联查询返回名称

        注意：如果使用 select_related 预加载了关联数据，self.spec、self.warehouse 等
        会直接返回对象而不是协程
        """
        # 获取 spec
        spec = None
        if self.spec_id:
            try:
                spec = self.spec
                if spec is None or not hasattr(spec, 'id'):
                    spec = await self.spec
            except TypeError:
                spec = await self.spec

        # 获取 warehouse
        warehouse = None
        if self.warehouse_id:
            try:
                warehouse = self.warehouse
                if warehouse is None or not hasattr(warehouse, 'id'):
                    warehouse = await self.warehouse
            except TypeError:
                warehouse = await self.warehouse

        # 通过 spec 获取 product 和 brand
        product = None
        brand = None
        if spec:
            try:
                product = spec.product
                if product is None or not hasattr(product, 'id'):
                    product = await spec.product
            except (TypeError, AttributeError):
                if hasattr(spec, 'product_id') and spec.product_id:
                    product = await spec.product

            if product:
                try:
                    brand = product.brand
                    if brand is None or not hasattr(brand, 'id'):
                        brand = await product.brand
                except (TypeError, AttributeError):
                    if hasattr(product, 'brand_id') and product.brand_id:
                        brand = await product.brand

        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "row_no": self.row_no,
            "product_id": product.id if product else self.product_id,
            "product_code": product.product_code if product else None,
            "product_name": product.name if product else None,
            "spec_id": self.spec_id,
            "spec_code": spec.spec_code if spec else None,
            "brand_id": brand.id if brand else self.brand_id,
            "brand_name": brand.name if brand else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": warehouse.name if warehouse else None,
            "purchase_qty": self.purchase_qty,
            "purchase_price": float(self.purchase_price),
            "discount": float(self.discount),
            "amt": float(self.amt) if self.amt else None,
            "in_qty": self.in_qty,
            "return_qty": self.return_qty,
            "source_sale_row_no": self.source_sale_row_no,
            "shipping_method": self.shipping_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }