# 销售订单状态显示修复 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复销售订单列表页和详情页的状态字段显示问题，使前端正确读取后端返回的扁平状态字段。

**Architecture:** 前端直接使用后端返回的扁平字段（order_status、delivery_status、receive_status、invoice_status），移除不存在的 payment_status 字段引用，统一状态映射表。

**Tech Stack:** Vue 3, TypeScript, Composition API

---

## 文件结构

**修改文件：**
- `web/src/components/workspace/SalesOrderDetail.vue` - 详情页，修复状态字段引用
- `web/src/components/workspace/SalesOrderList.vue` - 列表页，修复状态字段引用和移除付款状态列

---

### Task 1: 修复 SalesOrderDetail.vue 状态字段引用

**Files:**
- Modify: `web/src/components/workspace/SalesOrderDetail.vue`

- [ ] **Step 1: 修复模板中的订单状态字段引用**

将模板中所有 `order.status?.order_status` 替换为 `order.order_status`：

```vue
<!-- 第 344-346 行：顶部状态标签 -->
<span class="status-tag" :class="getStatusClass(orderStatusMap, order.order_status)">
  {{ getStatusLabel(orderStatusMap, order.order_status) }}
</span>

<!-- 第 349 行：审核按钮条件 -->
<button v-if="order.order_status === 'draft'" class="btn-primary" @click="handleAudit" :disabled="actionLoading">审核通过</button>

<!-- 第 351 行：关闭按钮条件 -->
<button v-if="order.order_status === 'audited'" class="btn-warning" @click="handleClose" :disabled="actionLoading">关闭订单</button>

<!-- 第 352 行：取消按钮条件 -->
<button v-if="order.order_status === 'draft' || order.order_status === 'audited'" class="btn-danger" @click="handleCancel" :disabled="actionLoading">取消订单</button>

<!-- 第 378-379 行：状态信息区域 -->
<span class="status-tag" :class="getStatusClass(orderStatusMap, order.order_status)">{{ getStatusLabel(orderStatusMap, order.order_status) }}</span>
<select :value="order.order_status" @change="handleUpdateOrderStatus(($event.target as HTMLSelectElement).value)" class="status-select">
```

- [ ] **Step 2: 修复模板中的发货状态字段引用**

将模板中所有 `order.status?.delivery_status` 替换为 `order.delivery_status`：

```vue
<!-- 第 392-393 行 -->
<span class="status-tag" :class="getStatusClass(deliveryStatusMap, order.delivery_status)">{{ getStatusLabel(deliveryStatusMap, order.delivery_status) }}</span>
<select :value="order.delivery_status" @change="handleUpdateDeliveryStatus(($event.target as HTMLSelectElement).value)" class="status-select">
```

- [ ] **Step 3: 修复模板中的收货状态字段引用**

将模板中所有 `order.status?.receive_status` 替换为 `order.receive_status`：

```vue
<!-- 第 403-404 行 -->
<span class="status-tag" :class="getStatusClass(receiveStatusMap, order.receive_status)">{{ getStatusLabel(receiveStatusMap, order.receive_status) }}</span>
<select :value="order.receive_status" @change="handleUpdateReceiveStatus(($event.target as HTMLSelectElement).value)" class="status-select">
```

- [ ] **Step 4: 修复模板中的开票状态字段引用**

将模板中所有 `order.status?.invoice_status` 替换为 `order.invoice_status`：

```vue
<!-- 第 414-415 行 -->
<span class="status-tag" :class="getStatusClass(invoiceStatusMap, order.invoice_status)">{{ getStatusLabel(invoiceStatusMap, order.invoice_status) }}</span>
<select :value="order.invoice_status" @change="handleUpdateInvoiceStatus(($event.target as HTMLSelectElement).value)" class="status-select">
```

- [ ] **Step 5: 修复计算属性 canPushPurchase**

修改第 77-80 行的计算属性：

```typescript
const canPushPurchase = computed(() => {
  const s = order.value?.order_status
  return s === 'audited' || s === 'partially_pushed_to_purchase'
})
```

- [ ] **Step 6: 修复状态更新方法**

修改 handleUpdateOrderStatus 方法（第 122-134 行）：

```typescript
const handleUpdateOrderStatus = async (status: string) => {
  if (!order.value) return
  try {
    await salesOrderApi.updateOrderStatus(order.value.order_no, status)
    window.showToast('订单状态更新成功', 'success')
    order.value = { ...order.value, order_status: status }
    const flowsRes = await salesOrderApi.getStatusFlows(order.value.order_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
    loadOrder()
  }
}
```

