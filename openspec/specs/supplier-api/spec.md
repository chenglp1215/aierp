## MODIFIED Requirements

### Requirement: Create Supplier

系统 SHALL 支持创建供应商，使用 MySQL 存储。

#### Scenario: 成功创建供应商
- **WHEN** 用户提交供应商创建请求，包含名称、联系人、联系电话等信息
- **THEN** 系统 SHALL 在 MySQL 创建供应商记录并返回整数 ID

#### Scenario: 创建供应商带银行账户
- **WHEN** 用户提交供应商创建请求，包含银行账户信息
- **THEN** 系统 SHALL 同时创建供应商记录和银行账户记录

#### Scenario: 创建供应商带品牌关联
- **WHEN** 用户提交供应商创建请求，包含品牌关联列表
- **THEN** 系统 SHALL 同时创建供应商记录和品牌关联记录

#### Scenario: 供应商名称重复
- **WHEN** 用户提交的供应商名称已存在
- **THEN** 系统 SHALL 返回错误 "供应商名称已存在"

### Requirement: Update Supplier

系统 SHALL 支持更新供应商信息。

#### Scenario: 更新基本信息
- **WHEN** 用户提交供应商更新请求
- **THEN** 系统 SHALL 更新 MySQL 中对应的供应商记录

#### Scenario: 更新银行账户
- **WHEN** 用户提交包含银行账户的更新请求
- **THEN** 系统 SHALL 同步更新银行账户记录

#### Scenario: 更新品牌关联
- **WHEN** 用户提交包含品牌关联列表的更新请求
- **THEN** 系统 SHALL 删除旧关联并创建新关联

### Requirement: Delete Supplier

系统 SHALL 支持删除供应商。

#### Scenario: 成功删除供应商
- **WHEN** 用户删除没有关联采购单的供应商
- **THEN** 系统 SHALL 级联删除供应商及其关联数据

#### Scenario: 供应商有采购单无法删除
- **WHEN** 用户删除有关联采购单的供应商
- **THEN** 系统 SHALL 返回错误 "该供应商下存在 X 个采购单，无法删除"

### Requirement: List Suppliers

系统 SHALL 支持分页查询供应商列表。

#### Scenario: 分页查询
- **WHEN** 用户请求供应商列表，指定页码和每页数量
- **THEN** 系统 SHALL 返回分页结果，包含总数、当前页、每页数量和供应商列表

#### Scenario: 关键词搜索
- **WHEN** 用户指定搜索关键词
- **THEN** 系统 SHALL 模糊匹配供应商名称

#### Scenario: 按状态筛选
- **WHEN** 用户指定 `is_active` 参数
- **THEN** 系统 SHALL 只返回对应状态的供应商

#### Scenario: 按品牌筛选
- **WHEN** 用户指定品牌 ID 列表
- **THEN** 系统 SHALL 只返回关联了指定品牌的供应商

### Requirement: Get Supplier Detail

系统 SHALL 支持获取供应商详情。

#### Scenario: 获取详情
- **WHEN** 用户请求指定 ID 的供应商详情
- **THEN** 系统 SHALL 返回供应商信息，包含银行账户和品牌关联列表

#### Scenario: 供应商不存在
- **WHEN** 用户请求不存在的供应商 ID
- **THEN** 系统 SHALL 返回错误 "供应商不存在"

### Requirement: Toggle Supplier Active

系统 SHALL 支持切换供应商激活状态。

#### Scenario: 激活供应商
- **WHEN** 用户激活停用的供应商
- **THEN** 系统 SHALL 将 `is_active` 设为 `true`

#### Scenario: 停用供应商
- **WHEN** 用户停用激活的供应商
- **THEN** 系统 SHALL 将 `is_active` 设为 `false`

### Requirement: Get Suppliers by Brand

系统 SHALL 支持根据品牌 ID 获取供应商列表。

#### Scenario: 按品牌查询
- **WHEN** 用户指定品牌 ID
- **THEN** 系统 SHALL 返回关联了该品牌的激活供应商列表

### Requirement: API Response Format

API 响应 SHALL 使用统一格式。

#### Scenario: 成功响应
- **WHEN** API 执行成功
- **THEN** 系统 SHALL 返回 `{status: "success", message: "...", result: {...}}`

#### Scenario: 错误响应
- **WHEN** API 执行失败
- **THEN** 系统 SHALL 返回 `{status: "error", message: "...", result: null}`

#### Scenario: ID 类型变更
- **WHEN** 返回供应商数据
- **THEN** `id` 字段 SHALL 为整数类型（非字符串）
