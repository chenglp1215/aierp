"""
客户管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class Customer(Model):
    """客户模型"""
    id = fields.IntField(pk=True, description="客户ID")
    customer_code = fields.CharField(max_length=50, unique=True, description="客户编码")
    name = fields.CharField(max_length=200, description="客户名称")
    customer_type = fields.CharField(max_length=20, description="客户类型: terminal/dealer")
    research_group = fields.CharField(max_length=200, null=True, description="课题组信息")
    contact_person = fields.CharField(max_length=100, null=True, description="联系人")
    contact_phone = fields.CharField(max_length=20, null=True, description="联系电话")
    contact_email = fields.CharField(max_length=100, null=True, description="电子邮箱")
    sales_user_id = fields.IntField(null=True, description="销售人ID")
    sales_user_name = fields.CharField(max_length=100, null=True, description="销售人名称")
    status = fields.CharField(max_length=20, default="normal", description="客户状态: normal/inactive/blacklisted")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "customers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer_code}: {self.name}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "customer_code": self.customer_code,
            "name": self.name,
            "customer_type": self.customer_type,
            "research_group": self.research_group,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "sales_user_id": self.sales_user_id,
            "sales_user_name": self.sales_user_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InvoiceInfo(Model):
    """开票信息模型"""
    id = fields.IntField(pk=True, description="开票信息ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="invoice_infos", on_delete=fields.CASCADE, description="客户"
    )
    invoice_title = fields.CharField(max_length=200, description="开票抬头")
    invoice_type = fields.CharField(max_length=50, description="开票类型")
    tax_number = fields.CharField(max_length=50, description="税务编码")
    bank_name = fields.CharField(max_length=200, description="银行开户行")
    bank_account = fields.CharField(max_length=50, description="银行账号")
    is_default = fields.BooleanField(default=False, description="是否默认")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "invoice_infos"
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.invoice_title}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "invoice_title": self.invoice_title,
            "invoice_type": self.invoice_type,
            "tax_number": self.tax_number,
            "bank_name": self.bank_name,
            "bank_account": self.bank_account,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ShippingAddress(Model):
    """收货地址模型"""
    id = fields.IntField(pk=True, description="收货地址ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="shipping_addresses", on_delete=fields.CASCADE, description="客户"
    )
    recipient_name = fields.CharField(max_length=100, description="收货人")
    recipient_phone = fields.CharField(max_length=20, description="收货电话")
    province = fields.CharField(max_length=100, description="省份")
    province_code = fields.CharField(max_length=20, null=True, description="省份代码")
    city = fields.CharField(max_length=100, description="城市")
    city_code = fields.CharField(max_length=20, null=True, description="城市代码")
    district = fields.CharField(max_length=100, null=True, description="区县")
    address = fields.CharField(max_length=500, description="详细地址")
    is_default = fields.BooleanField(default=False, description="是否默认")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "shipping_addresses"
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.recipient_name} - {self.address}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "recipient_name": self.recipient_name,
            "recipient_phone": self.recipient_phone,
            "province": self.province,
            "province_code": self.province_code,
            "city": self.city,
            "city_code": self.city_code,
            "district": self.district,
            "address": self.address,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CustomerDiscount(Model):
    """客户折扣模型"""
    id = fields.IntField(pk=True, description="折扣ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="discounts", on_delete=fields.CASCADE, description="客户"
    )
    brand_id = fields.IntField(description="品牌ID")
    brand_name = fields.CharField(max_length=100, null=True, description="品牌名称")
    discount_value = fields.FloatField(description="折扣值")
    is_active = fields.BooleanField(default=True, description="是否生效")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "customer_discounts"
        ordering = ["-created_at"]
        unique_together = ("customer", "brand_id")

    def __str__(self):
        return f"Customer {self.customer_id} - Brand {self.brand_id}: {self.discount_value}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "discount_value": self.discount_value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
