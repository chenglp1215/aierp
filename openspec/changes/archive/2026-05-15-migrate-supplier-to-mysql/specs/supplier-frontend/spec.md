## MODIFIED Requirements

### Requirement: Supplier TypeScript Types

前端 SHALL 定义正确的供应商 TypeScript 类型。

#### Scenario: 供应商 ID 类型
- **WHEN** 定义供应商接口类型
- **THEN** `id` 字段 SHALL 为 `number` 类型

#### Scenario: 银行账户类型
- **WHEN** 定义银行账户接口类型
- **THEN** SHALL 包含 `id`、`bank_name`、`account_name`、`account_no`、`is_default` 字段

#### Scenario: 品牌关联类型
- **WHEN** 定义品牌关联接口类型
- **THEN** `brand_id` 字段 SHALL 为 `number` 类型

### Requirement: Supplier Workspace Component

供应商管理组件 SHALL 正确处理整数 ID。

#### Scenario: 显示供应商列表
- **WHEN** 加载供应商列表
- **THEN** 组件 SHALL 正确处理整数 ID 的供应商数据

#### Scenario: 创建供应商
- **WHEN** 提交创建供应商表单
- **THEN** 组件 SHALL 正确发送银行账户和品牌关联数据

#### Scenario: 编辑供应商
- **WHEN** 编辑供应商
- **THEN** 组件 SHALL 正确加载和显示银行账户及品牌关联数据

#### Scenario: 删除供应商
- **WHEN** 删除供应商
- **THEN** 组件 SHALL 使用整数 ID 调用删除 API

### Requirement: Supplier API Service

前端 API 服务 SHALL 正确处理供应商接口。

#### Scenario: 列表查询
- **WHEN** 调用 `supplierApi.list()`
- **THEN** 服务 SHALL 返回正确类型的供应商列表

#### Scenario: 详情查询
- **WHEN** 调用 `supplierApi.get(id)`
- **THEN** 服务 SHALL 使用整数 ID 查询

#### Scenario: 更新供应商
- **WHEN** 调用 `supplierApi.update(id, data)`
- **THEN** 服务 SHALL 使用整数 ID 更新
