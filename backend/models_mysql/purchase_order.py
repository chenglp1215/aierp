"""
采购单管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model
from enum import Enum


class PurchaseType(str, Enum):
    """采购类型"""
    DIRECT = "direct"      # 直运采购
    WAREHOUSE = "warehouse"  # 仓库采购


class PurchaseStatus(str, Enum):
    """采购单主流程状态"""
    DRAFT = "draft"
    AUDITED = "audited"
    CLOSED = "closed"
    CANCELLED = "cancelled"


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
    brand_id = fields.IntField(null=True, description="品牌ID")
    brand_name = fields.CharField(max_length=100, null=True, description="品牌名称")
    supplier_id = fields.IntField(null=True, description="供应商ID")
    supplier_name = fields.CharField(max_length=200, null=True, description="供应商名称")
    purchase_user_id = fields.IntField(null=True, description="采购员用户ID")
    purchase_status = fields.CharEnumField(PurchaseStatus, default=PurchaseStatus.DRAFT, description="采购单状态")
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
    creator_id = fields.IntField(null=True, description="创建人ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "purchase_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.purchase_no}"

    def to_dict(self):
        return {
            "id": self.id,
            "purchase_no": self.purchase_no,
            "purchase_type": self.purchase_type.value if self.purchase_type else None,
            "source_sale_order_id": self.source_sale_order_id,
            "source_sale_order_no": self.source_sale_order_no,
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
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
            "creator_id": self.creator_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PurchaseOrderItem(Model):
    """采购单明细"""
    id = fields.IntField(pk=True, description="明细ID")
    purchase_order = fields.ForeignKeyField("models.PurchaseOrder", related_name="items", on_delete=fields.CASCADE)
    row_no = fields.IntField(description="行号")
    product_id = fields.IntField(null=True, description="商品ID")
    spec_id = fields.IntField(null=True, description="规格ID")
    brand_id = fields.IntField(null=True, description="品牌ID")
    brand_name = fields.CharField(max_length=100, null=True, description="品牌名称")
    warehouse_id = fields.IntField(null=True, description="仓库ID")
    warehouse_name = fields.CharField(max_length=100, null=True, description="仓库名称")
    purchase_qty = fields.IntField(description="采购数量")
    purchase_price = fields.DecimalField(max_digits=12, decimal_places=2, description="采购单价")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣系数")
    amt = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="行金额")
    in_qty = fields.IntField(default=0, description="已入库数量")
    return_qty = fields.IntField(default=0, description="已退货数量")
    source_sale_row_no = fields.IntField(null=True, description="关联源销售单明细行号")
    shipping_method = fields.CharField(max_length=50, null=True, description="发货方式")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "purchase_order_items"
        ordering = ["row_no"]

    def to_dict(self):
        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "row_no": self.row_no,
            "product_id": self.product_id,
            "spec_id": self.spec_id,
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
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