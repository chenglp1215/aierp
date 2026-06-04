"""
销售订单管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model
from enum import Enum


class OrderStatus(str, Enum):
    """订单状态枚举"""
    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待审核
    AUDITED = "audited"  # 审核通过
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class PushStatus(str, Enum):
    """下推状态枚举"""
    NONE = "none"  # 未下推
    PARTIAL = "partial"  # 部分下推
    FULL = "full"  # 已下推
    NOT_NEEDED = "not_needed"  # 无需下推


class DeliveryStatus(str, Enum):
    """发货状态枚举"""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    NO_NEED = "no_need"  # 无需发货
    HAS_RETURN = "has_return"  # 有退货


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
    NO_NEED = "no_need"  # 无需开票


class CostType(str, Enum):
    """成本类型枚举"""
    PURCHASE = "purchase"      # 采购成本
    FREIGHT = "freight"        # 运费
    TRANSFER = "transfer"      # 调货费
    OTHER = "other"            # 其他


class CostSourceType(str, Enum):
    """成本来源类型枚举"""
    PURCHASE_ORDER = "purchase_order"  # 采购单
    OUTBOUND = "outbound"              # 出库发货
    MANUAL = "manual"                  # 手动添加


class FinanceStatus(str, Enum):
    """财务状态枚举"""
    UNPAID = "unpaid"                  # 未付款
    PARTIAL_PAID = "partial_paid"      # 部分付款
    PAID = "paid"                      # 已付款
    RECONCILED = "reconciled"          # 已对账
    NO_NEED = "no_need"                # 无需付款


class ShippingMethod(str, Enum):
    """发货方式枚举"""
    DIRECT = "direct"      # 直运
    WAREHOUSE = "warehouse"  # 仓库发货
    WAREHOUSE_PICKUP = "warehouse_pickup"  # 仓库自提
    LOGISTICS = "logistics"  # 物流
    DELIVERY = "delivery"  # 送货


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
    finance_status = fields.CharEnumField(FinanceStatus, default=FinanceStatus.UNPAID, description="财务状态")
    push_status = fields.CharEnumField(PushStatus, null=True, description="下推状态")
    total_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="商品总金额（未税）")
    tax_rate = fields.DecimalField(max_digits=5, decimal_places=4, default=0.13, description="税率")
    tax_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="税额")
    total_tax_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="含税总金额")
    total_discount_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="整单折扣金额")
    freight_amt = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="运费金额")
    expect_deliver_date = fields.DateField(null=True, description="期望交货日")
    settle_type = fields.CharField(max_length=50, null=True, description="结算方式")
    remark = fields.TextField(null=True, description="备注")
    third_party_platform = fields.CharField(max_length=50, null=True, description="第三方平台")
    platform_order_no = fields.CharField(max_length=100, null=True, description="平台订单号")
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
            "finance_status": self.finance_status.value if self.finance_status else None,
            "push_status": self.push_status.value if self.push_status else None,
            "total_amt": float(self.total_amt),
            "tax_rate": float(self.tax_rate),
            "tax_amt": float(self.tax_amt),
            "total_tax_amt": float(self.total_tax_amt),
            "total_discount_amt": float(self.total_discount_amt),
            "freight_amt": float(self.freight_amt) if self.freight_amt else 0.00,
            "expect_deliver_date": self.expect_deliver_date.isoformat() if self.expect_deliver_date else None,
            "settle_type": self.settle_type,
            "remark": self.remark,
            "third_party_platform": self.third_party_platform,
            "platform_order_no": self.platform_order_no,
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

    # 外键关联 - spec 关联 product，product 关联 brand，只需 spec 和 warehouse
    spec: fields.ForeignKeyNullableRelation["ProductSpec"] = fields.ForeignKeyField(
        "models.ProductSpec", related_name="sales_order_items", null=True, description="规格"
    )
    warehouse: fields.ForeignKeyNullableRelation["Warehouse"] = fields.ForeignKeyField(
        "models.Warehouse", related_name="sales_order_items", null=True, description="仓库"
    )

    # 保留的字段（历史快照）
    product_code = fields.CharField(max_length=50, null=True, description="商品编码（快照）")
    spec_code = fields.CharField(max_length=50, null=True, description="规格编码（快照）")

    qty = fields.IntField(description="订购数量")
    price = fields.DecimalField(max_digits=12, decimal_places=2, description="原始单价")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣率")
    discounted_price = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="折后单价")
    amt = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="行金额")
    shipping_method = fields.CharEnumField(ShippingMethod, max_length=20, description="发货方式")
    purchase_qty = fields.IntField(default=0, description="需要采购的数量")
    pushed_qty = fields.IntField(default=0, description="已下推采购的数量")
    out_qty = fields.IntField(default=0, description="已发货数量")
    return_qty = fields.IntField(default=0, description="已退货数量")
    exchange_qty = fields.IntField(default=0, description="换货数量")
    supplement_qty = fields.IntField(default=0, description="补货数量")
    tax_rate = fields.DecimalField(max_digits=5, decimal_places=4, default=0.13, description="税率")
    item_remark = fields.TextField(null=True, description="商品备注")
    return_info = fields.CharField(max_length=500, null=True, description="退货信息：格式'退货数量（退货方式，金额）'")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "sales_order_items"
        ordering = ["row_no"]
        unique_together = ("sales_order", "row_no")

    async def to_dict(self):
        """转换为字典格式，通过关联查询返回名称

        注意：如果使用 select_related 预加载了关联数据，self.spec、self.warehouse 等
        会直接返回对象而不是协程
        """
        # 获取 spec - select_related 预加载时直接返回对象，否则需要 await
        spec = None
        if self.spec_id:
            try:
                spec = self.spec  # 如果已预加载，直接返回对象
                if spec is None or not hasattr(spec, 'id'):
                    spec = await self.spec  # 未预加载，需要 await
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
                pass  # self.warehouse 为 None，无法 await

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

        # 发货方式中文映射
        shipping_method_map = {
            ShippingMethod.DIRECT: "直运",
            ShippingMethod.WAREHOUSE: "仓库发货",
            ShippingMethod.WAREHOUSE_PICKUP: "仓库自提",
            ShippingMethod.LOGISTICS: "物流",
            ShippingMethod.DELIVERY: "送货",
        }
        shipping_method_cn = shipping_method_map.get(self.shipping_method) if self.shipping_method else None

        return {
            "id": self.id,
            "sales_order_id": self.sales_order_id,
            "row_no": self.row_no,
            "product_id": product.id if product else None,
            "product_code": self.product_code or (product.product_code if product else None),
            "product_name": product.name if product else None,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code or (spec.spec_code if spec else None),
            "brand_id": brand.id if brand else None,
            "brand_name": brand.name if brand else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": warehouse.name if warehouse else None,
            "qty": self.qty,
            "price": float(self.price),
            "discount": float(self.discount),
            "discounted_price": float(self.discounted_price) if self.discounted_price else None,
            "amt": float(self.amt) if self.amt else None,
            "shipping_method": shipping_method_cn,
            "purchase_qty": self.purchase_qty,
            "pushed_qty": self.pushed_qty,
            "out_qty": self.out_qty,
            "return_qty": self.return_qty,
            "exchange_qty": self.exchange_qty,
            "supplement_qty": self.supplement_qty,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0.13,
            "item_remark": self.item_remark,
            "return_info": self.return_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SalesOrderCostItem(Model):
    """销售订单成本明细"""
    id = fields.IntField(pk=True, description="成本明细ID")
    sales_order = fields.ForeignKeyField("models.SalesOrder", related_name="cost_items", on_delete=fields.CASCADE)
    cost_type = fields.CharEnumField(CostType, description="成本类型")
    amount = fields.DecimalField(max_digits=12, decimal_places=2, description="金额（未税）")
    source_type = fields.CharEnumField(CostSourceType, description="来源类型")
    source_no = fields.CharField(max_length=50, null=True, description="来源单号")
    purchase_order_id = fields.IntField(null=True, description="关联采购单ID")
    pending_outbound_id = fields.IntField(null=True, description="关联待出库单ID")
    remark = fields.TextField(null=True, description="备注")
    creator_id = fields.IntField(null=True, description="创建人ID")
    creator_name = fields.CharField(max_length=100, null=True, description="创建人名称")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "sales_order_cost_items"
        ordering = ["-created_at"]

    def to_dict(self):
        return {
            "id": self.id,
            "sales_order_id": self.sales_order_id,
            "cost_type": self.cost_type.value if self.cost_type else None,
            "amount": float(self.amount),
            "source_type": self.source_type.value if self.source_type else None,
            "source_no": self.source_no,
            "purchase_order_id": self.purchase_order_id,
            "pending_outbound_id": self.pending_outbound_id,
            "remark": self.remark,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
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


class SalesInvoiceInfo(Model):
    """开票信息"""
    id = fields.IntField(pk=True, description="开票信息ID")
    sales_order = fields.ForeignKeyField("models.SalesOrder", related_name="invoice_infos", on_delete=fields.CASCADE)
    invoice_title = fields.CharField(max_length=200, null=True, description="发票抬头")
    invoice_type = fields.CharField(max_length=50, null=True, description="发票类型")
    tax_number = fields.CharField(max_length=50, null=True, description="税号")
    bank_name = fields.CharField(max_length=100, null=True, description="开户银行")
    bank_account = fields.CharField(max_length=50, null=True, description="银行账号")
    address = fields.CharField(max_length=200, null=True, description="注册地址")
    phone = fields.CharField(max_length=20, null=True, description="注册电话")

    class Meta:
        table = "sales_invoice_infos"

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_title": self.invoice_title,
            "invoice_type": self.invoice_type,
            "tax_number": self.tax_number,
            "bank_name": self.bank_name,
            "bank_account": self.bank_account,
            "address": self.address,
            "phone": self.phone,
        }