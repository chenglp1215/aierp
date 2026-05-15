## ADDED Requirements

### Requirement: 销售订单 API 返回值正确处理
前端组件在调用 `salesOrderApi.getByOrderNo()` 后，必须正确处理返回值，直接使用返回的订单对象，而不是访问 `.result` 属性。

#### Scenario: 下推采购功能正常工作
- **WHEN** 用户在销售订单列表页面点击"下推采购"按钮
- **THEN** 系统正确获取订单详情并展示商品选择弹窗，无 JavaScript 报错

#### Scenario: 订单详情页面正常展示
- **WHEN** 用户进入销售订单详情页面
- **THEN** 系统正确加载并展示订单信息、商品明细、状态流转记录等数据