"""
销售订单管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model
from enum import Enum


class OrderStatus(str, Enum):
    """订单状态枚举"""
    DRAFT = "draft"
    PENDING = "pending"  # 新增：待审核
    AUDITED = "audited"
    PARTIALLY_PUSHED_TO_PURCHASE = "partially_pushed_to_purchase"
    PUSHED_TO_PURCHASE = "pushed_to_purchase"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    """发货状态枚举"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class ReceiveStatus(str, Enum):
    """收货状态枚举"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class InvoiceStatus(str, Enum):
    """开票状态枚举"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"


class ShippingMethod(str, Enum):
    """发货方式枚举"""
    DIRECT = "direct"      # 直运
    WAREHOUSE = "warehouse"  # 仓库发货


class SalesOrder(Model):
    """销售订单主表"""
    id = fields.IntField(pk=True, description="订单ID")
    order_no = fields.CharField(max_length=50, unique=True, description="订单号")
    order_date = fields.DateField(description="订单日期")
    customer_id = fields.IntField(description="客户ID")
    customer_name = fields.CharField(max_length=200, description="客户名称")
    sale_user_id = fields.IntField(null=True, description="销售人员ID")
    sale_user_name = fields.CharField(max_length=100, null=True, description="销售人员名称")
    order_status = fields.CharEnumField(OrderStatus, default=OrderStatus.DRAFT, description="订单状态")
    delivery_status = fields.CharEnumField(DeliveryStatus, default=DeliveryStatus.NONE, description="发货状态")
    receive_status = fields.CharEnumField(ReceiveStatus, default=ReceiveStatus.NONE, description="收货状态")
    invoice_status = fields.CharEnumField(InvoiceStatus, default=InvoiceStatus.NONE, description="开票状态")
    total_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="商品总金额（未税）")
    tax_rate = fields.DecimalField(max_digits=5, decimal_places=4, default=0.13, description="税率")
    tax_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="税额")
    total_tax_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="含税总金额")
    total_discount_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="整单折扣金额")
    expect_deliver_date = fields.DateField(null=True, description="期望交货日")
    settle_type = fields.CharField(max_length=50, null=True, description="结算方式")
    remark = fields.TextField(null=True, description="备注")
    creator_id = fields.IntField(null=True, description="创建人ID")
    creator_name = fields.CharField(max_length=100, null=True, description="创建人名称")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "sales_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order_no}"

    def to_dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "sale_user_id": self.sale_user_id,
            "sale_user_name": self.sale_user_name,
            "order_status": self.order_status.value if self.order_status else None,
            "delivery_status": self.delivery_status.value if self.delivery_status else None,
            "receive_status": self.receive_status.value if self.receive_status else None,
            "invoice_status": self.invoice_status.value if self.invoice_status else None,
            "total_amt": float(self.total_amt),
            "tax_rate": float(self.tax_rate),
            "tax_amt": float(self.tax_amt),
            "total_tax_amt": float(self.total_tax_amt),
            "total_discount_amt": float(self.total_discount_amt),
            "expect_deliver_date": self.expect_deliver_date.isoformat() if self.expect_deliver_date else None,
            "settle_type": self.settle_type,
            "remark": self.remark,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SalesOrderItem(Model):
    """销售订单明细"""
    id = fields.IntField(pk=True, description="明细ID")
    sales_order = fields.ForeignKeyField("models.SalesOrder", related_name="items", on_delete=fields.CASCADE)
    row_no = fields.IntField(description="行号")
    product_id = fields.IntField(null=True, description="商品ID")
    product_code = fields.CharField(max_length=50, null=True, description="商品编码")
    product_name = fields.CharField(max_length=200, null=True, description="商品名称")
    spec_id = fields.IntField(null=True, description="规格ID")
    spec_code = fields.CharField(max_length=50, null=True, description="规格编码")
    brand_id = fields.IntField(null=True, description="品牌ID")
    brand_name = fields.CharField(max_length=100, null=True, description="品牌名称")
    warehouse_id = fields.IntField(null=True, description="仓库ID")
    warehouse_name = fields.CharField(max_length=100, null=True, description="仓库名称")
    qty = fields.IntField(description="订购数量")
    price = fields.DecimalField(max_digits=12, decimal_places=2, description="原始单价")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣率")
    discounted_price = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="折后单价")
    amt = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="行金额")
    shipping_method = fields.CharEnumField(ShippingMethod, description="发货方式")
    pushed = fields.BooleanField(default=False, description="是否已下推采购")
    out_qty = fields.IntField(default=0, description="已发货数量")
    return_qty = fields.IntField(default=0, description="已退货数量")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "sales_order_items"
        ordering = ["row_no"]
        unique_together = ("sales_order", "row_no")

    def to_dict(self):
        return {
            "id": self.id,
            "sales_order_id": self.sales_order_id,
            "row_no": self.row_no,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code,
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "qty": self.qty,
            "price": float(self.price),
            "discount": float(self.discount),
            "discounted_price": float(self.discounted_price) if self.discounted_price else None,
            "amt": float(self.amt) if self.amt else None,
            "shipping_method": self.shipping_method.value if self.shipping_method else None,
            "pushed": self.pushed,
            "out_qty": self.out_qty,
            "return_qty": self.return_qty,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SalesDeliverInfo(Model):
    """发货信息"""
    id = fields.IntField(pk=True, description="发货信息ID")
    sales_order = fields.ForeignKeyField("models.SalesOrder", related_name="deliver_infos", on_delete=fields.CASCADE)
    addr = fields.CharField(max_length=500, null=True, description="详细地址")
    province = fields.CharField(max_length=50, null=True, description="省")
    city = fields.CharField(max_length=50, null=True, description="市")
    person_name = fields.CharField(max_length=100, null=True, description="收货人")
    person_tel = fields.CharField(max_length=20, null=True, description="联系电话")

    class Meta:
        table = "sales_deliver_infos"

    def to_dict(self):
        return {
            "id": self.id,
            "addr": self.addr,
            "province": self.province,
            "city": self.city,
            "person_name": self.person_name,
            "person_tel": self.person_tel,
        }