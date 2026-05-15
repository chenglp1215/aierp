## Why

销售订单模块已完成从 MongoDB 到 MySQL 的重构迁移，但 API 接口文档尚未同步更新。为确保接口文档与实际代码一致，需要：
1. 基于重构后的代码生成 API 测试脚本
2. 执行接口测试验证功能正确性
3. 更新接口文档以反映最新的数据结构和接口定义

## What Changes

- 生成销售订单模块 API 测试脚本（Python pytest）
- 执行接口测试，验证 CRUD 和状态流转功能
- 更新 `.project_docs/backend/项目模块说明.md` 中销售订单模块的 API 文档
- 更新或创建 `app/routers/api_docs/sales_order.md` 详细接口文档

## Capabilities

### New Capabilities

- `sales-order-api-testing`: 销售订单模块 API 测试脚本，覆盖创建、查询、更新、删除、状态流转等接口

### Modified Capabilities

- `sales-order-module-docs`: 更新销售订单模块 API 文档，反映 MySQL 迁移后的数据结构和接口变更

## Impact

- **后端代码**: 无变更（仅测试和文档）
- **测试脚本**: 新增 `backend/tests/test_sales_order_api.py`
- **文档更新**: `.project_docs/backend/项目模块说明.md`、`app/routers/api_docs/sales_order.md`
