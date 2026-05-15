# 销售订单前端 API 对齐实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构前端销售订单模块，使 API 调用、参数结构与后端 MySQL 版本完全对称

**Architecture:** 直接重构 `salesOrderApi` 接口定义，更新组件使用新的状态操作接口（submit/approve/reject/cancel），商品明细只传 spec_id 和 warehouse_id 外键字段

**Tech Stack:** Vue 3, TypeScript, Axios, vxe-table

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `web/src/services/api.ts` | API 接口定义 | 修改 |
| `web/src/components/workspace/SalesOrderWorkspace.vue` | 主工作区组件 | 修改 |
| `web/src/components/workspace/SalesOrderCreate.vue` | 创建订单组件 | 修改 |
| `web/src/components/workspace/SalesOrderList.vue` | 列表组件 | 修改 |
| `web/src/components/workspace/SalesOrderDetail.vue` | 详情组件 | 修改 |

---

### Task 1: 重构 API 接口定义

**Files:**
- Modify: `web/src/services/api.ts:257-414`

- [ ] **Step 1: 重构 salesOrderApi 接口**

将 `web/src/services/api.ts` 中的 `salesOrderApi` 对象（第 257-414 行）替换为以下内容：

```typescript
export const salesOrderApi = {
  // 获取订单列表
  list: (params: { page?: number; page_size?: number; status?: string; customer_id?: string | number; order_no?: string; keyword?: string }) => {
    return apiService.get<any>('/sales-orders/', params)
  },

  // 获取订单详情
  getByOrderNo: (orderNo: string) => {
    return apiService.get<any>(`/sales-orders/${orderNo}`)
  },

  // 创建订单
  create: (data: {
    order_date: string
    customer_id: string | number
    customer_name?: string
    sale_user_id?: string | number
    deliver_info?: {
      addr: string
      province: string
      city: string
      person_name: string
      person_tel: string
    }
    expect_deliver_date?: string
    settle_type?: string
    tax_rate?: number
    remark?: string
    items: Array<{
      row_no: number
      spec_id?: number
      product_code?: string
      spec_code?: string
      warehouse_id?: number
      qty: number
      price: number
      discount?: number
      shipping_method: 'direct' | 'warehouse'
    }>
  }) => {
    return apiService.post<any>('/sales-orders/', data)
  },

  // 创建并提交订单（直接审核通过）
  createAndSubmit: (data: {
    order_date: string
    customer_id: string | number
    customer_name?: string
    sale_user_id?: string | number
    deliver_info?: {
      addr: string
      province: string
      city: string
      person_name: string
      person_tel: string
    }
    expect_deliver_date?: string
    settle_type?: string
    tax_rate?: number
    remark?: string
    items: Array<{
      row_no: number
      spec_id?: number
      product_code?: string
      spec_code?: string
      warehouse_id?: number
      qty: number
      price: number
      discount?: number
      shipping_method: 'direct' | 'warehouse'
    }>
  }) => {
    return apiService.post<any>('/sales-orders/create-and-submit', data)
  },

  // 更新订单
  update: (orderNo: string, data: {
    order_date?: string
    customer_id?: string | number
    customer_name?: string
    expect_deliver_date?: string
    settle_type?: string
    remark?: string
    items?: Array<{
      row_no: number
      spec_id?: number
      product_code?: string
      spec_code?: string
      warehouse_id?: number
      qty: number
      price: number
      discount?: number
      shipping_method: 'direct' | 'warehouse'
    }>
  }) => {
    return apiService.put<any>(`/sales-orders/${orderNo}`, data)
  },

  // 删除订单
  delete: (orderNo: string) => {
    return apiService.delete<any>(`/sales-orders/${orderNo}`)
  },

  // 提交审核（draft → pending）
  submit: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/submit`)
  },

  // 审核通过（pending → audited）
  approve: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/approve`)
  },

  // 驳回（pending → draft）
  reject: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/reject`)
  },

  // 取消订单
  cancel: (orderNo: string) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/cancel`)
  },

  // 获取订单状态流转记录
  getStatusFlows: (orderNo: string) => {
    return apiService.get<any>(`/sales-orders/${orderNo}/status-flows`)
  },

  // 下推采购
  pushToPurchase: (orderNo: string, items: { row_no: number }[]) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/push-to-purchase`, { items })
  }
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd web && npm run build`
Expected: 编译成功，无类型错误

- [ ] **Step 3: 提交 API 接口重构**

```bash
git add web/src/services/api.ts
git commit -m "refactor: 重构 salesOrderApi 接口对齐后端 MySQL 版本

