"""
客户管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class Customer(Model):
    """客户模型"""
    id = fields.IntField(pk=True, description="客户ID")
    customer_code = fields.CharField(max_length=50, unique=True, description="客户编码")
    customer_name = fields.CharField(max_length=200, description="客户名称")
    customer_type = fields.CharField(max_length=20, default="terminal", description="客户类型: terminal=终端, dealer=经销商")
    customer_status = fields.IntField(default=1, description="客户状态: 1=正常, 2=公共池")
    sales_user_id = fields.IntField(null=True, description="业务员ID")
    sales_user_name = fields.CharField(max_length=50, null=True, description="业务员名称")
    settlement_method = fields.IntField(default=1, description="结算方式: 1=月结, 2=现结, 3=预付")
    account_balance = fields.DecimalField(max_digits=18, decimal_places=2, default=0, description="账户余额")
    debt_total = fields.DecimalField(max_digits=18, decimal_places=2, default=0, description="欠款总额")
    credit_limit = fields.DecimalField(max_digits=18, decimal_places=2, default=0, description="信用额度")
    credit_days = fields.IntField(default=0, description="账期天数")
    is_overdue = fields.IntField(default=0, description="是否超账期: 0=否, 1=是")
    last_order_time = fields.DatetimeField(null=True, description="尾单时间")
    total_order_amount = fields.DecimalField(max_digits=18, decimal_places=2, default=0, description="成单金额")
    member_account = fields.CharField(max_length=100, null=True, description="会员账号")
    contact_person = fields.CharField(max_length=50, null=True, description="联系人")
    contact_phone = fields.CharField(max_length=20, null=True, description="联系电话")
    email = fields.CharField(max_length=100, null=True, description="邮箱地址")
    province = fields.CharField(max_length=50, null=True, description="省")
    city = fields.CharField(max_length=50, null=True, description="市")
    district = fields.CharField(max_length=50, null=True, description="区")
    address = fields.CharField(max_length=200, null=True, description="详细地址")
    remark = fields.TextField(null=True, description="备注")
    created_by = fields.IntField(null=True, description="创建人ID")
    default_shipping_address_id = fields.IntField(null=True, description="默认收货地址ID")
    default_invoice_info_id = fields.IntField(null=True, description="默认开票信息ID")
    default_tax_rate = fields.DecimalField(max_digits=5, decimal_places=2, null=True, description="默认税率(百分比,如13表示13%)")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "customers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer_code}: {self.customer_name}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "customer_code": self.customer_code,
            "customer_name": self.customer_name,
            "customer_type": self.customer_type,
            "customer_status": self.customer_status,
            "sales_user_id": self.sales_user_id,
            "sales_user_name": self.sales_user_name,
            "settlement_method": self.settlement_method,
            "account_balance": float(self.account_balance) if self.account_balance else 0,
            "debt_total": float(self.debt_total) if self.debt_total else 0,
            "credit_limit": float(self.credit_limit) if self.credit_limit else 0,
            "credit_days": self.credit_days,
            "is_overdue": self.is_overdue,
            "last_order_time": self.last_order_time.isoformat() if self.last_order_time else None,
            "total_order_amount": float(self.total_order_amount) if self.total_order_amount else 0,
            "member_account": self.member_account,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "email": self.email,
            "province": self.province,
            "city": self.city,
            "district": self.district,
            "address": self.address,
            "remark": self.remark,
            "created_by": self.created_by,
            "default_shipping_address_id": self.default_shipping_address_id,
            "default_invoice_info_id": self.default_invoice_info_id,
            "default_tax_rate": float(self.default_tax_rate) if self.default_tax_rate else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CustomerResearchGroup(Model):
    """客户课题组模型"""
    id = fields.IntField(pk=True, description="课题组ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="research_groups", on_delete=fields.CASCADE, description="客户"
    )
    research_group_name = fields.CharField(max_length=100, description="课题组名称")
    research_leader = fields.CharField(max_length=50, null=True, description="课题组负责人")
    contact_phone = fields.CharField(max_length=20, null=True, description="联系电话")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "customer_research_group"
        ordering = ["id"]

    def __str__(self):
        return f"{self.research_group_name}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "research_group_name": self.research_group_name,
            "research_leader": self.research_leader,
            "contact_phone": self.contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InvoiceInfo(Model):
    """开票信息模型"""
    id = fields.IntField(pk=True, description="开票信息ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="invoice_infos", on_delete=fields.CASCADE, description="客户"
    )
    invoice_title = fields.CharField(max_length=200, description="开票抬头")
    tax_number = fields.CharField(max_length=50, description="税务编码")
    bank_name = fields.CharField(max_length=200, description="银行开户行")
    bank_account = fields.CharField(max_length=50, description="银行账号")
    address_phone = fields.CharField(max_length=200, null=True, description="地址、电话")
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
            "tax_number": self.tax_number,
            "bank_name": self.bank_name,
            "bank_account": self.bank_account,
            "address_phone": self.address_phone,
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
    receiver = fields.CharField(max_length=50, description="收货人")
    phone = fields.CharField(max_length=20, description="联系电话")
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
        return f"{self.receiver} - {self.address}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "receiver": self.receiver,
            "phone": self.phone,
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