## ADDED Requirements

### Requirement: CustomerService MySQL 实现

系统 SHALL 提供 CustomerService 类，使用 Tortoise ORM 实现客户 CRUD 操作：
- create_customer(data, current_user): 创建客户，自动生成 customer_code
- update_customer(customer_id, data): 更新客户信息
- delete_customer(customer_id): 删除客户（级联删除关联数据）
- get_customer_by_id(customer_id): 获取客户详情
- list_customers(page, page_size, filters): 分页查询客户列表
- get_customer_stats(): 获取客户统计信息
- update_status(customer_id, status): 更新客户状态
- transfer_customer(customer_id, new_sales_user_id): 转移客户

#### Scenario: 创建客户成功
- **WHEN** 调用 create_customer() 并提供有效的客户数据
- **THEN** 系统创建客户记录，自动生成 customer_code，返回完整客户信息

#### Scenario: 创建客户失败
- **WHEN** 调用 create_customer() 但缺少必填字段（name, customer_type）
- **THEN** 系统返回验证错误

#### Scenario: 查询客户列表
- **WHEN** 调用 list_customers(page=1, page_size=20)
- **THEN** 系统返回分页结果，包含 total, page, page_size, items 字段

---

### Requirement: InvoiceInfoService MySQL 实现

系统 SHALL 提供 InvoiceInfoService 类，管理客户开票信息：
- add_invoice_info(customer_id, data): 添加开票信息
- update_invoice_info(invoice_id, data): 更新开票信息
- delete_invoice_info(invoice_id): 删除开票信息
- set_default_invoice_info(customer_id, invoice_id): 设置默认开票信息

#### Scenario: 添加开票信息
- **WHEN** 为客户添加开票信息
- **THEN** 系统创建记录并关联到客户

#### Scenario: 设置默认开票信息
- **WHEN** 设置某开票信息为默认
- **THEN** 系统将该客户其他开票信息的 is_default 设为 False

---

### Requirement: ShippingAddressService MySQL 实现

系统 SHALL 提供 ShippingAddressService 类，管理客户收货地址：
- add_shipping_address(customer_id, data): 添加收货地址
- update_shipping_address(address_id, data): 更新收货地址
- delete_shipping_address(address_id): 删除收货地址
- set_default_shipping_address(customer_id, address_id): 设置默认收货地址

#### Scenario: 添加收货地址
- **WHEN** 为客户添加收货地址
- **THEN** 系统创建记录并关联到客户

#### Scenario: 设置默认收货地址
- **WHEN** 设置某收货地址为默认
- **THEN** 系统将该客户其他收货地址的 is_default 设为 False

---

### Requirement: CustomerDiscountService MySQL 实现

系统 SHALL 提供 CustomerDiscountService 类，管理客户折扣：
- create_discount(data): 创建客户折扣
- update_discount(discount_id, data): 更新折扣
- delete_discount(discount_id): 删除折扣
- list_discounts(page, page_size, filters): 查询折扣列表
- get_discount_by_customer_and_brand(customer_id, brand_id): 获取指定客户品牌的折扣
- toggle_discount_status(discount_id, is_active): 切换折扣状态

#### Scenario: 创建折扣成功
- **WHEN** 为客户和品牌创建折扣
- **THEN** 系统验证客户和品牌存在，保存折扣值

#### Scenario: 创建重复折扣失败
- **WHEN** 为同一客户和品牌创建重复折扣
- **THEN** 系统返回错误 "该客户和品牌的折扣配置已存在"

---

### Requirement: API 响应格式兼容

服务层 SHALL 返回与现有 MongoDB 实现一致的响应格式，确保前端无需修改。

#### Scenario: 客户详情响应格式
- **WHEN** 调用 get_customer_by_id()
- **THEN** 返回包含 invoice_infos 和 shipping_addresses 嵌套数组的字典

#### Scenario: ID 字段类型
- **WHEN** 返回任何模型数据
- **THEN** id 字段为整数值（MySQL 自增主键）