## Context

当前系统存在两个 BUG：

1. **销售订单提交失败**：前端调用 `/api/v1/sales-orders/create-and-submit` 时，后端模型 `SalesOrder` 的 `customer_name` 字段定义为非空（`CharField(max_length=200)`），但前端提交数据中没有包含该字段，导致 Tortoise ORM 报错。

2. **规格库存详情接口缺失**：前端定义了 `getSpecStockDetail` API 调用 `/products/specs/{spec_id}/stock-detail`，但后端没有实现该路由。现有库存服务 `StockService.get_stock_status_by_spec_ids` 已经具备查询规格库存的能力。

## Goals / Non-Goals

**Goals:**
- 修复销售订单提交时 `customer_name` 为 null 的问题
- 实现规格库存详情查询接口

**Non-Goals:**
- 不修改数据库模型
- 不涉及其他订单类型或库存操作

## Decisions

### 1. 前端添加 customer_name 字段

**决定**：在前端提交订单数据时添加 `customer_name` 字段

**理由**：
- 后端模型 `customer_name` 是非空字段，必须传递
- 前端在选择客户时已经获取了客户名称，只需在提交数据中包含
- 这是最小改动方案，不需要修改后端模型

**替代方案**：
- 后端根据 `customer_id` 查询客户名称：增加额外数据库查询，性能开销

### 2. 后端新增库存详情接口

**决定**：在 `product_router` 中添加 `/specs/{spec_id}/stock-detail` 接口

**理由**：
- 复用现有 `StockService.get_stock_status_by_spec_ids` 方法
- 接口路径与前端 API 定义一致
- 返回格式与前端期望一致

**接口设计**：
```
GET /api/v1/products/specs/{spec_id}/stock-detail

Response:
{
  "status": "success",
  "message": "",
  "result": {
    "spec_id": 4,
    "items": [
      {
        "warehouse_id": 1,
        "warehouse_name": "主仓库",
        "quantity": 100
      }
    ],
    "total_quantity": 100
  }
}
```

## Risks / Trade-offs

- **风险**：前端可能存在其他地方调用订单创建 API 但未传递 `customer_name`
  - **缓解**：全局搜索确认所有调用点

- **风险**：库存接口返回格式可能与前端期望不完全一致
  - **缓解**：检查前端调用代码确认返回格式
