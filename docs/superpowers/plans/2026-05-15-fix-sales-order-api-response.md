# 销售订单 API 返回值修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复销售订单下推采购功能和详情页面的 API 返回值处理问题

**Architecture:** 前端 API 服务层自动解包 `result` 字段，但部分组件错误地访问了 `response.result`，导致获取 `undefined`。修复方案是直接使用 API 返回值，移除 `.result` 访问。

**Tech Stack:** Vue 3, TypeScript, Composition API

---

## 文件结构

**修改文件：**
- `web/src/components/workspace/SalesOrderWorkspace.vue` - 销售订单列表页面，修复 `confirmPushPurchase` 函数
- `web/src/components/workspace/SalesOrderDetail.vue` - 销售订单详情页面，修复 `loadOrder` 和 `handlePushPurchase` 函数

---

### Task 1: 修复 SalesOrderWorkspace.vue 中的 confirmPushPurchase 函数

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue:1140-1142`

- [ ] **Step 1: 修复 API 返回值处理**

将第 1140-1142 行：
```typescript
    const orderRes = await salesOrderApi.getByOrderNo(orderNo)
    const fullOrder = orderRes.result
    const items = fullOrder.items || []
```

修改为：
```typescript
    const fullOrder = await salesOrderApi.getByOrderNo(orderNo)
    const items = fullOrder.items || []
```

- [ ] **Step 2: 验证修改**

检查文件中是否还有其他 `orderRes.result` 或 `prodRes.result` 的引用需要修复。

第 1151-1153 行的 `prodRes.result` 也需要修复：
```typescript
        if (prodRes.result) {
          brandMap[pid] = prodRes.result.brand_name || ''
          brandIdMap[pid] = prodRes.result.brand_id || ''
```

修改为：
```typescript
        if (prodRes) {
          brandMap[pid] = prodRes.brand_name || ''
          brandIdMap[pid] = prodRes.brand_id || ''
```

- [ ] **Step 3: 提交修改**

```bash
git add web/src/components/workspace/SalesOrderWorkspace.vue
git commit -m "fix: 修复 SalesOrderWorkspace 下推采购 API 返回值处理"
```

---

### Task 2: 修复 SalesOrderDetail.vue 中的 loadOrder 函数

**Files:**
- Modify: `web/src/components/workspace/SalesOrderDetail.vue:87-92`

- [ ] **Step 1: 修复 loadOrder 函数的 API 返回值处理**

将第 87-92 行：
```typescript
    const [orderRes, flowsRes] = await Promise.all([
      salesOrderApi.getByOrderNo(props.orderNo),
      salesOrderApi.getStatusFlows(props.orderNo)
    ])
    order.value = orderRes.result
    flows.value = flowsRes.result || []
```

修改为：
```typescript
    const [orderData, flowsData] = await Promise.all([
      salesOrderApi.getByOrderNo(props.orderNo),
      salesOrderApi.getStatusFlows(props.orderNo)
    ])
    order.value = orderData
    flows.value = flowsData || []
```

- [ ] **Step 2: 提交修改**

```bash
git add web/src/components/workspace/SalesOrderDetail.vue
git commit -m "fix: 修复 SalesOrderDetail loadOrder 函数 API 返回值处理"
```

---

### Task 3: 修复 SalesOrderDetail.vue 中的 handlePushPurchase 函数

**Files:**
- Modify: `web/src/components/workspace/SalesOrderDetail.vue:190-204`

- [ ] **Step 1: 修复 handlePushPurchase 函数的 API 返回值处理**

将第 190-204 行：
```typescript
    const orderRes = await salesOrderApi.getByOrderNo(order.value.order_no)
    const fullOrder = orderRes.result
    const items = fullOrder.items || []

    const productIds: string[] = [...new Set(items.map((item: any) => item.product_id).filter(Boolean) as string[])]
    const brandMap: Record<string, string> = {}
    const brandIdMap: Record<string, string> = {}
    for (const pid of productIds) {
      try {
        const prodRes = await productApi.getById(pid)
        if (prodRes.result) {
          brandMap[pid] = prodRes.result.brand_name || ''
          brandIdMap[pid] = prodRes.result.brand_id || ''
        }
      } catch {}
```

修改为：
```typescript
    const fullOrder = await salesOrderApi.getByOrderNo(order.value.order_no)
    const items = fullOrder.items || []

    const productIds: string[] = [...new Set(items.map((item: any) => item.product_id).filter(Boolean) as string[])]
    const brandMap: Record<string, string> = {}
    const brandIdMap: Record<string, string> = {}
    for (const pid of productIds) {
      try {
        const prodRes = await productApi.getById(pid)
        if (prodRes) {
          brandMap[pid] = prodRes.brand_name || ''
          brandIdMap[pid] = prodRes.brand_id || ''
        }
      } catch {}
```

- [ ] **Step 2: 提交修改**

```bash
git add web/src/components/workspace/SalesOrderDetail.vue
git commit -m "fix: 修复 SalesOrderDetail handlePushPurchase 函数 API 返回值处理"
```

---

### Task 4: 验证修复

**Files:**
- 无文件修改，仅功能验证

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd web && npm run dev
```

- [ ] **Step 2: 验证销售订单列表页面下推采购功能**

1. 打开销售订单列表页面
2. 找到一个状态为"已审核"的订单
3. 点击"下推采购"按钮
4. 确认弹窗正常显示商品列表，无 JavaScript 报错

- [ ] **Step 3: 验证销售订单详情页面**

1. 点击订单编号进入详情页面
2. 确认订单基本信息正常显示
3. 确认商品明细正常显示
4. 确认状态流转记录正常显示
5. 确认下推采购按钮功能正常

- [ ] **Step 4: 最终提交（如有遗漏）**

```bash
git status
# 如果有未提交的修改，一并提交
git add -A
git commit -m "fix: 完成销售订单 API 返回值处理修复"
```
