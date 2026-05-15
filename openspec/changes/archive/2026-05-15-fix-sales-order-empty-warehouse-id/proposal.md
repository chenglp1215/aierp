## Why

销售订单创建接口 `/api/v1/sales-orders/create-and-submit` 报错 `invalid literal for int() with base 10: ''`。

**根本原因**：前端在提交订单明细时，`warehouse_id` 字段传递的是空字符串 `""`（特别是当发货方式为"直运"时，不需要选择仓库）。后端模型 `SalesOrderItem.warehouse_id` 定义为 `IntField(null=True)`，Tortoise ORM 尝试将空字符串转换为整数时失败。

## What Changes

- **后端修改**：在 `sales_order_service_mysql.py` 的 `create_order` 方法中，处理明细数据时将空字符串的 `warehouse_id` 转换为 `None`

## Capabilities

### New Capabilities
无

### Modified Capabilities
无

## Impact

- **后端**：`backend/services/sales_order_service_mysql.py` - 处理空字符串 warehouse_id
