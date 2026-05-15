## Why

采购单模块已完成外键关联重构（参照销售订单重构方案），移除了冗余字段 `brand_name`、`warehouse_name`，改用 ForeignKeyField 关联查询。接口文档需要更新以反映这些变化，确保前端开发人员了解新的数据结构和字段来源。

**问题影响：**
1. 文档中仍显示已删除的冗余字段（如 `brand_name` 作为传入参数）
2. 文档未说明 `brand_name`、`warehouse_name` 等字段现在通过关联查询获取
3. 文档中的数据模型说明与实际实现不一致

## What Changes

### 需要更新的内容

**1. 采购单创建模型**
- 移除 `brand_name` 作为传入参数
- 说明 `brand_name` 通过 `brand_id` 关联查询获取

**2. 采购单明细数据结构**
- 移除 `brand_name`、`warehouse_name` 作为传入参数
- 添加 `spec_id` 作为必填字段（外键关联）
- 说明 `product_name`、`brand_name`、`warehouse_name` 通过关联查询获取
- 添加 `product_code`、`spec_code` 字段说明

**3. 响应数据结构**
- 更新字段说明，明确哪些字段通过关联查询获取
- 保持响应格式兼容（字段名不变，但来源变化）

## Capabilities

### New Capabilities

- `purchase-order-api-docs-update`: 采购单 API 文档更新，反映外键关联重构后的数据结构变化

### Modified Capabilities

- 无（文档更新不影响功能需求）

## Impact

- **文档文件**: `backend/app/routers/api_docs/purchase_order.md`
- **项目模块说明**: `.project_docs/backend/项目模块说明.md` 中的采购单部分
- **API 兼容性**: 响应格式保持兼容，前端无需修改