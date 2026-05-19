## ADDED Requirements

### Requirement: Supplier MySQL Model

供应商数据 SHALL 使用 MySQL 存储，采用 Tortoise ORM 定义模型。

#### Scenario: 创建供应商模型
- **WHEN** 定义供应商数据模型
- **THEN** 系统 SHALL 创建 `Supplier` 模型，包含 `id`、`name`、`contact_person`、`contact_phone`、`contact_email`、`address`、`remark`、`is_active`、`created_at`、`updated_at` 字段

#### Scenario: 创建银行账户模型
- **WHEN** 定义银行账户数据模型
- **THEN** 系统 SHALL 创建 `SupplierBankAccount` 模型，包含 `id`、`supplier_id`（外键）、`bank_name`、`account_name`、`account_no`、`is_default` 字段

#### Scenario: 创建供应商品牌关联模型
- **WHEN** 定义供应商品牌关联数据模型
- **THEN** 系统 SHALL 创建 `SupplierBrand` 模型，包含 `id`、`supplier_id`（外键）、`brand_id`（外键）、`discount`、`is_priority` 字段

### Requirement: Supplier Foreign Key Constraints

供应商相关表 SHALL 建立外键约束保证数据完整性。

#### Scenario: 银行账户外键约束
- **WHEN** 创建银行账户记录
- **THEN** 系统 SHALL 验证 `supplier_id` 关联的供应商存在

#### Scenario: 品牌关联外键约束
- **WHEN** 创建供应商品牌关联记录
- **THEN** 系统 SHALL 验证 `supplier_id` 和 `brand_id` 分别关联的供应商和品牌存在

#### Scenario: 供应商删除级联
- **WHEN** 删除供应商
- **THEN** 系统 SHALL 级联删除关联的银行账户和品牌关联记录

### Requirement: Supplier Model Methods

供应商模型 SHALL 提供数据转换方法。

#### Scenario: 转换为字典
- **WHEN** 调用 `to_dict()` 方法
- **THEN** 系统 SHALL 返回包含所有字段及其关联数据的字典

#### Scenario: 包含关联数据
- **WHEN** 调用 `to_dict()` 方法
- **THEN** 系统 SHALL 包含银行账户列表和品牌关联列表
