## 1. 销售订单详情页修复

- [ ] 1.1 修复 SalesOrderDetail.vue 状态字段引用，将 `order.status?.order_status` 改为 `order.order_status`
- [ ] 1.2 修复 SalesOrderDetail.vue 发货状态字段引用，将 `order.status?.delivery_status` 改为 `order.delivery_status`
- [ ] 1.3 修复 SalesOrderDetail.vue 收货状态字段引用，将 `order.status?.receive_status` 改为 `order.receive_status`
- [ ] 1.4 修复 SalesOrderDetail.vue 开票状态字段引用，将 `order.status?.invoice_status` 改为 `order.invoice_status`
- [ ] 1.5 修复状态更新方法中的字段引用

## 2. 销售订单列表页修复

- [ ] 2.1 更新 SalesOrderList.vue 状态映射表，使用与后端一致的枚举值
- [ ] 2.2 修复列表页订单状态字段引用，将 `order.status` 改为 `order.order_status`
- [ ] 2.3 移除不存在的付款状态列（payment_status）
- [ ] 2.4 更新表格列定义，移除付款状态列

## 3. 验证

- [ ] 3.1 启动前端开发服务器，验证列表页状态显示正确
- [ ] 3.2 验证详情页所有状态字段显示正确
- [ ] 3.3 验证状态更新功能正常工作
