## ADDED Requirements

### Requirement: 外键关联查询规范

系统 SHALL 使用 Tortoise ORM 的 ForeignKeyField 建立外键关联，并通过 prefetch_related 优化查询性能。

#### Scenario: 订单明细关联品牌查询
- **WHEN** 查询订单明细时需要获取品牌名称
- **THEN** 使用 `prefetch_related("items__brand")` 预加载品牌数据

#### Scenario: 订单明细关联仓库查询
- **WHEN** 查询订单明细时需要获取仓库名称
- **THEN** 使用 `prefetch_related("items__warehouse")` 预加载仓库数据

#### Scenario: 订单关联客户查询
- **WHEN** 查询订单时需要获取客户名称
- **THEN** 使用 `prefetch_related("customer")` 预加载客户数据

### Requirement: API 响应格式保持兼容

系统 SHALL 在 API 响应中返回关联的名称字段，保持与原有格式兼容。

#### Scenario: 订单详情返回品牌名称
- **WHEN** 查询订单详情接口
- **THEN** 响应中包含 `brand_id` 和 `brand_name` 字段

#### Scenario: 订单详情返回仓库名称
- **WHEN** 查询订单详情接口
- **THEN** 响应中包含 `warehouse_id` 和 `warehouse_name` 字段

### Requirement: API 请求格式简化

系统 SHALL 接受仅包含 ID 的请求，无需传入冗余的名称字段。

#### Scenario: 创建订单只需传入品牌ID
- **WHEN** 创建订单明细时传入 `brand_id`
- **THEN** 系统自动查询品牌名称，无需传入 `brand_name`

#### Scenario: 创建订单只需传入仓库ID
- **WHEN** 创建订单明细时传入 `warehouse_id`
- **THEN** 系统自动查询仓库名称，无需传入 `warehouse_name`
