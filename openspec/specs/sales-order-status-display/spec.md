## Purpose

定义销售订单状态显示规范，确保前端状态映射与后端枚举值一致，操作按钮显示条件正确。
## Requirements
### Requirement: 销售订单列表页状态显示
销售订单列表页 SHALL 正确显示订单状态字段，使用后端返回的 `order_status` 字段，状态映射调整如下。

#### Scenario: 列表页显示订单状态
- **WHEN** 用户访问销售订单列表页
- **THEN** 订单状态列 SHALL 显示 `order_status` 字段的值
- **AND** 状态标签 SHALL 使用正确的状态映射显示中文标签

#### Scenario: 草稿订单操作按钮
- **WHEN** 订单状态为 `draft`
- **THEN** 操作区域 SHALL 显示"编辑"、"提交审核"、"删除"、"取消"按钮

#### Scenario: 待审核订单操作按钮（兼容历史数据）
- **WHEN** 订单状态为 `pending`（历史数据兼容）
- **THEN** 操作区域 SHALL 显示"审核通过"按钮
- **AND** 操作区域 SHALL NOT 显示"编辑"、"删除"、"驳回"按钮

#### Scenario: 已审核订单操作按钮
- **WHEN** 订单状态为 `audited`
- **THEN** 操作区域 SHALL 显示"下推采购"按钮
- **AND** 操作区域 SHALL NOT 显示"关闭"、"取消"按钮

#### Scenario: 部分下推订单操作按钮
- **WHEN** 订单状态为 `partially_pushed_to_purchase`
- **THEN** 操作区域 SHALL 显示"下推采购"按钮
- **AND** 操作区域 SHALL NOT 显示"关闭"、"取消"按钮

#### Scenario: 已下推订单操作按钮
- **WHEN** 订单状态为 `pushed_to_purchase`
- **THEN** 操作区域 SHALL NOT 显示任何操作按钮

#### Scenario: 已完成订单操作按钮
- **WHEN** 订单状态为 `closed`
- **THEN** 操作区域 SHALL NOT 显示任何操作按钮

### Requirement: 销售订单详情页状态显示
销售订单详情页 SHALL 正确显示所有状态字段，使用后端返回的扁平字段结构，操作按钮调整如下。

#### Scenario: 详情页显示订单状态
- **WHEN** 用户查看销售订单详情
- **THEN** 订单状态 SHALL 显示 `order_status` 字段的值
- **AND** 发货状态 SHALL 显示 `delivery_status` 字段的值
- **AND** 收货状态 SHALL 显示 `receive_status` 字段的值
- **AND** 开票状态 SHALL 显示 `invoice_status` 字段的值
- **AND** 财务状态 SHALL 显示 `finance_status` 字段的值

#### Scenario: 详情页草稿状态操作
- **WHEN** 订单状态为 `draft`
- **THEN** 详情页 SHALL 显示"提交审核"按钮
- **AND** 详情页 SHALL 显示"取消订单"按钮

#### Scenario: 详情页已审核状态操作
- **WHEN** 订单状态为 `audited`
- **THEN** 详情页 SHALL 显示"下推采购"按钮
- **AND** 详情页 SHALL NOT 显示"关闭订单"、"取消订单"按钮

#### Scenario: 详情页部分下推状态操作
- **WHEN** 订单状态为 `partially_pushed_to_purchase`
- **THEN** 详情页 SHALL 显示"下推采购"按钮
- **AND** 详情页 SHALL NOT 显示"关闭订单"、"取消订单"按钮

### Requirement: 发货状态基于出库单已发货状态计算
订单发货状态 SHALL 基于出库单的 `shipped`（已发货）状态判断，而非基于出库数量判断。计算逻辑：获取订单下所有仓库发货明细对应的出库单，根据出库单的 `shipped` 状态占比确定发货状态。

#### Scenario: 全部已发货
- **WHEN** 订单下所有仓库发货明细对应的出库单状态均为 `shipped`
- **THEN** 订单 `delivery_status` 更新为 `full`（全部发货）

#### Scenario: 部分已发货
- **WHEN** 订单下部分仓库发货明细对应的出库单状态为 `shipped`，但并非全部
- **THEN** 订单 `delivery_status` 更新为 `partial`（部分发货）

#### Scenario: 未发货
- **WHEN** 订单下所有仓库发货明细对应的出库单状态均非 `shipped`
- **THEN** 订单 `delivery_status` 为 `none`（未发货）

#### Scenario: 直运明细不参与发货状态计算
- **WHEN** 订单明细的 `shipping_method` 为 `direct`（直运）
- **THEN** 该明细不参与发货状态计算

### Requirement: 状态映射一致性
前端状态映射表 SHALL 与后端枚举值保持一致，状态显示文案调整如下。

#### Scenario: 订单状态映射
- **WHEN** 后端返回订单状态值
- **THEN** 前端 SHALL 正确映射为中文标签：
  - `draft` → 草稿
  - `pending` → 待审核（兼容历史数据）
  - `audited` → 已审核
  - `partially_pushed_to_purchase` → 部分下推
  - `pushed_to_purchase` → 已下推采购
  - `closed` → 已完成
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

#### Scenario: 财务状态映射
- **WHEN** 后端返回财务状态值
- **THEN** 前端 SHALL 正确映射为中文标签：
  - `unpaid` → 未付款
  - `partial_paid` → 部分付款
  - `paid` → 已付款
  - `reconciled` → 已对账