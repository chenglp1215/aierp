## Context

销售订单模块已完成从 MongoDB 到 MySQL 的重构迁移，使用 Tortoise ORM 作为 ORM 框架。当前需要：
1. 验证重构后的 API 接口功能正确性
2. 更新接口文档以反映最新的数据结构和接口定义

**当前技术栈**：
- 后端：Python, FastAPI, Tortoise ORM, MySQL
- 测试框架：pytest, httpx (异步 HTTP 客户端)
- 数据库：MySQL (erp_test)

**API 接口清单**（共 11 个）：
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/sales-orders/` | 创建销售订单 |
| POST | `/api/v1/sales-orders/create-and-submit` | 创建并提交订单 |
| GET | `/api/v1/sales-orders/` | 获取订单列表 |
| GET | `/api/v1/sales-orders/{order_no}` | 获取订单详情 |
| PUT | `/api/v1/sales-orders/{order_no}` | 更新订单 |
| DELETE | `/api/v1/sales-orders/{order_no}` | 删除订单 |
| POST | `/api/v1/sales-orders/{order_no}/submit` | 提交审核 |
| POST | `/api/v1/sales-orders/{order_no}/approve` | 审核通过 |
| POST | `/api/v1/sales-orders/{order_no}/reject` | 驳回订单 |
| POST | `/api/v1/sales-orders/{order_no}/cancel` | 取消订单 |
| GET | `/api/v1/sales-orders/{order_no}/status-flows` | 获取状态流转记录 |

## Goals / Non-Goals

**Goals:**
- 生成完整的 API 测试脚本，覆盖所有 11 个接口
- 测试正常流程和边界条件
- 验证状态流转逻辑的正确性
- 更新接口文档，反映 MySQL 迁移后的数据结构变更

**Non-Goals:**
- 不涉及前端代码变更
- 不涉及后端业务逻辑修改
- 不涉及性能测试

## Decisions

### 1. 测试脚本设计

**决策**：使用 pytest + httpx 异步测试

**理由**：
- 项目已使用 FastAPI，httpx 原生支持异步
- pytest 提供丰富的 fixture 和断言功能
- 可复用现有的测试基础设施

**测试用例设计**：
1. **创建订单测试**：验证订单号生成、金额计算、明细创建
2. **查询测试**：列表分页、条件筛选、详情查询
3. **更新测试**：仅草稿状态可修改
4. **删除测试**：仅草稿或已取消状态可删除
5. **状态流转测试**：draft → pending → audited → cancelled

### 2. 文档更新策略

**决策**：更新两处文档

**位置**：
- `.project_docs/backend/项目模块说明.md` — 模块概览
- `app/routers/api_docs/sales_order.md` — 详细接口文档（如不存在则创建）

**内容变更**：
- 更新数据模型字段（MySQL 表结构）
- 更新状态枚举值（OrderStatus 新增 PENDING）
- 更新响应格式示例

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 测试数据污染数据库 | 使用独立的测试数据库或测试后清理数据 |
| 后端服务未启动 | 测试前检查服务状态，提供启动命令 |
| 依赖模块数据缺失 | 测试前创建必要的客户、商品、仓库数据 |
