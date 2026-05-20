"""
待出库单管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model
from enum import Enum


class PendingOutboundStatus(str, Enum):
    """待出库状态"""
    PENDING = "pending"      # 待出库
    PARTIAL = "partial"      # 部分出库
    FULL = "full"            # 已出库
    CANCELLED = "cancelled"  # 已取消


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
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
