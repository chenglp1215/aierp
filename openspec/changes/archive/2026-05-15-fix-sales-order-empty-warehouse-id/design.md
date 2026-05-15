## Context

销售订单创建接口在处理明细数据时，前端传递的 `warehouse_id` 可能是空字符串（当发货方式为"直运"时）。后端模型 `SalesOrderItem.warehouse_id` 是 `IntField(null=True)`，Tortoise ORM 无法将空字符串转换为整数。

## Goals / Non-Goals

**Goals:**
- 修复后端处理空字符串 `warehouse_id` 的问题
- 确保直运订单可以正常创建

**Non-Goals:**
- 不修改前端逻辑
- 不修改数据库模型

## Decisions

### 1. 后端转换空字符串为 None

**决定**：在创建订单明细前，将空字符串的 `warehouse_id` 转换为 `None`

**理由**：
- 最小改动，只修改后端服务层
- 符合数据库模型定义（`null=True`）
- 不影响其他功能

**实现位置**：`backend/services/sales_order_service_mysql.py` 的 `create_order` 方法

```python
# 处理空字符串 warehouse_id
warehouse_id = item.get("warehouse_id")
if warehouse_id == "" or warehouse_id is None:
    warehouse_id = None
```

## Risks / Trade-offs

- **风险**：其他整数字段可能也有类似问题
  - **缓解**：检查并处理所有可能为空字符串的整数字段
