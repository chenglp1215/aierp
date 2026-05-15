## Context

采购单模块已完成外键关联重构：
- `PurchaseOrder` 添加 `brand` 外键关联 Brand 表
- `PurchaseOrderItem` 添加 `spec`、`warehouse` 外键关联 ProductSpec、Warehouse 表
- 移除冗余字段 `brand_name`、`warehouse_name`
- `to_dict()` 方法通过关联查询返回名称字段

接口文档需要更新以反映这些变化。

## Goals / Non-Goals

**Goals:**
1. 更新采购单创建模型，移除冗余字段作为传入参数
2. 更新采购单明细数据结构，说明外键关联方式
3. 更新响应数据结构说明，明确字段来源
4. 保持文档格式一致性

**Non-Goals:**
1. 不修改 API 接口定义
2. 不添加新的接口
3. 不修改前端代码

## Decisions

### 1. 文档更新策略

**决策：** 保持响应格式说明不变，更新字段来源说明

**理由：**
- API 响应格式保持兼容，字段名不变
- 只需说明字段来源变化（从冗余存储改为关联查询）
- 前端无需修改，只需了解后端实现变化

### 2. 请求参数更新

**决策：** 移除冗余字段作为传入参数

**变更：**
- 创建采购单时，不再需要传入 `brand_name`、`warehouse_name`
- 明确 `spec_id` 为必填字段
- `brand_id`、`product_id` 可选（通过 spec 关联获取）

### 3. 数据模型说明更新

**决策：** 添加外键关联说明

**新增内容：**
- 说明 PurchaseOrderItem 通过 `spec` 外键关联 ProductSpec
- ProductSpec 关联 Product，Product 关联 Brand
- 名称字段通过关联链查询获取

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 文档与代码不一致 | 参照最新模型定义更新文档 |
| 遗漏字段说明 | 对照 to_dict() 方法检查所有返回字段 |