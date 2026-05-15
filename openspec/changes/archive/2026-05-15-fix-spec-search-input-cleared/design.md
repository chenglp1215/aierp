## Context

当前 `SalesOrderWorkspace.vue` 的商品搜索输入框使用 `:value` 绑定到 `item.product_name`，导致用户输入的搜索关键字无法正确显示。需要参考 `SalesOrderCreate.vue` 的实现，添加 `productSearchKeywords` 变量来保存每个订单行的搜索关键字。

## Goals / Non-Goals

**Goals:**
- 添加 `productSearchKeywords` 变量保存搜索关键字
- 修改输入框绑定逻辑，优先显示搜索关键字
- 修改 `handleProductSearch` 函数接收索引参数
- 选择规格后清空搜索关键字

**Non-Goals:**
- 不修改后端代码
- 不修改搜索 API

## Decisions

### 1. 搜索关键字存储

**决定**: 使用 `ref<Record<number, string>>` 存储每个订单行的搜索关键字

**理由**:
- 与 `SalesOrderCreate.vue` 实现一致
- 支持多订单行独立搜索
- 响应式更新

### 2. 输入框绑定逻辑

**决定**: 使用 `:value="productSearchKeywords[index] ?? item.product_name ..."`

**理由**:
- 优先显示用户输入的搜索关键字
- 如果没有搜索关键字，显示已选商品名称
- 与 `SalesOrderCreate.vue` 实现一致

## Risks / Trade-offs

- **状态管理复杂度**: 增加了一个额外的状态变量
  - **缓解**: 参考已有实现，保持一致性