- 移除 updateOrderStatus、updateDeliveryStatus 等旧接口
- 添加 submit、approve、reject、cancel 独立状态操作接口
- 更新 items 类型定义，只需 spec_id 和 warehouse_id
- 更新 shipping_method 类型为 direct/warehouse

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: 更新 SalesOrderWorkspace 组件

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue`

- [ ] **Step 1: 更新发货方式选项**

找到 `shippingMethodOptions` 定义（约第 170-175 行），修改为：

```typescript
const shippingMethodOptions = [
  { value: 'direct', label: '直运' },
  { value: 'warehouse', label: '仓库发货' }
]
```

- [ ] **Step 2: 更新状态操作方法**

找到 `handleAuditOrder` 方法（约第 1085-1104 行），修改为使用 `approve` 接口：

```typescript
const handleAuditOrder = async () => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.approve(actionTargetOrderNo.value)
    window.showToast('订单审核通过', 'success')
    showAuditConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.order_no === actionTargetOrderNo.value) {
      selectedOrder.value = { ...selectedOrder.value, order_status: 'audited' }
      await refreshFlows(actionTargetOrderNo.value)
    }
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}
```

- [ ] **Step 3: 更新取消订单方法**

找到 `handleCancelOrder` 方法（约第 1210-1228 行），修改为使用 `cancel` 接口：

```typescript
const handleCancelOrder = async () => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.cancel(actionTargetOrderNo.value)
    window.showToast('订单取消成功', 'success')
    showCancelConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.order_no === actionTargetOrderNo.value) {
      selectedOrder.value = { ...selectedOrder.value, order_status: 'cancelled' }
      await refreshFlows(actionTargetOrderNo.value)
    }
  } catch (error: any) {
    window.showToast(error.message || '取消失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}
```

- [ ] **Step 4: 添加提交审核方法**

在 `handleAuditOrder` 方法之前添加：

```typescript
const handleSubmitOrder = async (orderNo: string) => {
  actionLoading.value = true
  try {
    await salesOrderApi.submit(orderNo)
    window.showToast('订单已提交审核', 'success')
    loadOrders()
  } catch (error: any) {
    window.showToast(error.message || '提交失败', 'error')
  } finally {
    actionLoading.value = false
  }
}
```

- [ ] **Step 5: 添加驳回订单方法**

在 `handleAuditOrder` 方法之后添加：

```typescript
const handleRejectOrder = async () => {
  if (!actionTargetOrderNo.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.reject(actionTargetOrderNo.value)
    window.showToast('订单已驳回', 'success')
    showRejectConfirm.value = false
    loadOrders()
    if (selectedOrder.value?.order_no === actionTargetOrderNo.value) {
      selectedOrder.value = { ...selectedOrder.value, order_status: 'draft' }
      await refreshFlows(actionTargetOrderNo.value)
    }
  } catch (error: any) {
    window.showToast(error.message || '驳回失败', 'error')
  } finally {
    actionLoading.value = false
    actionTargetOrderNo.value = null
  }
}
```

- [ ] **Step 6: 添加驳回确认弹窗状态**

在 `showCancelConfirm` 定义附近添加：

```typescript
const showRejectConfirm = ref(false)
```

- [ ] **Step 7: 更新列表操作按钮模板**

找到操作列模板（约第 1474-1486 行），修改为：

```html
<span class="action-btns">
  <button class="btn-link" @click="emit('navigate', 'sales-order-detail', { orderNo: row.order_no })">详情</button>
  <button class="btn-link" @click="openEditOrder(row)" v-if="row.order_status === 'draft'">编辑</button>
  <button class="btn-link" @click="handleSubmitOrder(row.order_no)" v-if="row.order_status === 'draft'">提交审核</button>
  <button class="btn-link success" @click="confirmAudit(row.order_no)" v-if="row.order_status === 'pending'">审核通过</button>
  <button class="btn-link warning" @click="confirmReject(row.order_no)" v-if="row.order_status === 'pending'">驳回</button>
  <button class="btn-link primary" @click="confirmPushPurchase(row.order_no)" v-if="row.order_status === 'audited' || row.order_status === 'partially_pushed_to_purchase'">下推采购</button>
  <button class="btn-link warning" @click="confirmClose(row.order_no)" v-if="row.order_status === 'audited' || row.order_status === 'partially_pushed_to_purchase'">关闭</button>
  <button class="btn-link danger" @click="confirmCancel(row.order_no)" v-if="['draft', 'pending', 'audited', 'partially_pushed_to_purchase'].includes(row.order_status)">取消</button>
  <button class="btn-link danger" @click="confirmDelete(row.order_no)" v-if="row.order_status === 'draft'">删除</button>
</span>
```

- [ ] **Step 8: 添加驳回确认弹窗方法**

在 `confirmCancel` 方法附近添加：

```typescript
const confirmReject = (orderNo: string) => {
  actionTargetOrderNo.value = orderNo
  showRejectConfirm.value = true
}
```

- [ ] **Step 9: 添加驳回确认弹窗模板**

在取消确认弹窗之后添加驳回确认弹窗：

```html
<!-- Reject Confirm Modal -->
<div class="modal-overlay" v-if="showRejectConfirm">
  <div class="modal confirm-modal">
    <div class="modal-header">
      <h3>确认驳回</h3>
    </div>
    <div class="modal-body">
      <p>确定要驳回该订单吗？驳回后订单将返回草稿状态。</p>
    </div>
    <div class="modal-footer">
      <button class="btn-secondary" @click="showRejectConfirm = false">取消</button>
      <button class="btn-warning" @click="handleRejectOrder" :disabled="actionLoading">
        {{ actionLoading ? '驳回中...' : '确认驳回' }}
      </button>
    </div>
  </div>
</div>
```

- [ ] **Step 10: 移除发货/收货/开票状态更新方法**

删除以下方法：
- `handleUpdateDeliveryStatus`
- `handleUpdateReceiveStatus`
- `handleUpdateInvoiceStatus`

- [ ] **Step 11: 隐藏详情页状态更新区域**

找到详情页状态更新区域（约第 1898-1938 行），删除或注释掉整个 `status-actions` 区域。

- [ ] **Step 12: 提交组件更新**

```bash
git add web/src/components/workspace/SalesOrderWorkspace.vue
git commit -m "refactor: 更新 SalesOrderWorkspace 使用新状态操作接口

- 发货方式选项改为英文值 direct/warehouse
- 添加提交审核、驳回功能
- 移除旧的 updateOrderStatus 调用
- 隐藏发货/收货/开票状态更新功能

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: 更新 SalesOrderCreate 组件

**Files:**
- Modify: `web/src/components/workspace/SalesOrderCreate.vue`

- [ ] **Step 1: 更新发货方式选项**

找到 `shippingMethodOptions` 定义（约第 83-88 行），修改为：

```typescript
const shippingMethodOptions = [
  { value: 'direct', label: '直运' },
  { value: 'warehouse', label: '仓库发货' }
]
```

- [ ] **Step 2: 更新商品明细提交数据结构**

找到 `handleSaveOrder` 方法中的 `items` 映射（约第 603-618 行），修改为：

```typescript
items: orderForm.value.items.map(item => ({
  row_no: item.row_no,
  spec_id: item.spec_id ? Number(item.spec_id) : undefined,
  product_code: item.product_code || undefined,
  spec_code: item.spec_code || undefined,
  warehouse_id: item.warehouse_id ? Number(item.warehouse_id) : undefined,
  qty: item.qty,
  price: item.price,
  discount: item.discount,
  shipping_method: item.shipping_method
}))
```

- [ ] **Step 3: 更新初始化商品明细**

找到 `addOrderItem` 方法（约第 540-556 行），确保 `shipping_method` 默认值为英文：

```typescript
const addOrderItem = () => {
  orderForm.value.items.push({
    row_no: orderForm.value.items.length + 1,
    product_id: '',
    spec_id: '',
    qty: 1,
    price: 0,
    discount: 1,
    discounted_price: 0,
    amt: 0,
    warehouse_id: '',
    shipping_method: 'direct',
    out_qty: 0,
    return_qty: 0,
    remain_out_qty: 0
  })
}
```

- [ ] **Step 4: 提交组件更新**

```bash
git add web/src/components/workspace/SalesOrderCreate.vue
git commit -m "refactor: 更新 SalesOrderCreate 商品明细数据结构

- 发货方式选项改为英文值
- 商品明细只传 spec_id 和 warehouse_id 外键
- 移除冗余字段 product_id、brand_id 等

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: 更新 SalesOrderList 组件

**Files:**
- Modify: `web/src/components/workspace/SalesOrderList.vue`

- [ ] **Step 1: 更新状态映射添加 pending**

找到 `statusMap` 定义（约第 65-73 行），确保包含 `pending`：

```typescript
const statusMap: Record<string, { label: string; class: string }> = {
  draft: { label: '草稿', class: 'draft' },
  pending: { label: '待审核', class: 'pending' },
  audited: { label: '已审核', class: 'audited' },
  partially_pushed_to_purchase: { label: '部分下推采购', class: 'partial-pushed' },
  pushed_to_purchase: { label: '已下推采购', class: 'pushed' },
  closed: { label: '已关闭', class: 'closed' },
  cancelled: { label: '已取消', class: 'cancelled' }
}
```

- [ ] **Step 2: 添加 pending 状态样式**

在样式部分添加 pending 状态样式：

```css
.status-tag.pending { background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; }
```

- [ ] **Step 3: 更新操作按钮逻辑**

找到操作按钮模板（约第 714-719 行），修改为：

```html
<div class="action-buttons">
  <button class="btn-link" @click="openDetail(order)">详情</button>
  <button class="btn-link" @click="openEditOrder(order)" v-if="order.order_status === 'draft'">编辑</button>
  <button class="btn-link highlight" @click="handleApproveOrder(order.order_no)" v-if="order.order_status === 'pending'">审核通过</button>
  <button class="btn-link warning" @click="handleRejectOrder(order.order_no)" v-if="order.order_status === 'pending'">驳回</button>
  <button class="btn-link danger" @click="confirmDelete(order.order_no)" v-if="order.order_status === 'draft'">删除</button>
</div>
```

- [ ] **Step 4: 添加审核通过和驳回方法**

添加以下方法：

```typescript
const handleApproveOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.approve(orderNo)
    window.showToast('订单审核通过', 'success')
    const index = orders.value.findIndex(o => o.order_no === orderNo)
    if (index !== -1) {
      orders.value[index] = { ...orders.value[index], order_status: 'audited' }
    }
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  }
}

