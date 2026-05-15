## ADDED Requirements

### Requirement: 销售订单列表页状态显示
销售订单列表页 SHALL 正确显示订单状态字段，使用后端返回的 `order_status` 字段。

#### Scenario: 列表页显示订单状态
- **WHEN** 用户访问销售订单列表页
- **THEN** 订单状态列 SHALL 显示 `order_status` 字段的值
- **AND** 状态标签 SHALL 使用正确的状态映射显示中文标签

### Requirement: 销售订单详情页状态显示
销售订单详情页 SHALL 正确显示所有状态字段，使用后端返回的扁平字段结构。

#### Scenario: 详情页显示订单状态
- **WHEN** 用户查看销售订单详情
- **THEN** 订单状态 SHALL 显示 `order_status` 字段的值
- **AND** 发货状态 SHALL 显示 `delivery_status` 字段的值
- **AND** 收货状态 SHALL 显示 `receive_status` 字段的值
- **AND** 开票状态 SHALL 显示 `invoice_status` 字段的值

#### Scenario: 详情页状态更新
- **WHEN** 用户修改订单状态
- **THEN** 状态更新请求 SHALL 正确发送到后端
- **AND** 更新成功后 SHALL 刷新订单数据

### Requirement: 状态映射一致性
前端状态映射表 SHALL 与后端枚举值保持一致。

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

#### Scenario: 发货状态映射
- **WHEN** 后端返回发货状态值
- **THEN** 前端 SHALL 正确映射为中文标签：
  - `none` → 未发货
  - `partial` → 部分发货
  - `full` → 全部发货

#### Scenario: 收货状态映射
- **WHEN** 后端返回收货状态值
- **THEN** 前端 SHALL 正确映射为中文标签：
  - `none` → 未收货
  - `partial` → 部分收货
  - `full` → 全部收货

#### Scenario: 开票状态映射
- **WHEN** 后端返回开票状态值
- **THEN** 前端 SHALL 正确映射为中文标签：
  - `none` → 未开票
  - `partial` → 部分开票
  - `full` → 全部开票
