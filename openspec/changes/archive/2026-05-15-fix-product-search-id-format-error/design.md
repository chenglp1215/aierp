## Context

当前系统商品搜索功能存在路由缺失问题。前端 `SalesOrderWorkspace.vue` 组件在商品搜索时并行调用两个 API：
1. `productApi.search(keyword)` - 请求 `/products/search`（后端不存在此路由）
2. `productApi.searchSpecs(keyword)` - 请求 `/products/specs/search`（正常工作）

根据用户需求，商品搜索只需要搜索规格编码，不需要搜索产品。当前实现中 `productApi.search` 调用了一个不存在的路由，导致 FastAPI 将 `/products/search` 匹配到 `/{product_id}` 路由，"search" 字符串被传入 `to_int_id()` 函数，抛出 "无效的ID格式" 错误。

## Goals / Non-Goals

**Goals:**
- 移除前端对 `productApi.search` 的调用
- 简化搜索逻辑，只使用 `productApi.searchSpecs` 搜索规格编码
- 修复 "无效的ID格式" 错误

**Non-Goals:**
- 不添加后端 `/products/search` 路由（用户不需要搜索产品）
- 不修改规格搜索的后端实现

## Decisions

### 1. 修改前端搜索逻辑

**决定**: 移除 `productApi.search` 调用，只保留 `productApi.searchSpecs`

**理由**:
- 用户明确表示只需要搜索规格编码
- 减少不必要的 API 调用
- 简化代码逻辑

### 2. 简化搜索结果处理

**决定**: 直接使用 `searchSpecs` 返回的结果，不再构建商品树

**理由**:
- 规格搜索结果已包含 `product_name` 和 `product_code` 字段
- 前端可以直接展示规格列表，无需额外的商品树结构
- 减少代码复杂度

## Risks / Trade-offs

- **UI 变化风险**: 原有商品树展示方式可能需要调整
  - **缓解**: 规格搜索结果已包含商品信息，可以直接展示规格列表