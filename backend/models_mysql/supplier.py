"""
供应商管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class Supplier(Model):
    """供应商模型"""
    id = fields.IntField(pk=True, description="供应商ID")
    name = fields.CharField(max_length=200, unique=True, description="供应商名称")
    contact_person = fields.CharField(max_length=100, null=True, description="联系人")
    contact_phone = fields.CharField(max_length=50, null=True, description="联系电话")
    contact_email = fields.CharField(max_length=200, null=True, description="联系邮箱")
    address = fields.CharField(max_length=500, null=True, description="地址")
    remark = fields.TextField(null=True, description="备注")
    is_active = fields.BooleanField(default=True, description="是否激活")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "suppliers"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "remark": self.remark,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SupplierBankAccount(Model):
    """供应商银行账户模型"""
    id = fields.IntField(pk=True, description="账户ID")
    supplier: fields.ForeignKeyRelation[Supplier] = fields.ForeignKeyField(
        "models.Supplier", related_name="bank_accounts", on_delete=fields.CASCADE, description="供应商"
    )
    bank_name = fields.CharField(max_length=200, null=True, description="开户行")
    account_name = fields.CharField(max_length=200, null=True, description="账户名")
    account_no = fields.CharField(max_length=50, null=True, description="账号")
    is_default = fields.BooleanField(default=False, description="是否默认")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "supplier_bank_accounts"
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_no}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "bank_name": self.bank_name,
            "account_name": self.account_name,
            "account_no": self.account_no,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SupplierBrand(Model):
    """供应商品牌关联模型"""
    id = fields.IntField(pk=True, description="关联ID")
    supplier: fields.ForeignKeyRelation[Supplier] = fields.ForeignKeyField(
        "models.Supplier", related_name="supplied_brands", on_delete=fields.CASCADE, description="供应商"
    )
    brand_id = fields.IntField(description="品牌ID")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣率")
    is_priority = fields.BooleanField(default=False, description="是否优先")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "supplier_brands"
        ordering = ["-is_priority", "id"]
        unique_together = ("supplier", "brand_id")

    def __str__(self):
        return f"Supplier {self.supplier_id} - Brand {self.brand_id}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "brand_id": self.brand_id,
            "discount": float(self.discount),
            "is_priority": self.is_priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }