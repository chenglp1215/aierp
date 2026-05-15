# 销售订单详情显示问题修复 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复销售订单详情页面的显示问题，包括商品信息不完整、发货方式显示英文、直发时仓库信息未处理

**Architecture:** 后端修改 `SalesOrderItem.to_dict()` 返回中文发货方式；前端修改 `SalesOrderCreate.vue` 提交完整商品信息；前端修改 `SalesOrderDetail.vue` 和 `PushPurchaseItemSelectModal.vue` 正确展示仓库信息

**Tech Stack:** Python/FastAPI (后端), Vue 3 + TypeScript (前端)

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/models_mysql/sales_order.py` | 修改 `SalesOrderItem.to_dict()` 返回中文发货方式 |
| `web/src/components/workspace/SalesOrderCreate.vue` | 修改 `handleSaveOrder` 提交完整商品信息 |
| `web/src/components/workspace/SalesOrderDetail.vue` | 添加仓库列、处理直发显示、移除冗余查询 |
| `web/src/components/workspace/PushPurchaseItemSelectModal.vue` | 处理直发时仓库显示 |

---

### Task 1: 后端 - 发货方式中文映射

**Files:**
- Modify: `backend/models_mysql/sales_order.py:139-164`

- [ ] **Step 1: 修改 `SalesOrderItem.to_dict()` 方法**

在 `to_dict()` 方法中，将 `shipping_method` 返回中文值而非英文枚举值。

```python
def to_dict(self):
    # 发货方式中文映射
    shipping_method_map = {
        ShippingMethod.DIRECT: "直运",
        ShippingMethod.WAREHOUSE: "仓库发货",
    }
    shipping_method_value = self.shipping_method.value if self.shipping_method else None
    shipping_method_cn = shipping_method_map.get(self.shipping_method, shipping_method_value) if self.shipping_method else None

    return {
        "id": self.id,
        "sales_order_id": self.sales_order_id,
        "row_no": self.row_no,
        "product_id": self.product_id,
        "product_code": self.product_code,
        "product_name": self.product_name,
        "spec_id": self.spec_id,
        "spec_code": self.spec_code,
        "brand_id": self.brand_id,
        "brand_name": self.brand_name,
        "warehouse_id": self.warehouse_id,
        "warehouse_name": self.warehouse_name,
        "qty": self.qty,
        "price": float(self.price),
        "discount": float(self.discount),
        "discounted_price": float(self.discounted_price) if self.discounted_price else None,
        "amt": float(self.amt) if self.amt else None,
        "shipping_method": shipping_method_cn,
        "pushed": self.pushed,
        "out_qty": self.out_qty,
        "return_qty": self.return_qty,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
```

- [ ] **Step 2: 验证修改**

启动后端服务，调用销售订单详情 API，确认 `shipping_method` 返回中文值。

```bash
cd backend && venv/Scripts/python -c "
from models_mysql.sales_order import SalesOrderItem, ShippingMethod
item = SalesOrderItem()
item.shipping_method = ShippingMethod.DIRECT
print('Direct:', item.to_dict().get('shipping_method'))
item.shipping_method = ShippingMethod.WAREHOUSE
print('Warehouse:', item.to_dict().get('shipping_method'))
"
```

Expected: 输出 "直运" 和 "仓库发货"

- [ ] **Step 3: 提交**

```bash
git add backend/models_mysql/sales_order.py
git commit -m "fix: SalesOrderItem.to_dict() 返回中文发货方式"
```

---

### Task 2: 前端 - 新建订单提交完整商品信息

**Files:**
- Modify: `web/src/components/workspace/SalesOrderCreate.vue:593-613`

- [ ] **Step 1: 修改 `handleSaveOrder` 函数中的 items 映射**

找到 `handleSaveOrder` 函数中的 `items` 映射代码（约第 603-612 行），修改为提交完整商品信息：

```javascript
items: orderForm.value.items.map(item => ({
  row_no: item.row_no,
  product_id: item.product_id,
  product_code: item.product_code || item.product_id,
  product_name: item.product_name,
  spec_id: item.spec_id,
  spec_code: item.spec_code || item.spec_id,
  brand_id: item.brand_id,
  brand_name: item.brand_name,
  warehouse_id: item.warehouse_id || '',
  warehouse_name: item.warehouse_name,
  qty: item.qty,
  price: item.price,
  discount: item.discount,
  shipping_method: item.shipping_method
}))
```

- [ ] **Step 2: 验证修改**

启动前端开发服务器，新建销售订单，选择商品并提交，检查网络请求中是否包含完整的商品信息。

```bash
cd web && npm run dev
```

在浏览器开发者工具中查看 POST `/sales-orders/` 请求体，确认包含 `product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name` 字段。

- [ ] **Step 3: 提交**

```bash
git add web/src/components/workspace/SalesOrderCreate.vue
git commit -m "fix: 新建销售订单时提交完整的商品信息"
```

---

### Task 3: 前端 - 详情页添加仓库列

**Files:**
- Modify: `web/src/components/workspace/SalesOrderDetail.vue:451-492`

- [ ] **Step 1: 在商品明细表格中添加"仓库"列**

找到商品明细表格的 `<thead>` 部分（约第 451-466 行），在"规格"列后添加"仓库"列：

```html
<thead>
  <tr>
    <th>行号</th>
    <th>商品</th>
    <th>品牌</th>
    <th>规格</th>
    <th>仓库</th>
    <th class="col-num">数量</th>
    <th class="col-num">库存</th>
    <th>库存状态</th>
    <th class="col-num">单价</th>
    <th class="col-num">金额</th>
    <th>发货方式</th>
    <th>下推状态</th>
  </tr>
</thead>
```

- [ ] **Step 2: 在表格 `<tbody>` 中添加仓库列数据**

找到 `<tbody>` 部分（约第 467-490 行），在"规格"列后添加"仓库"列，直发时显示 "--"：

```html
<tbody>
  <tr v-for="item in order.items" :key="item.row_no" :class="{ 'row-pushed': item.pushed }">
    <td>{{ item.row_no }}</td>
    <td>{{ item.product_name || item.product_id }}</td>
    <td>{{ item.brand_name || '-' }}</td>
    <td>{{ item.spec_code || '-' }}</td>
    <td>{{ item.shipping_method === '直运' ? '--' : (item.warehouse_name || '-') }}</td>
    <td class="col-num">{{ item.qty }}</td>
    <td class="col-num">{{ item.stock_quantity ?? '-' }}</td>
    <td>
      <span v-if="item.stock_status" class="status-tag" :class="getStatusClass(stockStatusMap, item.stock_status)">
        {{ getStatusLabel(stockStatusMap, item.stock_status) }}
      </span>
      <span v-else class="text-muted">-</span>
    </td>
    <td class="col-num">{{ item.price?.toFixed(2) }}</td>
    <td class="col-num">{{ item.amt?.toFixed(2) }}</td>
    <td>{{ item.shipping_method }}</td>
    <td>
      <span v-if="item.shipping_method !== '直运' && (item.stock_quantity ?? 0) >= item.qty" class="status-tag stock-sufficient">库存发货，无需采购</span>
      <span v-else-if="item.pushed" class="status-tag pushed">已下推</span>
      <span v-else class="status-tag pending">待下推</span>
    </td>
  </tr>
</tbody>
```

- [ ] **Step 3: 提交**

```bash
git add web/src/components/workspace/SalesOrderDetail.vue
git commit -m "feat: 销售订单详情页添加仓库列，直发时显示--"
```

---

### Task 4: 前端 - 移除冗余的品牌信息查询

**Files:**
- Modify: `web/src/components/workspace/SalesOrderDetail.vue:186-233`

- [ ] **Step 1: 简化 `handlePushPurchase` 函数**

移除冗余的品牌信息查询逻辑，直接使用后端返回的数据。修改 `handlePushPurchase` 函数（约第 186-233 行）：

```typescript
const handlePushPurchase = async () => {
  if (!order.value) return
  actionLoading.value = true
  try {
    const fullOrder = await salesOrderApi.getByOrderNo(order.value.order_no)
    const items = fullOrder.items || []

    // 批量获取品牌的采购人信息
    const uniqueBrandIds = [...new Set(items.map((item: any) => item.brand_id).filter(Boolean))] as string[]
    const purchaserMap: Record<string, { purchaser_id: string; purchaser_name: string }> = {}

    if (uniqueBrandIds.length > 0) {
      try {
        const purchaserRes = await brandApi.batchGetPurchasers(uniqueBrandIds)
        Object.assign(purchaserMap, purchaserRes.result || {})
      } catch {}
    }

    const enrichedItems = items.map((item: any) => ({
      ...item,
      purchaser_name: item.brand_id && purchaserMap[item.brand_id]
        ? purchaserMap[item.brand_id].purchaser_name
        : ''
    }))

    pushableItems.value = enrichedItems
    showPushItemSelect.value = true
  } catch (error: any) {
    window.showToast(error.message || '加载商品数据失败', 'error')
  } finally {
    actionLoading.value = false
  }
}
```

- [ ] **Step 2: 移除未使用的导入**

检查是否需要移除 `productApi` 导入（如果不再使用）：

```typescript
// 移除 productApi 导入（如果不再需要）
import { salesOrderApi, purchaseOrderApi, receivableApi, brandApi } from '../../services/api'
```

- [ ] **Step 3: 提交**

```bash
git add web/src/components/workspace/SalesOrderDetail.vue
git commit -m "refactor: 移除下推采购中冗余的品牌信息查询"
```

---

### Task 5: 前端 - 下推采购弹窗处理直发仓库显示

**Files:**
- Modify: `web/src/components/workspace/PushPurchaseItemSelectModal.vue`

- [ ] **Step 1: 更新发货方式判断逻辑**

由于后端现在返回中文发货方式，需要更新判断逻辑。找到所有 `shipping_method === '直运'` 的判断（约第 41、58、91、109、186 行），确认使用中文值：

```typescript
// 确认所有判断使用中文值
if (item.shipping_method === '直运') {
  // 直运相关逻辑
}
```

- [ ] **Step 2: 添加仓库列显示逻辑**

如果弹窗表格中有仓库相关字段，确保直发时显示 "--"。检查模板中是否有仓库列，如有则添加条件显示：

```html
<td>{{ item.shipping_method === '直运' ? '--' : (item.warehouse_name || '-') }}</td>
```

- [ ] **Step 3: 提交**

```bash
git add web/src/components/workspace/PushPurchaseItemSelectModal.vue
git commit -m "fix: 下推采购弹窗直发时仓库显示--"
```

---

### Task 6: 集成验证

- [ ] **Step 1: 新建订单验证**

1. 启动后端和前端服务
2. 新建销售订单，选择商品（包含品牌信息）
3. 提交订单
4. 检查数据库 `sales_order_items` 表，确认 `product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name` 字段已正确存储

- [ ] **Step 2: 详情页验证**

1. 打开销售订单详情页
2. 确认发货方式显示为中文（"直运" 或 "仓库发货"）
3. 确认仓库列已添加
4. 确认直发明细的仓库列显示 "--"

- [ ] **Step 3: 下推采购验证**

1. 点击"下推采购"按钮
2. 确认弹窗中发货方式显示为中文
3. 确认直发明细的仓库信息显示 "--"
4. 确认品牌信息正确显示，无需额外查询

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "fix: 修复销售订单详情显示问题

- 后端 SalesOrderItem.to_dict() 返回中文发货方式
- 前端新建订单时提交完整商品信息
- 详情页添加仓库列，直发时显示--
- 移除下推采购中冗余的品牌信息查询
"
```
