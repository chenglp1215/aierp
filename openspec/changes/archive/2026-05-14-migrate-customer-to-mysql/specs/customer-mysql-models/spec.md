## ADDED Requirements

### Requirement: Customer 模型定义

系统 SHALL 使用 Tortoise ORM 定义 Customer 模型，包含以下字段：
- id: IntField (主键，自增)
- customer_code: CharField(max_length=50, unique=True)
- name: CharField(max_length=200)
- customer_type: CharField(max_length=20) - 枚举值: terminal, dealer
- research_group: CharField(max_length=200, null=True)
- contact_person: CharField(max_length=100, null=True)
- contact_phone: CharField(max_length=20, null=True)
- contact_email: CharField(max_length=100, null=True)
- sales_user_id: IntField(null=True)
- sales_user_name: CharField(max_length=100, null=True)
- status: CharField(max_length=20, default="normal") - 枚举值: normal, inactive, blacklisted
- created_at: DatetimeField(auto_now_add=True)
- updated_at: DatetimeField(auto_now=True)

#### Scenario: 创建客户模型实例
- **WHEN** 使用 Customer.create() 创建客户
- **THEN** 系统自动生成 id、created_at、updated_at 字段

#### Scenario: 查询客户关联数据
- **WHEN** 调用 customer.invoice_infos 或 customer.shipping_addresses
- **THEN** 系统返回关联的开票信息和收货地址列表

---

### Requirement: InvoiceInfo 模型定义

系统 SHALL 使用 Tortoise ORM 定义 InvoiceInfo 模型，包含以下字段：
- id: IntField (主键，自增)
- customer: ForeignKeyField(Customer, related_name="invoice_infos")
- invoice_title: CharField(max_length=200)
- invoice_type: CharField(max_length=50)
- tax_number: CharField(max_length=50)
- bank_name: CharField(max_length=200)
- bank_account: CharField(max_length=50)
- is_default: BooleanField(default=False)
- created_at: DatetimeField(auto_now_add=True)
- updated_at: DatetimeField(auto_now=True)

#### Scenario: 创建开票信息
- **WHEN** 为客户创建新的开票信息
- **THEN** 系统关联到正确的客户，并设置 is_default 字段

#### Scenario: 级联删除
- **WHEN** 删除客户
- **THEN** 系统自动删除该客户的所有开票信息

---

### Requirement: ShippingAddress 模型定义

系统 SHALL 使用 Tortoise ORM 定义 ShippingAddress 模型，包含以下字段：
- id: IntField (主键，自增)
- customer: ForeignKeyField(Customer, related_name="shipping_addresses")
- recipient_name: CharField(max_length=100)
- recipient_phone: CharField(max_length=20)
- province: CharField(max_length=100)
- province_code: CharField(max_length=20, null=True)
- city: CharField(max_length=100)
- city_code: CharField(max_length=20, null=True)
- district: CharField(max_length=100, null=True)
- address: CharField(max_length=500)
- is_default: BooleanField(default=False)
- created_at: DatetimeField(auto_now_add=True)
- updated_at: DatetimeField(auto_now=True)

#### Scenario: 创建收货地址
- **WHEN** 为客户创建新的收货地址
- **THEN** 系统关联到正确的客户，并设置 is_default 字段

#### Scenario: 级联删除
- **WHEN** 删除客户
- **THEN** 系统自动删除该客户的所有收货地址

---

### Requirement: CustomerDiscount 模型定义

系统 SHALL 使用 Tortoise ORM 定义 CustomerDiscount 模型，包含以下字段：
- id: IntField (主键，自增)
- customer: ForeignKeyField(Customer, related_name="discounts")
- brand_id: IntField()
- brand_name: CharField(max_length=100, null=True)
- discount_value: FloatField()
- is_active: BooleanField(default=True)
- created_at: DatetimeField(auto_now_add=True)
- updated_at: DatetimeField(auto_now=True)

#### Scenario: 创建客户折扣
- **WHEN** 为客户创建品牌折扣
- **THEN** 系统验证客户和品牌存在，并保存折扣值

#### Scenario: 唯一性约束
- **WHEN** 为同一客户和品牌创建重复折扣
- **THEN** 系统拒绝创建并返回错误

---

### Requirement: 模型 to_dict 方法

每个模型 SHALL 提供 to_dict() 方法，返回字典格式的数据，字段名与 API 响应一致。

#### Scenario: Customer to_dict
- **WHEN** 调用 customer.to_dict()
- **THEN** 返回包含 id, customer_code, name, customer_type 等字段的字典

#### Scenario: Customer to_dict with relations
- **WHEN** 调用 await customer.to_dict(include_relations=True)
- **THEN** 返回包含 invoice_infos 和 shipping_addresses 嵌套数组的字典