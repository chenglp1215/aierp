## Why

销售订单下推采购单时报错 `AttributeError: 'SalesOrderItem' object has no attribute 'brand_id'`。原因是 `purchase_order_service_mysql.py` 直接访问 `SalesOrderItem.brand_id` 属性，但该模型已重构为通过外键关联链（`spec -> product -> brand`）获取品牌信息，不再有冗余的 `brand_id` 字段。

## What Changes

- 修复 `purchase_order_service_mysql.py` 中对 `SalesOrderItem.brand_id` 的错误访问
- 通过正确的关联链获取品牌信息：`item.spec.product.brand.id`
- 同步修复其他可能存在的字段访问错误（`product_id`, `warehouse_id` 等）

## Capabilities

### New Capabilities
无

### Modified Capabilities
- `purchase-order-creation`: 修复从销售订单创建采购单时的字段映射逻辑

## Impact

- **后端服务**: `backend/services/purchase_order_service_mysql.py`
- **涉及接口**: `POST /api/sales-orders/{order_no}/push-to-purchase`
- **数据模型**: `SalesOrderItem`（无变更，只是修正访问方式）
