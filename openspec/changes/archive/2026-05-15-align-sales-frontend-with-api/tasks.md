## 1. API 接口重构

- [ ] 1.1 重构 `web/src/services/api.ts` 中的 `salesOrderApi`
  - 移除 `updateOrderStatus`、`updateDeliveryStatus`、`updateReceiveStatus`、`updateInvoiceStatus` 接口
  - 添加 `submit`、`approve`、`reject`、`cancel` 独立接口
  - 更新 `create` 和 `createAndSubmit` 的 items 类型定义
  - 验证：TypeScript 编译通过

- [ ] 1.2 更新发货方式下拉选项
  - 将 `shippingMethodOptions` 的 value 改为英文：`direct`、`warehouse`
  - 验证：创建订单时发送的 `shipping_method` 为英文值

## 2. SalesOrderWorkspace 组件更新

- [ ] 2.1 更新状态操作方法
  - 将 `handleAuditOrder` 改为调用 `salesOrderApi.approve`
  - 将 `handleCancelOrder` 改为调用 `salesOrderApi.cancel`
  - 添加 `handleSubmitOrder` 方法调用 `salesOrderApi.submit`
  - 添加 `handleRejectOrder` 方法调用 `salesOrderApi.reject`
  - 验证：各状态操作按钮功能正常

- [ ] 2.2 更新状态按钮显示逻辑
  - `draft` 状态显示：编辑、提交审核、删除、取消
  - `pending` 状态显示：审核通过、驳回
  - `audited` 状态显示：下推采购、关闭、取消
  - 验证：不同状态显示正确的操作按钮

- [ ] 2.3 移除发货/收货/开票状态更新功能
  - 移除 `handleUpdateDeliveryStatus`、`handleUpdateReceiveStatus`、`handleUpdateInvoiceStatus` 方法
  - 隐藏详情页中的状态更新下拉框
  - 验证：详情页不再显示状态更新区域

## 3. SalesOrderCreate 组件更新

- [ ] 3.1 更新商品明细数据结构
  - 创建订单时 items 只传 `spec_id`、`warehouse_id`、`qty`、`price`、`discount`、`shipping_method`
  - 移除 `product_id`、`brand_id`、`product_name`、`brand_name` 等冗余字段
  - 验证：创建订单请求体结构正确

- [ ] 3.2 更新发货方式选项
  - 将 `shippingMethodOptions` 改为英文值
  - 验证：下拉选项显示中文，发送值为英文

## 4. SalesOrderList 组件更新

- [ ] 4.1 添加 `pending` 状态支持
  - 更新 `statusMap` 添加 `pending` 状态映射
  - 添加 `pending` 状态的样式类
  - 验证：列表正确显示待审核状态

- [ ] 4.2 更新操作按钮逻辑
  - 移除旧的 `handleConfirmOrder` 方法
  - 添加审核通过和驳回按钮逻辑
  - 验证：待审核订单显示正确的操作按钮

## 5. SalesOrderDetail 组件更新

- [ ] 5.1 更新详情页状态展示
  - 确保 `pending` 状态正确显示
  - 添加驳回按钮和功能
  - 验证：详情页状态操作功能完整

## 6. 测试验证

- [ ] 6.1 完整流程测试
  - 创建草稿订单
  - 提交审核（draft → pending）
  - 审核通过（pending → audited）
  - 驳回测试（pending → draft）
  - 取消订单测试
  - 验证：所有状态流转正常

- [ ] 6.2 商品明细验证
  - 创建订单后查看详情
  - 验证商品名称、品牌名称、仓库名称正确回显
  - 验证发货方式显示中文
