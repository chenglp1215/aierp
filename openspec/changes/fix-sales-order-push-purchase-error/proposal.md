## Why

销售订单列表页面的"下推采购"功能报错 `Cannot read properties of undefined (reading 'items')`，订单详情页面也不展示数据。原因是前端代码在调用 `salesOrderApi.getByOrderNo()` 后，错误地使用了 `orderRes.result` 来访问数据，但 API 服务层已经解包了 `result` 字段，实际返回的就是订单对象本身。

## What Changes

- **修复 SalesOrderWorkspace.vue**: `confirmPushPurchase` 函数中移除对 `.result` 的访问
- **修复 SalesOrderDetail.vue**: `loadOrder` 函数中移除对 `.result` 的访问
- **修复 SalesOrderDetail.vue**: `handlePushPurchase` 函数中移除对 `.result` 的访问

## Capabilities

### New Capabilities
无新增能力

### Modified Capabilities
无修改的能力规格

## Impact

- **前端文件**: `web/src/components/workspace/SalesOrderWorkspace.vue`, `web/src/components/workspace/SalesOrderDetail.vue`
- **API 调用**: `salesOrderApi.getByOrderNo()` 返回值处理
- **影响范围**: 销售订单下推采购功能、订单详情页面展示
