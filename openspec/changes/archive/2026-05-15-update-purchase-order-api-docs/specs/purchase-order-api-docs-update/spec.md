## ADDED Requirements

### Requirement: 采购单创建请求参数更新

采购单创建接口 SHALL 不再要求传入冗余字段 `brand_name`、`warehouse_name`。

#### Scenario: 创建采购单时只传入外键 ID
- **WHEN** 创建采购单时
- **THEN** 只需传入 `brand_id`、`spec_id`、`warehouse_id` 等外键 ID
- **AND** 不需要传入 `brand_name`、`warehouse_name` 等冗余字段

### Requirement: 采购单明细数据结构说明

接口文档 SHALL 说明采购单明细通过外键关联获取名称字段。

#### Scenario: 明细字段来源说明
- **WHEN** 查看采购单明细数据结构
- **THEN** 文档说明 `product_name`、`brand_name`、`warehouse_name` 通过外键关联查询获取
- **AND** 说明关联链：spec → product → brand

### Requirement: 响应格式兼容说明

接口文档 SHALL 说明响应格式保持兼容，字段名不变但来源变化。

#### Scenario: 响应字段来源说明
- **WHEN** 查看采购单详情响应
- **THEN** 文档说明 `brand_name` 通过 `brand_id` 外键关联查询获取
- **AND** 说明 `warehouse_name` 通过 `warehouse_id` 外键关联查询获取