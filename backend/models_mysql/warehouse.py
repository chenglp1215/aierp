"""
仓库管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class Warehouse(Model):
    """仓库模型"""
    id = fields.IntField(pk=True, description="仓库ID")
    warehouse_code = fields.CharField(max_length=50, unique=True, description="仓库编码")
    name = fields.CharField(max_length=100, description="仓库名称")
    address = fields.CharField(max_length=500, description="仓库地址")
    manager_id = fields.IntField(null=True, description="仓库管理员用户ID")
    manager_name = fields.CharField(max_length=100, null=True, description="仓库管理员姓名")
    status = fields.CharField(max_length=20, default="active", description="仓库状态: active/inactive/maintenance")
    description = fields.CharField(max_length=500, null=True, description="仓库描述")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "warehouses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.warehouse_code}: {self.name}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "warehouse_code": self.warehouse_code,
            "name": self.name,
            "address": self.address,
            "manager_id": self.manager_id,
            "manager_name": self.manager_name,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Stock(Model):
    """库存模型"""
    id = fields.IntField(pk=True, description="库存ID")
    warehouse_id = fields.IntField(description="仓库ID")
    product_id = fields.IntField(description="商品ID")
    product_code = fields.CharField(max_length=50, description="商品编号")
    product_name = fields.CharField(max_length=200, description="商品名称")
    spec_id = fields.IntField(description="规格ID")
    spec_code = fields.CharField(max_length=50, description="规格编号")
    quantity = fields.FloatField(default=0, description="当前库存数量")
    min_stock = fields.FloatField(default=0, description="最小库存警告阈值")
    max_stock = fields.FloatField(default=0, description="最大库存警告阈值")
    status = fields.CharField(max_length=20, default="normal", description="库存状态: normal/low_stock/out_of_stock/overstock")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "stocks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Stock {self.id}: {self.product_name} - {self.spec_code}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code,
            "quantity": self.quantity,
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InboundBatch(Model):
    """入库批次模型"""
    id = fields.IntField(pk=True, description="入库批次ID")
    warehouse_id = fields.IntField(description="仓库ID")
    product_id = fields.IntField(description="商品ID")
    product_code = fields.CharField(max_length=50, description="商品编号")
    product_name = fields.CharField(max_length=200, description="商品名称")
    spec_id = fields.IntField(description="规格ID")
    spec_code = fields.CharField(max_length=50, description="规格编号")
    stock_id = fields.IntField(description="库存ID")
    quantity = fields.FloatField(description="入库数量")
    user_id = fields.IntField(description="操作用户ID")
    user_name = fields.CharField(max_length=100, description="操作用户名")
    remarks = fields.CharField(max_length=500, null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "inbound_batches"
        ordering = ["-created_at"]

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code,
            "stock_id": self.stock_id,
            "quantity": self.quantity,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OutboundBatch(Model):
    """出库批次模型"""
    id = fields.IntField(pk=True, description="出库批次ID")
    warehouse_id = fields.IntField(description="仓库ID")
    product_id = fields.IntField(description="商品ID")
    product_code = fields.CharField(max_length=50, description="商品编号")
    product_name = fields.CharField(max_length=200, description="商品名称")
    spec_id = fields.IntField(description="规格ID")
    spec_code = fields.CharField(max_length=50, description="规格编号")
    stock_id = fields.IntField(description="库存ID")
    quantity = fields.FloatField(description="出库数量")
    user_id = fields.IntField(description="操作用户ID")
    user_name = fields.CharField(max_length=100, description="操作用户名")
    remarks = fields.CharField(max_length=500, null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "outbound_batches"
        ordering = ["-created_at"]

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code,
            "stock_id": self.stock_id,
            "quantity": self.quantity,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }