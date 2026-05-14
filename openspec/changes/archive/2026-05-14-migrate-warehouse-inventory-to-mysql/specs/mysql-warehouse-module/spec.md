## ADDED Requirements

### Requirement: 仓库数据模型使用 MySQL 存储

系统 SHALL 使用 Tortoise ORM 定义仓库数据模型，存储在 MySQL 数据库的 `warehouses` 表中。

#### Scenario: 创建仓库记录
- **WHEN** 调用 Warehouse.create() 创建仓库
- **THEN** 系统在 MySQL 的 warehouses 表中插入一条记录，自动生成整数 ID

#### Scenario: 查询仓库列表
- **WHEN** 调用 Warehouse.filter().all() 查询仓库列表
- **THEN** 系统从 MySQL 数据库返回仓库记录列表

### Requirement: 仓库编码自动生成

系统 SHALL 在创建仓库时自动生成唯一的仓库编码，格式为 `WH{YYYYMMDD}{6位随机数字}`。

#### Scenario: 创建仓库时未提供编码
- **WHEN** 创建仓库时未提供 warehouse_code
- **THEN** 系统自动生成格式为 WH20260514XXXXXX 的唯一编码

#### Scenario: 创建仓库时提供编码
- **WHEN** 创建仓库时提供了 warehouse_code
- **THEN** 系统使用提供的编码，不自动生成

### Requirement: 仓库状态管理

系统 SHALL 支持仓库状态管理，包括 active（启用）、inactive（停用）、maintenance（维护中）三种状态。

#### Scenario: 创建仓库时默认状态
- **WHEN** 创建仓库时未指定状态
- **THEN** 系统默认设置状态为 active

#### Scenario: 更新仓库状态
- **WHEN** 更新仓库状态为 maintenance
- **THEN** 系统更新 warehouses 表中的 status 字段为 maintenance

### Requirement: 仓库管理员分配

系统 SHALL 支持为仓库分配管理员，记录管理员 ID 和姓名。

#### Scenario: 分配仓库管理员
- **WHEN** 创建或更新仓库时指定 manager_id 和 manager_name
- **THEN** 系统保存管理员信息到 warehouses 表

#### Scenario: 获取管理员候选列表
- **WHEN** 调用获取管理员候选接口
- **THEN** 系统返回可分配为仓库管理员的用户列表

### Requirement: 仓库列表分页查询

系统 SHALL 支持仓库列表的分页查询，支持按状态筛选和关键词搜索。

#### Scenario: 分页查询仓库列表
- **WHEN** 调用 list_warehouses(page=1, page_size=20)
- **THEN** 系统返回第一页的 20 条仓库记录和总数

#### Scenario: 按状态筛选仓库
- **WHEN** 调用 list_warehouses(status='active')
- **THEN** 系统只返回状态为 active 的仓库记录

#### Scenario: 关键词搜索仓库
- **WHEN** 调用 list_warehouses(keyword='深圳')
- **THEN** 系统返回仓库名称或编码包含"深圳"的记录

### Requirement: API 接口保持兼容

系统 SHALL 保持现有 API 接口签名和响应格式不变，前端无需修改。

#### Scenario: 获取仓库详情
- **WHEN** 调用 GET /api/v1/warehouses/{id}
- **THEN** 系统返回包含 id、warehouse_code、name、address、manager_id、manager_name、status、description、created_at、updated_at 的 JSON 对象

#### Scenario: 创建仓库
- **WHEN** 调用 POST /api/v1/warehouses/ 创建仓库
- **THEN** 系统返回创建成功的仓库信息，响应格式与 MongoDB 版本一致
