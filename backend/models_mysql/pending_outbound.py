"""
待出库单管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model
from enum import Enum


class PendingOutboundStatus(str, Enum):
    """出库单状态"""
    PENDING = "pending"      # 未出库
    OUTBOUND = "outbound"    # 已出库
    SHIPPED = "shipped"      # 已发货
    CANCELLED = "cancelled"  # 已取消


class OutboundType(str, Enum):
    """出库类型"""
    ORDER_OUTBOUND = "order_outbound"      # 订单出库
    TRANSFER_OUTBOUND = "transfer_outbound"  # 调拨出库


class PendingOutboundOrder(Model):
    """待出库单"""
    id = fields.IntField(pk=True, description="待出库单ID")
    pending_no = fields.CharField(max_length=50, unique=True, description="待出库单号")
    sales_order_id = fields.IntField(description="关联销售订单ID")
    sales_order_no = fields.CharField(max_length=50, description="关联销售订单号")
    sales_order_item_id = fields.IntField(description="关联销售订单明细ID")
    row_no = fields.IntField(description="行号")

    warehouse_id = fields.IntField(description="仓库ID")
    warehouse_name = fields.CharField(max_length=100, description="仓库名称")
    spec_id = fields.IntField(description="规格ID")
    product_code = fields.CharField(max_length=50, description="商品编码")
    spec_code = fields.CharField(max_length=50, description="规格编码")

    locked_qty = fields.IntField(description="锁定数量")
    out_qty = fields.IntField(default=0, description="已出库数量")
    status = fields.CharEnumField(PendingOutboundStatus, default=PendingOutboundStatus.PENDING, description="状态")
    outbound_type = fields.CharEnumField(OutboundType, default=OutboundType.ORDER_OUTBOUND, description="出库类型")

    # 收货地址信息
    province = fields.CharField(max_length=100, null=True, description="省份")
    city = fields.CharField(max_length=100, null=True, description="城市")
    address = fields.CharField(max_length=500, null=True, description="详细地址")
    recipient_name = fields.CharField(max_length=100, null=True, description="收货人")
    recipient_phone = fields.CharField(max_length=20, null=True, description="收货电话")

    remark = fields.TextField(null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "pending_outbound_orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.pending_no}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "pending_no": self.pending_no,
            "sales_order_id": self.sales_order_id,
            "sales_order_no": self.sales_order_no,
            "sales_order_item_id": self.sales_order_item_id,
            "row_no": self.row_no,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "spec_id": self.spec_id,
            "product_code": self.product_code,
            "spec_code": self.spec_code,
            "locked_qty": self.locked_qty,
            "out_qty": self.out_qty,
            "status": self.status.value if self.status else None,
            "outbound_type": self.outbound_type.value if self.outbound_type else None,
            "province": self.province,
            "city": self.city,
            "address": self.address,
            "recipient_name": self.recipient_name,
            "recipient_phone": self.recipient_phone,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
