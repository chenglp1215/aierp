## Why

两个 BUG 需要修复：

1. **销售订单提交失败**：`/api/v1/sales-orders/create-and-submit` 接口返回错误 "customer_name is non nullable field, but null was passed"。原因是前端提交订单时没有传递 `customer_name` 字段，但后端模型定义该字段为非空。

2. **规格库存详情接口 404**：前端调用 `/api/v1/products/specs/{spec_id}/stock-detail` 接口返回 404，原因是后端没有实现该接口。

## What Changes

- **后端修改**：
  - 在 `product.py` 路由中添加 `/specs/{spec_id}/stock-detail` 接口
  - 该接口调用 `stock_service.get_stock_status_by_spec_ids` 获取规格库存信息

- **前端修改**：
  - 在 `SalesOrderWorkspace.vue` 的 `submitData` 中添加 `customer_name` 字段
  - 在 `SalesOrderCreate.vue` 的提交数据中添加 `customer_name` 字段

## Capabilities

### New Capabilities
- `spec-stock-detail-api`: 新增规格库存详情查询接口

### Modified Capabilities
无

## Impact

- **后端**：`backend/app/routers/product.py` - 新增接口
- **前端**：
  - `web/src/components/workspace/SalesOrderWorkspace.vue` - 提交数据添加 customer_name
  - `web/src/components/workspace/SalesOrderCreate.vue` - 提交数据添加 customer_name
