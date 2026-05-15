"""
订单状态流转记录 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class OrderStatusFlow(Model):
    """订单状态流转记录"""
    id = fields.IntField(pk=True, description="记录ID")
    order_no = fields.CharField(max_length=50, description="订单号")
    order_type = fields.CharField(max_length=20, description="订单类型: sales/purchase")
    field = fields.CharField(max_length=50, description="状态字段名")
    old_value = fields.CharField(max_length=50, null=True, description="旧值")
    new_value = fields.CharField(max_length=50, description="新值")
    operator = fields.CharField(max_length=100, default="system", description="操作人")
    operate_time = fields.DatetimeField(auto_now_add=True, description="操作时间")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "order_status_flows"
        ordering = ["operate_time"]
        indexes = [("order_no",)]

    def to_dict(self):
        return {
            "id": self.id,
            "order_no": self.order_no,
            "order_type": self.order_type,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "operator": self.operator,
            "operate_time": self.operate_time.isoformat() if self.operate_time else None,
            "remark": self.remark,
        }