修改 handleUpdateDeliveryStatus 方法（第 136-145 行）：

```typescript
const handleUpdateDeliveryStatus = async (status: string) => {
  if (!order.value) return
  try {
    await salesOrderApi.updateDeliveryStatus(order.value.order_no, status)
    window.showToast('发货状态更新成功', 'success')
    order.value = { ...order.value, delivery_status: status }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
}
```

修改 handleUpdateReceiveStatus 方法（第 147-156 行）：

```typescript
const handleUpdateReceiveStatus = async (status: string) => {
  if (!order.value) return
  try {
    await salesOrderApi.updateReceiveStatus(order.value.order_no, status)
    window.showToast('收货状态更新成功', 'success')
    order.value = { ...order.value, receive_status: status }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
}
```

修改 handleUpdateInvoiceStatus 方法（第 158-167 行）：

```typescript
const handleUpdateInvoiceStatus = async (status: string) => {
  if (!order.value) return
  try {
    await salesOrderApi.updateInvoiceStatus(order.value.order_no, status)
    window.showToast('开票状态更新成功', 'success')
    order.value = { ...order.value, invoice_status: status }
  } catch (error: any) {
    window.showToast(error.message || '状态更新失败', 'error')
  }
}
```

- [ ] **Step 7: 修复 handleAudit 方法**

修改第 170-184 行：

```typescript
const handleAudit = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.updateOrderStatus(order.value.order_no, 'audited')
    window.showToast('订单审核成功', 'success')
    order.value = { ...order.value, order_status: 'audited' }
    const flowsRes = await salesOrderApi.getStatusFlows(order.value.order_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '审核失败', 'error')
  } finally {
    actionLoading.value = false
  }
}
```

- [ ] **Step 8: 修复 handleClose 方法**

修改第 263-277 行：

```typescript
const handleClose = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.updateOrderStatus(order.value.order_no, 'closed')
    window.showToast('订单关闭成功', 'success')
    order.value = { ...order.value, order_status: 'closed' }
    const flowsRes = await salesOrderApi.getStatusFlows(order.value.order_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '关闭失败', 'error')
  } finally {
    actionLoading.value = false
  }
}
```

- [ ] **Step 9: 修复 handleCancel 方法**

修改第 279-293 行：

```typescript
const handleCancel = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    await salesOrderApi.updateOrderStatus(order.value.order_no, 'cancelled')
    window.showToast('订单取消成功', 'success')
    order.value = { ...order.value, order_status: 'cancelled' }
    const flowsRes = await salesOrderApi.getStatusFlows(order.value.order_no)
    flows.value = flowsRes.result || []
  } catch (error: any) {
    window.showToast(error.message || '取消失败', 'error')
  } finally {
    actionLoading.value = false
  }
}
```

- [ ] **Step 10: 提交详情页修复**

```bash
git add web/src/components/workspace/SalesOrderDetail.vue
git commit -m "fix: 修复销售订单详情页状态字段引用

- 将 order.status?.order_status 改为 order.order_status
- 将 order.status?.delivery_status 改为 order.delivery_status
- 将 order.status?.receive_status 改为 order.receive_status
- 将 order.status?.invoice_status 改为 order.invoice_status
- 修复状态更新方法中的字段引用

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: 修复 SalesOrderList.vue 状态字段引用

**Files:**
- Modify: `web/src/components/workspace/SalesOrderList.vue`

- [ ] **Step 1: 更新状态映射表**

替换第 63-77 行的状态映射表，使用与后端一致的枚举值：

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

const deliveryStatusMap: Record<string, { label: string; class: string }> = {
  none: { label: '未发货', class: 'none' },
  partial: { label: '部分发货', class: 'partial' },
  full: { label: '全部发货', class: 'full' }
}
```

- [ ] **Step 2: 移除付款状态映射表和相关代码**

删除第 73-77 行的 paymentStatusMap：

```typescript
// 删除以下代码
const paymentStatusMap: Record<string, { label: string; class: string }> = {
  unpaid: { label: '未付款', class: 'unpaid' },
  partial: { label: '部分付款', class: 'partial' },
  paid: { label: '已付款', class: 'paid' }
}
```

删除第 619 行的 getPaymentStatusInfo 函数：

```typescript
// 删除以下代码
const getPaymentStatusInfo = (status: string) => paymentStatusMap[status] || { label: status, class: '' }
```

- [ ] **Step 3: 修复模板中的状态字段引用**

修改表格中的状态列（第 713-721 行），将 `order.status` 改为 `order.order_status`，移除付款状态列：

