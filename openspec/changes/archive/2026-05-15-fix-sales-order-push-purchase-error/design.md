## Context

当前系统使用统一的 API 响应格式 `{status, message, result, exc}`，前端 `ApiService.request<T>()` 方法会自动解包 `result` 字段（如果存在），直接返回 `result` 的内容给调用方。

问题出在部分前端组件在调用 API 后，仍然尝试访问 `response.result`，导致获取到 `undefined`。

**涉及的代码路径：**
- `web/src/services/api.ts` 第 112-115 行：解包逻辑
- `web/src/components/workspace/SalesOrderWorkspace.vue` 第 1140-1142 行
- `web/src/components/workspace/SalesOrderDetail.vue` 第 88-92 行、第 190-192 行

## Goals / Non-Goals

**Goals:**
- 修复下推采购功能的报错
- 修复订单详情页面不展示的问题
- 统一 API 调用的返回值处理方式

**Non-Goals:**
- 不修改 API 服务层的解包逻辑
- 不修改后端接口格式
- 不修改其他正常工作的组件

## Decisions

### 决策 1：直接移除 `.result` 访问

**选择理由：**
- API 服务层已经解包，直接返回订单对象
- 保持与其他正常工作组件的一致性
- 最小改动范围

**备选方案：**
- 修改 API 服务层不解包：影响范围大，可能破坏其他功能
- 添加类型检查：增加复杂度，不必要

### 决策 2：修复所有相关位置

需要修复的位置：
1. `SalesOrderWorkspace.vue` 第 1141 行：`const fullOrder = orderRes.result`
2. `SalesOrderDetail.vue` 第 91 行：`order.value = orderRes.result`
3. `SalesOrderDetail.vue` 第 191 行：`const fullOrder = orderRes.result`

## Risks / Trade-offs

**风险 1：其他地方可能也有类似问题**
→ 缓解：本次只修复已知问题，后续可全局搜索排查

**风险 2：修复后功能回归**
→ 缓解：修复后验证下推采购和详情页面功能正常
