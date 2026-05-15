## Context

当前销售订单模块存在前后端数据结构不一致问题：

**后端返回结构（扁平字段）：**
```json
{
  "order_status": "audited",
  "delivery_status": "none",
  "receive_status": "none",
  "invoice_status": "none"
}
```

**前端详情页期望结构（嵌套字段）：**
```javascript
order.status?.order_status
order.status?.delivery_status
order.status?.receive_status
order.status?.invoice_status
```

**前端列表页使用字段（不匹配）：**
```javascript
order.status  // 期望订单状态
order.payment_status  // 付款状态（后端不存在）
```

## Goals / Non-Goals

**Goals:**
- 修复详情页状态显示，使其正确读取后端返回的扁平字段
- 修复列表页状态显示，使用正确的字段名
- 统一状态映射表，确保与后端枚举值一致

**Non-Goals:**
- 不修改后端 API 结构（保持扁平字段设计）
- 不添加新状态字段
- 不修改数据库模型

## Decisions

### 1. 前端适配后端扁平结构

**选择：** 在前端直接使用扁平字段，不创建嵌套对象

**理由：**
- 后端 `to_dict()` 方法返回扁平字段，这是合理的设计
- 前端适配后端是更简单的方案，无需修改后端
- 避免在 API 层添加额外的数据转换逻辑

**替代方案（已否决）：**
- 后端返回嵌套 `status` 对象 → 需修改 `to_dict()` 方法，影响范围大
- 前端添加数据转换层 → 增加复杂度，不必要

### 2. 移除不存在的 payment_status

**选择：** 从列表页移除付款状态列

**理由：**
- 后端模型中没有 `payment_status` 字段
- 当前付款状态显示为空是正确行为（字段不存在）
- 如需付款状态，应作为独立需求另行开发

### 3. 统一状态映射表

**选择：** 使用详情页的状态映射表作为标准，更新列表页

**理由：**
- 详情页的状态映射与后端枚举值一致
- 列表页使用的是旧版状态映射（draft/pending/confirmed 等），与当前后端不匹配

## Risks / Trade-offs

**风险：状态映射不一致导致显示错误**
→ 缓解：使用详情页已验证的状态映射表

**风险：列表页移除付款状态可能影响用户习惯**
→ 缓解：付款状态本就不存在数据，移除空列是正确行为