const handleRejectOrder = async (orderNo: string) => {
  try {
    await salesOrderApi.reject(orderNo)
    window.showToast('订单已驳回', 'success')
    const index = orders.value.findIndex(o => o.order_no === orderNo)
    if (index !== -1) {
      orders.value[index] = { ...orders.value[index], order_status: 'draft' }
    }
  } catch (error: any) {
    window.showToast(error.message || '驳回失败', 'error')
  }
}
```

- [ ] **Step 5: 移除旧的 handleConfirmOrder 方法**

删除 `handleConfirmOrder` 方法（约第 567-585 行）。

- [ ] **Step 6: 提交组件更新**

```bash
git add web/src/components/workspace/SalesOrderList.vue
git commit -m "refactor: 更新 SalesOrderList 支持 pending 状态

- 添加 pending 状态映射和样式
- 添加审核通过和驳回操作按钮
- 移除旧的 confirm 方法

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: 更新 SalesOrderDetail 组件

**Files:**
- Modify: `web/src/components/workspace/SalesOrderDetail.vue`

- [ ] **Step 1: 检查文件是否存在并读取内容**

如果 `SalesOrderDetail.vue` 文件存在，读取并更新其中的状态操作方法。

- [ ] **Step 2: 提交组件更新（如需要）**

```bash
git add web/src/components/workspace/SalesOrderDetail.vue
git commit -m "refactor: 更新 SalesOrderDetail 使用新状态操作接口

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: 测试验证

- [ ] **Step 1: 启动前端开发服务器**

Run: `cd web && npm run dev`
Expected: 服务启动成功

- [ ] **Step 2: 启动后端服务**

Run: `cd backend && venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
Expected: 后端服务启动成功

- [ ] **Step 3: 测试完整流程**

手动测试以下流程：
1. 创建草稿订单
2. 提交审核（draft → pending）
3. 审核通过（pending → audited）
4. 创建新订单，提交后驳回（pending → draft）
5. 取消订单测试

- [ ] **Step 4: 提交最终变更**

```bash
git add -A
git commit -m "test: 验证销售订单前端 API 对齐完成

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```
