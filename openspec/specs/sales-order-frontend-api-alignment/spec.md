## Purpose

定义前端销售订单 API 接口与后端接口的对称规范，确保状态操作接口的一致性和正确性。
## Requirements
### Requirement: 前端销售订单 API 接口对称

前端销售订单 API 接口 SHALL 与后端接口完全对称，使用独立的状态操作接口。

#### Scenario: 提交审核直接审核通过
- **WHEN** 用户在草稿订单页面点击"提交审核"按钮
- **THEN** 系统调用 `POST /api/v1/sales-orders/{order_no}/submit` 接口
- **AND** 订单状态从 `draft` 直接变更为 `audited`（跳过 pending）

#### Scenario: 审核通过（兼容历史数据）
- **WHEN** 用户在待审核订单页面点击"审核通过"按钮（历史数据兼容）
- **THEN** 系统调用 `POST /api/v1/sales-orders/{order_no}/approve` 接口
- **AND** 订单状态从 `pending` 变更为 `audited`

#### Scenario: 驳回订单（兼容历史数据）
- **WHEN** 用户在待审核订单页面点击"驳回"按钮（历史数据兼容）
- **THEN** 系统调用 `POST /api/v1/sales-orders/{order_no}/reject` 接口
- **AND** 订单状态从 `pending` 变更为 `draft`

#### Scenario: 取消订单仅限草稿状态
- **WHEN** 用户点击"取消订单"按钮
- **THEN** 系统调用 `POST /api/v1/sales-orders/{order_no}/cancel` 接口
- **AND** 订单状态变更为 `cancelled`
- **AND** 取消操作仅限 `draft` 状态的订单

### Requirement: 商品明细只传外键字段

前端创建/更新订单时，商品明细 SHALL 只传递 `spec_id` 和 `warehouse_id` 外键字段，商品名称、品牌名称等通过后端外键关联获取。

#### Scenario: 创建订单商品明细
- **WHEN** 用户创建销售订单并添加商品明细
- **THEN** 请求体中的 items 数组 SHALL 包含 `spec_id`、`warehouse_id`、`qty`、`price`、`discount`、`shipping_method` 字段
- **AND** 请求体 SHALL NOT 包含 `product_name`、`brand_name`、`product_id`、`brand_id` 等冗余字段

#### Scenario: 订单详情返回完整信息
- **WHEN** 用户查看订单详情
- **THEN** 响应体中的 items 数组 SHALL 包含 `product_name`、`brand_name`、`warehouse_name` 等通过外键关联获取的字段
- **AND** `shipping_method` 字段 SHALL 返回中文值（直运/仓库发货）

### Requirement: 发货方式英文值映射

前端发货方式 SHALL 使用英文值发送请求，后端返回中文值用于展示。

#### Scenario: 选择直运方式
- **WHEN** 用户选择发货方式为"直运"
- **THEN** 请求体中的 `shipping_method` 字段 SHALL 为 `direct`
- **AND** 订单详情中显示的发货方式 SHALL 为"直运"

#### Scenario: 选择仓库发货方式
- **WHEN** 用户选择发货方式为"仓库发货"
- **THEN** 请求体中的 `shipping_method` 字段 SHALL 为 `warehouse`
- **AND** 订单详情中显示的发货方式 SHALL 为"仓库发货"

### Requirement: 移除旧的状态更新接口

前端 SHALL 移除 `updateOrderStatus`、`updateDeliveryStatus`、`updateReceiveStatus`、`updateInvoiceStatus` 等旧接口调用。

#### Scenario: 不再使用 updateOrderStatus
- **WHEN** 前端代码调用销售订单状态相关接口
- **THEN** SHALL 使用 `submit`、`approve`、`reject`、`cancel` 等独立接口
- **AND** SHALL NOT 使用 `updateOrderStatus` 接口

#### Scenario: 移除发货/收货/开票状态更新
- **WHEN** 前端代码需要更新发货/收货/开票状态
- **THEN** 暂时隐藏相关功能（后端暂未实现）
- **AND** 移除 `updateDeliveryStatus`、`updateReceiveStatus`、`updateInvoiceStatus` 接口调用

### Requirement: 测试用状态修改接口

后端 SHALL 提供测试用的状态修改接口，支持手动修改发货、收货、财务、开票状态。

#### Scenario: 调用测试状态修改接口
- **WHEN** 前端调用 `POST /api/v1/sales-orders/{order_no}/test-update-status` 接口
- **THEN** 后端 SHALL 更新订单的 `delivery_status`、`receive_status`、`finance_status`、`invoice_status` 字段
- **AND** 更新后 SHALL 检查是否满足自动完成条件

#### Scenario: 测试接口权限控制
- **WHEN** 用户调用测试状态修改接口
- **THEN** 系统 SHALL 验证用户具有 `order.edit` 权限
- **AND** 接口 SHALL 记录操作日志

