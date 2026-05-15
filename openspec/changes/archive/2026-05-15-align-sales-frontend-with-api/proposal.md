## Why

前端销售订单模块与后端 API 存在严重的不对称问题：
1. **接口不匹配**：前端使用 `updateOrderStatus` 等旧接口，后端已改为 `submit`/`approve`/`reject`/`cancel` 独立接口
2. **参数不匹配**：前端发送 `product_id`、`brand_id` 等字段，后端只需要 `spec_id` 和 `warehouse_id`
3. **响应不匹配**：前端期望旧字段结构，后端返回新的外键关联结构
4. **功能不完整**：缺少 `pending` 状态的处理、缺少驳回功能

## What Changes

- **BREAKING** 重构 `salesOrderApi` 接口定义，对齐后端 API
- 更新 `SalesOrderWorkspace.vue` 使用新的状态操作接口
- 更新 `SalesOrderCreate.vue` 商品明细只传 `spec_id` 和 `warehouse_id`
- 更新 `SalesOrderList.vue` 列表展示字段对齐后端返回
- 新增驳回订单功能按钮
- 新增 `pending` 状态的展示和处理
- 修复发货方式映射（`direct`/`warehouse` vs 前端的中文）

## Capabilities

### New Capabilities
- `sales-order-frontend-api-alignment`: 前端销售订单 API 与后端接口对齐

### Modified Capabilities
- `sales-order-status-display`: 更新状态展示以支持 `pending` 状态和驳回流程

## Impact

- **前端文件**：
  - `web/src/services/api.ts` - 重构 salesOrderApi
  - `web/src/components/workspace/SalesOrderWorkspace.vue` - 主工作区组件
  - `web/src/components/workspace/SalesOrderList.vue` - 列表组件
  - `web/src/components/workspace/SalesOrderCreate.vue` - 创建组件
  - `web/src/components/workspace/SalesOrderDetail.vue` - 详情组件
- **API 变更**：移除 `updateOrderStatus`，改用 `submit`/`approve`/`reject`/`cancel`
- **数据结构变更**：商品明细只需 `spec_id` 和 `warehouse_id`
