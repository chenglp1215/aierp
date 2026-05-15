## ADDED Requirements

### Requirement: PurchaseOrderItem 外键关联查询

采购单明细 SHALL 通过 ForeignKeyField 关联 ProductSpec 和 Warehouse 表，通过关联链获取 Product 和 Brand 信息。

#### Scenario: 查询采购单明细返回关联信息
- **WHEN** 调用 `get_order_by_no` 查询采购单详情
- **THEN** 返回的明细中包含 `product_id`、`product_code`、`product_name`、`spec_id`、`spec_code`、`brand_id`、`brand_name`、`warehouse_id`、`warehouse_name` 字段
- **AND** 这些字段通过外键关联查询获取，而非冗余存储

#### Scenario: 创建采购单明细时只传入外键 ID
- **WHEN** 创建采购单明细时
- **THEN** 只需传入 `spec_id`、`warehouse_id` 等外键 ID
- **AND** 不需要传入 `brand_name`、`warehouse_name` 等冗余字段

### Requirement: PurchaseOrder 主表外键关联

采购单主表 SHALL 通过 ForeignKeyField 关联 Brand 表，通过关联查询获取品牌名称。

#### Scenario: 查询采购单返回品牌信息
- **WHEN** 查询采购单列表或详情
- **THEN** 返回的 `brand_name` 通过 `brand_id` 外键关联查询获取

### Requirement: API 响应格式兼容

API 响应格式 SHALL 保持与重构前兼容，前端无需修改。

#### Scenario: 采购单详情接口返回格式不变
- **WHEN** 调用 GET `/purchase-orders/{purchase_no}` 接口
- **THEN** 返回的 JSON 结构与重构前相同
- **AND** 包含 `brand_name`、`warehouse_name` 等字段（通过关联查询获取）

### Requirement: 使用 prefetch_related 优化查询

Service 层 SHALL 使用 `prefetch_related` 预加载关联数据，避免 N+1 查询问题。

#### Scenario: 预加载关联数据
- **WHEN** 查询采购单详情时
- **THEN** 使用 `prefetch_related("items__spec__product__brand", "items__warehouse")` 预加载关联数据
- **AND** 不会产生额外的 N+1 查询