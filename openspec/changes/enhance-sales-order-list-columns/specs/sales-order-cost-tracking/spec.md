## ADDED Requirements

### Requirement: Cost item model structure
系统 SHALL 提供 `SalesOrderCostItem` 模型，包含以下字段：
- `id`: 主键
- `sales_order_id`: 关联销售订单 ID（外键）
- `cost_type`: 成本类型（purchase/freight/transfer/other）
- `amount`: 金额（未税，Decimal）
- `source_type`: 来源类型（purchase_order/manual）
- `source_no`: 来源单号（如采购单号）
- `purchase_order_id`: 关联采购单 ID
- `remark`: 备注
- `creator_id`: 创建人 ID
- `creator_name`: 创建人名称
- `created_at`: 创建时间

#### Scenario: Create cost item with purchase order source
- **WHEN** 采购单付款完成时自动创建成本明细
- **THEN** 系统创建 cost_type=purchase, source_type=purchase_order, source_no=采购单号, purchase_order_id=采购单ID 的成本明细

#### Scenario: Create cost item manually
- **WHEN** 用户手动添加运费成本
- **THEN** 系统创建 cost_type=freight, source_type=manual 的成本明细

### Requirement: Cost amount calculation
系统 SHALL 在销售单列表查询时实时计算成本总额。

#### Scenario: Calculate total cost
- **WHEN** 查询销售单列表
- **THEN** 系统返回 `cost_amt` = SUM(SalesOrderCostItem.amount WHERE sales_order_id = ?)

### Requirement: Profit calculation
系统 SHALL 在销售单列表查询时实时计算利润。

#### Scenario: Calculate profit
- **WHEN** 查询销售单列表
- **THEN** 系统返回 `profit_amt` = `total_amt` - `cost_amt`（未税金额计算）

### Requirement: Prevent duplicate cost items
系统 SHALL 防止同一采购单重复创建成本明细。

#### Scenario: Duplicate prevention
- **WHEN** 采购单付款完成触发创建成本明细
- **AND** 该采购单已存在成本明细（purchase_order_id 相同）
- **THEN** 系统跳过创建，不产生重复记录

### Requirement: Cost item CRUD API
系统 SHALL 提供成本明细管理 API。

#### Scenario: List cost items
- **WHEN** GET /api/v1/sales-orders/{order_no}/cost-items
- **THEN** 系统返回该销售单的所有成本明细及成本总额

#### Scenario: Create cost item manually
- **WHEN** POST /api/v1/sales-orders/{order_no}/cost-items
- **AND** 请求体包含 cost_type, amount, remark
- **THEN** 系统创建 source_type=manual 的成本明细

#### Scenario: Delete cost item
- **WHEN** DELETE /api/v1/sales-orders/{order_no}/cost-items/{id}
- **AND** 该成本明细 source_type=manual
- **THEN** 系统删除该成本明细

#### Scenario: Cannot delete purchase cost
- **WHEN** DELETE /api/v1/sales-orders/{order_no}/cost-items/{id}
- **AND** 该成本明细 source_type=purchase_order
- **THEN** 系统拒绝删除，返回错误提示"采购成本不可手动删除"
