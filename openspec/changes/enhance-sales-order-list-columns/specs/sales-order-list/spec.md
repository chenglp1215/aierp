## MODIFIED Requirements

### Requirement: Sales order list columns
销售单列表 SHALL 显示以下列：
- 订单日期（order_date）
- 订单编号（order_no）
- 客户名称（customer_name）
- 订单金额（total_tax_amt，含税）
- 订单状态（order_status）
- 成本（cost_amt，实时计算）
- 利润（profit_amt，实时计算）
- 财务状态（finance_status）
- 发票状态（invoice_status）
- 发货状态（delivery_status）
- 收货状态（receive_status）
- 业务员（sale_user_name）
- 操作

#### Scenario: Display all columns
- **WHEN** 用户访问销售单列表
- **THEN** 系统显示上述所有列

#### Scenario: Cost and profit display
- **WHEN** 销售单有关联成本明细
- **THEN** 成本列显示成本总额，利润列显示利润
- **WHEN** 销售单无关联成本明细
- **THEN** 成本列显示 0.00，利润列显示订单未税金额

### Requirement: Finance status field
销售单 SHALL 新增 `finance_status` 字段，枚举值：
- unpaid（未付款）
- partial_paid（部分付款）
- paid（已付款）
- reconciled（已对账）

#### Scenario: Default finance status
- **WHEN** 创建销售单
- **THEN** finance_status 默认为 unpaid

#### Scenario: Update finance status
- **WHEN** PUT /api/v1/sales-orders/{order_no}/finance-status
- **AND** 请求体包含 finance_status
- **THEN** 系统更新销售单的财务状态

### Requirement: Sales order item new fields
销售单明细 SHALL 新增以下字段：
- exchange_qty（换货数量，默认 0）
- supplement_qty（补货数量，默认 0）

#### Scenario: Create order item with new fields
- **WHEN** 创建销售单明细
- **THEN** exchange_qty 和 supplement_qty 默认为 0

#### Scenario: Update order item quantities
- **WHEN** 更新销售单明细
- **AND** 包含 exchange_qty 或 supplement_qty
- **THEN** 系统更新对应字段

### Requirement: List API enhanced response
销售单列表接口 SHALL 返回增强数据。

#### Scenario: Return cost and profit
- **WHEN** GET /api/v1/sales-orders/
- **THEN** 每个销售单返回 cost_amt 和 profit_amt 字段

#### Scenario: Return items for expansion
- **WHEN** GET /api/v1/sales-orders/
- **THEN** 每个销售单返回 items 数组，包含展开所需字段
