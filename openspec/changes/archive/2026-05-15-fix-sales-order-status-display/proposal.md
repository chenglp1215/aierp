## Why

销售订单列表页和详情页的状态字段显示为空，原因是前后端数据结构不一致：
- 后端返回的是扁平字段（`order_status`、`delivery_status`、`receive_status`、`invoice_status`）
- 详情页前端期望的是嵌套结构（`status.order_status`、`status.delivery_status` 等）
- 列表页前端使用的是旧的字段名（`status`、`payment_status`），与后端不匹配

## What Changes

- 修复 `SalesOrderDetail.vue`：将 `order.status?.order_status` 改为 `order.order_status`
- 修复 `SalesOrderList.vue`：将 `order.status` 改为 `order.order_status`，移除不存在的 `payment_status`
- 统一状态映射表，确保与后端枚举值一致

## Capabilities

### New Capabilities
无新能力

### Modified Capabilities
无规格变更，仅前端实现修复

## Impact

- 前端文件：
  - `web/src/components/workspace/SalesOrderDetail.vue`
  - `web/src/components/workspace/SalesOrderList.vue`
- 无 API 变更
- 无数据库变更
