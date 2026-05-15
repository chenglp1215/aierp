## MODIFIED Requirements

### Requirement: 销售订单列表页状态显示
销售订单列表页 SHALL 正确显示订单状态字段，使用后端返回的 `order_status` 字段，并支持 `pending` 状态的操作按钮。

#### Scenario: 列表页显示订单状态
- **WHEN** 用户访问销售订单列表页
- **THEN** 订单状态列 SHALL 显示 `order_status` 字段的值
- **AND** 状态标签 SHALL 使用正确的状态映射显示中文标签

#### Scenario: 草稿订单操作按钮
- **WHEN** 订单状态为 `draft`
- **THEN** 操作区域 SHALL 显示"编辑"、"提交审核"、"删除"、"取消"按钮

#### Scenario: 待审核订单操作按钮
- **WHEN** 订单状态为 `pending`
- **THEN** 操作区域 SHALL 显示"审核通过"、"驳回"按钮
- **AND** 操作区域 SHALL NOT 显示"编辑"、"删除"按钮

#### Scenario: 已审核订单操作按钮
- **WHEN** 订单状态为 `audited`
- **THEN** 操作区域 SHALL 显示"下推采购"、"关闭"、"取消"按钮

### Requirement: 销售订单详情页状态显示
销售订单详情页 SHALL 正确显示所有状态字段，使用后端返回的扁平字段结构，并支持驳回操作。

#### Scenario: 详情页显示订单状态
- **WHEN** 用户查看销售订单详情
- **THEN** 订单状态 SHALL 显示 `order_status` 字段的值
- **AND** 发货状态 SHALL 显示 `delivery_status` 字段的值
- **AND** 收货状态 SHALL 显示 `receive_status` 字段的值
- **AND** 开票状态 SHALL 显示 `invoice_status` 字段的值

#### Scenario: 详情页待审核状态操作
- **WHEN** 订单状态为 `pending`
- **THEN** 详情页 SHALL 显示"审核通过"和"驳回"按钮

#### Scenario: 详情页驳回操作
- **WHEN** 用户点击"驳回"按钮
- **THEN** 系统调用 `POST /api/v1/sales-orders/{order_no}/reject` 接口
- **AND** 订单状态从 `pending` 变更为 `draft`
- **AND** 刷新订单详情数据

### Requirement: 状态映射一致性
前端状态映射表 SHALL 与后端枚举值保持一致，包含 `pending` 状态。

#### Scenario: 订单状态映射
- **WHEN** 后端返回订单状态值
- **THEN** 前端 SHALL 正确映射为中文标签：
  - `draft` → 草稿
  - `pending` → 待审核
  - `audited` → 已审核
  - `partially_pushed_to_purchase` → 部分下推采购
  - `pushed_to_purchase` → 已下推采购
  - `closed` → 已关闭
  - `cancelled` → 已取消

#### Scenario: 待审核状态样式
- **WHEN** 订单状态为 `pending`
- **THEN** 状态标签 SHALL 使用黄色/橙色样式