```vue
<td>
  <span class="status-tag" :class="getStatusInfo(order.order_status).class">
    {{ getStatusInfo(order.order_status).label }}
  </span>
</td>
<td>{{ formatDate(order.order_date) }}</td>
```

- [ ] **Step 4: 移除付款状态列的表头和单元格**

修改表头（第 684-693 行），移除付款状态列：

```vue
<thead>
  <tr>
    <th style="width: 130px">订单编号</th>
    <th>客户名称</th>
    <th style="width: 100px">发货方式</th>
    <th style="width: 100px; text-align: right">订单金额</th>
    <th style="width: 80px">订单状态</th>
    <th style="width: 100px">下单日期</th>
    <th style="width: 200px">操作</th>
  </tr>
</thead>
```

修改表格数据行（第 702-732 行），移除付款状态列：

```vue
<tr v-else v-for="order in orders" :key="order.order_no">
  <td>{{ order.order_no }}</td>
  <td>{{ order.customer_name }}</td>
  <td>
    <span v-if="order.delivery_type === 'inventory'">
      库存发货
      <span v-if="order.warehouse_name" class="warehouse-tag">({{ order.warehouse_name }})</span>
    </span>
    <span v-else>采购直发</span>
  </td>
  <td style="text-align: right">{{ formatAmount(order.final_amount) }}</td>
  <td>
    <span class="status-tag" :class="getStatusInfo(order.order_status).class">
      {{ getStatusInfo(order.order_status).label }}
    </span>
  </td>
  <td>{{ formatDate(order.order_date) }}</td>
  <td>
    <div class="action-buttons">
      <button class="btn-link" @click="openDetail(order)">详情</button>
      <button class="btn-link" @click="openEditOrder(order)" v-if="order.order_status === 'draft'">编辑</button>
      <button class="btn-link highlight" @click="handleConfirmOrder(order.order_no)" v-if="order.order_status === 'pending'">确认</button>
      <button class="btn-link danger" @click="confirmDelete(order.order_no)" v-if="order.order_status === 'draft'">删除</button>
    </div>
  </td>
</tr>
```

- [ ] **Step 5: 更新加载空单元格的 colspan**

修改第 696-700 行的 colspan：

```vue
<tr v-if="loading">
  <td colspan="7" class="loading-cell">加载中...</td>
</tr>
<tr v-else-if="orders.length === 0">
  <td colspan="7" class="empty-cell">暂无数据</td>
</tr>
```

- [ ] **Step 6: 更新样式，添加新的状态样式类**

在第 1360-1369 行的状态样式后添加新样式：

```css
.status-tag.draft { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.pending { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.audited { background-color: rgba(59, 130, 246, 0.1); color: var(--accent-blue); }
.status-tag.partial-pushed { background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; }
.status-tag.pushed { background-color: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
.status-tag.closed { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
.status-tag.cancelled { background-color: rgba(239, 68, 68, 0.1); color: var(--accent-red); }
.status-tag.none { background-color: rgba(128, 128, 128, 0.1); color: var(--text-muted); }
.status-tag.partial { background-color: rgba(245, 158, 11, 0.1); color: var(--accent-yellow); }
.status-tag.full { background-color: rgba(16, 185, 129, 0.1); color: var(--accent-green); }
```

- [ ] **Step 7: 提交列表页修复**

```bash
git add web/src/components/workspace/SalesOrderList.vue
git commit -m "fix: 修复销售订单列表页状态字段引用

- 更新状态映射表使用与后端一致的枚举值
- 将 order.status 改为 order.order_status
- 移除不存在的付款状态列
- 更新表格列定义和 colspan

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: 验证修复

**Files:**
- 无文件修改，仅验证

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd web && npm run dev
```

- [ ] **Step 2: 验证列表页状态显示**

访问销售订单列表页，检查：
1. 订单状态列是否正确显示中文标签（草稿、待审核、已审核等）
2. 状态标签颜色是否正确
3. 操作按钮是否根据状态正确显示/隐藏

- [ ] **Step 3: 验证详情页状态显示**

点击订单详情，检查：
1. 订单状态是否正确显示
2. 发货状态是否正确显示
3. 收货状态是否正确显示
4. 开票状态是否正确显示
5. 状态下拉框是否可以正常切换

- [ ] **Step 4: 验证状态更新功能**

在详情页尝试更新状态：
1. 选择新的订单状态，确认更新成功
2. 选择新的发货状态，确认更新成功
3. 选择新的收货状态，确认更新成功
4. 选择新的开票状态，确认更新成功
