"""
盘库管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class StockCheckBatch(Model):
    """盘库批次模型"""
    id = fields.IntField(pk=True, description="批次ID")
    batch_code = fields.CharField(max_length=50, unique=True, description="批次编号")
    warehouse_id = fields.IntField(description="仓库ID")
    warehouse_name = fields.CharField(max_length=100, description="仓库名称")
    check_type = fields.CharField(max_length=20, description="盘库类型: single/batch")
    total_count = fields.IntField(default=0, description="总记录数")
    success_count = fields.IntField(default=0, description="成功数")
    fail_count = fields.IntField(default=0, description="失败数")
    user_id = fields.IntField(description="操作用户ID")
    user_name = fields.CharField(max_length=100, description="操作用户名")
    remarks = fields.CharField(max_length=500, null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "stock_check_batches"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.batch_code}: {self.warehouse_name}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "batch_code": self.batch_code,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "check_type": self.check_type,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StockCheckRecord(Model):
    """盘库记录模型"""
    id = fields.IntField(pk=True, description="记录ID")
    batch_id = fields.IntField(description="批次ID")
    stock_id = fields.IntField(null=True, description="库存ID（新建时为空）")
    warehouse_id = fields.IntField(description="仓库ID")
    product_id = fields.IntField(description="商品ID")
    product_code = fields.CharField(max_length=50, description="商品编号")
    product_name = fields.CharField(max_length=200, description="商品名称")
    spec_id = fields.IntField(description="规格ID")
    spec_code = fields.CharField(max_length=50, description="规格编号")
    before_quantity = fields.FloatField(description="盘点前数量")
    check_quantity = fields.FloatField(description="盘点数量")
    difference = fields.FloatField(description="差异")
    is_new_stock = fields.BooleanField(default=False, description="是否新建库存")
    user_id = fields.IntField(description="操作用户ID")
    user_name = fields.CharField(max_length=100, description="操作用户名")
    remarks = fields.CharField(max_length=500, null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "stock_check_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Check {self.id}: {self.spec_code} - {self.difference}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "stock_id": self.stock_id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code,
            "before_quantity": self.before_quantity,
            "check_quantity": self.check_quantity,
            "difference": self.difference,
            "is_new_stock": self.is_new_stock,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
