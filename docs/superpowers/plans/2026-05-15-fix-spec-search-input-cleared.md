# 修复规格搜索输入被清空问题实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复销售订单商品搜索输入框在搜索后被清空的问题，正确保存和显示用户输入的搜索关键字。

**Architecture:** 添加 `productSearchKeywords` 变量保存每个订单行的搜索关键字，修改输入框绑定逻辑优先显示搜索关键字。

**Tech Stack:** Vue 3, TypeScript, Composition API

---

## 文件结构

**修改文件:**
- `web/src/components/workspace/SalesOrderWorkspace.vue` - 修改搜索关键字保存和显示逻辑

---

### Task 1: 添加搜索关键字变量

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue`

- [ ] **Step 1: 在变量定义区域添加 `productSearchKeywords` 变量**

在 `showProductDropdown` 变量附近添加：

```typescript
const showProductDropdown = ref<number | null>(null)
const productSearchKeywords = ref<Record<number, string>>({})
```

---

### Task 2: 修改 handleProductSearch 函数

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue:395-414`

- [ ] **Step 1: 修改 `handleProductSearch` 函数，接收索引参数并保存搜索关键字**

将函数修改为：

```typescript
// 商品搜索（服务端模糊匹配规格编号）
let productSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleProductSearch = (index: number, keyword: string) => {
  // 保存搜索关键字
  productSearchKeywords.value[index] = keyword

  if (productSearchTimer) clearTimeout(productSearchTimer)
  if (!keyword || keyword.length < 1) {
    productTree.value = []
    specSearchResults.value = []
    return
  }
  productSearchTimer = setTimeout(async () => {
    try {
      // 只搜索规格
      const specsRes = await productApi.searchSpecs(keyword, 20)
      specSearchResults.value = specsRes || []
      productTree.value = []
    } catch (e) {
      console.error('搜索商品失败:', e)
      productTree.value = []
      specSearchResults.value = []
    }
  }, 300)
}
```

---

### Task 3: 修改输入框绑定

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue:1617-1622`

- [ ] **Step 1: 修改输入框的 `:value` 绑定和 `@input` 事件**

将模板修改为：

```vue
<input
  type="text"
  :value="productSearchKeywords[index] ?? (item.product_name ? (item.brand_name ? '[' + item.brand_name + '] ' + item.product_name : item.product_name) : '')"
  @focus="showProductDropdown = index; productTree = []"
  @input="handleProductSearch(index, ($event.target as HTMLInputElement).value)"
  placeholder="输入规格编号搜索"
/>
```

---

### Task 4: 修改 selectSpecFromSearch 函数

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue:416-470`

- [ ] **Step 1: 在 `selectSpecFromSearch` 函数开头添加清空搜索关键字的逻辑**

在函数开头添加：

```typescript
// 从规格搜索结果中选择规格（直接匹配规格编号）
const selectSpecFromSearch = async (specResult: SpecSearchResult) => {
  const itemIndex = showProductDropdown.value ?? 0
  showProductDropdown.value = null
  specSearchResults.value = []
  productSearchKeywords.value[itemIndex] = ''

  // 获取商品详情以获取品牌信息用于折扣计算
  ...
```

---

### Task 5: 验证并提交

- [ ] **Step 1: 构建前端验证修改**

```bash
cd web && npm run build
```

- [ ] **Step 2: 测试搜索功能**

1. 打开销售订单新建页面
2. 在商品搜索框输入规格编号关键字
3. 确认输入框保持显示关键字
4. 确认下拉框显示搜索结果
5. 选择规格，确认输入框显示商品名称

- [ ] **Step 3: 提交修改**

```bash
git add web/src/components/workspace/SalesOrderWorkspace.vue
git commit -m "fix: 修复商品搜索输入被清空问题，添加搜索关键字保存逻辑"
```