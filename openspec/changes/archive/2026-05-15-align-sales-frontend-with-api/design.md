## Context

前端销售订单模块使用旧的 MongoDB 版本 API 设计，后端已迁移到 MySQL 并重构了接口。主要差异：

| 方面 | 前端（旧） | 后端（新） |
|------|-----------|-----------|
| 状态操作 | `updateOrderStatus(orderNo, status)` | `submit`/`approve`/`reject`/`cancel` 独立接口 |
| 商品明细 | 传 `product_id`, `brand_id`, `product_name`, `brand_name` | 只需 `spec_id`, `warehouse_id` |
| 发货方式 | 中文：直运/物流/自提/送货 | 英文：`direct`/`warehouse` |
| 状态枚举 | 缺少 `pending` | 包含 `pending`（待审核） |
| 响应字段 | `create_time`, `invoice_info` | `created_at`, 无 `invoice_info` |

## Goals / Non-Goals

**Goals:**
- 前端 API 调用与后端接口完全对称
- 商品明细只传必要的外键字段
- 支持完整的订单状态流转（包括驳回）
- 发货方式正确映射

**Non-Goals:**
- 不修改后端 API（后端已完成重构）
- 不修改数据库结构
- 不涉及开票信息功能（后端暂未实现）

## Decisions

### 1. API 接口重构策略

**决策**: 直接重构 `salesOrderApi`，移除旧接口，添加新接口

**理由**: 
- 旧接口 `updateOrderStatus` 已被后端移除
- 新接口语义更清晰：`submit`（提交审核）、`approve`（审核通过）、`reject`（驳回）、`cancel`（取消）
- 避免维护兼容层增加复杂度

**新接口设计**:
```typescript
export const salesOrderApi = {
  // 列表和详情保持不变
  list: (params) => apiService.get('/sales-orders/', params),
  getByOrderNo: (orderNo) => apiService.get(`/sales-orders/${orderNo}`),
  
  // 创建接口：items 只需 spec_id 和 warehouse_id
  create: (data) => apiService.post('/sales-orders/', data),
  createAndSubmit: (data) => apiService.post('/sales-orders/create-and-submit', data),
  
  // 更新接口
  update: (orderNo, data) => apiService.put(`/sales-orders/${orderNo}`, data),
  
  // 删除接口保持不变
  delete: (orderNo) => apiService.delete(`/sales-orders/${orderNo}`),
  
  // 新的状态操作接口
  submit: (orderNo) => apiService.post(`/sales-orders/${orderNo}/submit`),
  approve: (orderNo) => apiService.post(`/sales-orders/${orderNo}/approve`),
  reject: (orderNo) => apiService.post(`/sales-orders/${orderNo}/reject`),
  cancel: (orderNo) => apiService.post(`/sales-orders/${orderNo}/cancel`),
  
  // 状态流转记录保持不变
  getStatusFlows: (orderNo) => apiService.get(`/sales-orders/${orderNo}/status-flows`),
  
  // 下推采购保持不变
  pushToPurchase: (orderNo, items) => apiService.post(`/sales-orders/${orderNo}/push-to-purchase`, { items })
}
```

### 2. 商品明细数据结构

**决策**: 前端只传 `spec_id` 和 `warehouse_id`，其他信息后端通过外键获取

**请求体结构**:
```typescript
items: [{
  row_no: number,
  spec_id: number,       // 规格ID（外键）
  product_code?: string, // 商品编码（快照，可选）
  spec_code?: string,    // 规格编码（快照，可选）
  warehouse_id?: number, // 仓库ID（外键，直运时可不传）
  qty: number,
  price: number,
  discount?: number,     // 默认 1.0
  shipping_method: 'direct' | 'warehouse'
}]
```

**响应体结构**（后端返回）:
```typescript
items: [{
  id: number,
  sales_order_id: number,
  row_no: number,
  product_id: number,      // 通过 spec.product 获取
  product_code: string,    // 快照
  product_name: string,    // 通过 spec.product.name 获取
  spec_id: number,
  spec_code: string,       // 快照
  brand_id: number,        // 通过 spec.product.brand 获取
  brand_name: string,      // 通过 spec.product.brand.name 获取
  warehouse_id: number,
  warehouse_name: string,  // 通过 warehouse.name 获取
  qty: number,
  price: number,
  discount: number,
  discounted_price: number,
  amt: number,
  shipping_method: string, // 中文：直运/仓库发货
  pushed: boolean,
  out_qty: number,
  return_qty: number,
  created_at: string,
  updated_at: string
}]
```

### 3. 发货方式映射

**决策**: 前端发送英文值，后端返回中文值

**映射表**:
| 前端发送 | 后端返回 | 说明 |
|---------|---------|------|
| `direct` | `直运` | 直运 |
| `warehouse` | `仓库发货` | 仓库发货 |

前端下拉选项改为：
```typescript
const shippingMethodOptions = [
  { value: 'direct', label: '直运' },
  { value: 'warehouse', label: '仓库发货' }
]
```

### 4. 状态流转按钮逻辑

**决策**: 根据当前状态显示对应操作按钮

| 当前状态 | 可用操作 |
|---------|---------|
| `draft` | 编辑、提交审核、删除、取消 |
| `pending` | 审核通过、驳回 |
| `audited` | 下推采购、关闭、取消 |
| `partially_pushed_to_purchase` | 下推采购、关闭、取消 |
| `pushed_to_purchase` | 关闭、取消 |
| `closed` | 无 |
| `cancelled` | 无 |

## Risks / Trade-offs

**风险1**: 前端组件分散在多个文件，可能遗漏某些调用点
→ **缓解**: 使用 Grep 全面搜索 `salesOrderApi` 和 `updateOrderStatus` 的所有调用

**风险2**: 发货方式映射变更可能影响现有订单显示
→ **缓解**: 后端已返回中文值，前端只需调整下拉选项的 value

**风险3**: 移除 `invoice_info` 相关功能可能影响用户体验
→ **缓解**: 后端暂未实现开票功能，前端暂时隐藏相关 UI

## Migration Plan

1. **Phase 1**: 重构 `api.ts` 中的 `salesOrderApi`
2. **Phase 2**: 更新 `SalesOrderWorkspace.vue` 使用新接口
3. **Phase 3**: 更新 `SalesOrderCreate.vue` 商品明细结构
4. **Phase 4**: 更新 `SalesOrderList.vue` 和 `SalesOrderDetail.vue`
5. **Phase 5**: 测试完整流程

无需数据库迁移，无需后端修改。

## Open Questions

- 开票信息功能何时实现？暂不在本次变更范围。