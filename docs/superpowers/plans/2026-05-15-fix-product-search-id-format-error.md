# 修复商品搜索 ID 格式错误实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复销售订单商品搜索功能的 "无效的ID格式" 错误，简化为只搜索规格编码。

**Architecture:** 移除前端对 `productApi.search` 的调用，只保留 `productApi.searchSpecs`，直接使用规格搜索结果展示列表。

**Tech Stack:** Vue 3, TypeScript, Composition API

---

## 文件结构

**修改文件:**
- `web/src/components/workspace/SalesOrderWorkspace.vue` - 修改 `handleProductSearch` 函数和模板展示

---

### Task 1: 修改商品搜索函数

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue:395-436`

- [ ] **Step 1: 修改 `handleProductSearch` 函数，移除对 `productApi.search` 的调用**

将 `handleProductSearch` 函数修改为只调用 `productApi.searchSpecs`，移除商品树构建逻辑：

```typescript
// 商品搜索（服务端模糊匹配规格编号）
let productSearchTimer: ReturnType<typeof setTimeout> | null = null
const handleProductSearch = (keyword: string) => {
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

- [ ] **Step 2: 验证修改**

检查修改后的代码：
1. 确认移除了 `productApi.search` 调用
2. 确认移除了 `Promise.all` 并行调用
3. 确认移除了商品树构建循环
4. 确认 `specSearchResults` 直接使用搜索结果

---

### Task 2: 简化模板展示

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue:1697-1748`

- [ ] **Step 1: 简化搜索下拉模板，移除商品树展示**

将搜索下拉模板简化为只展示规格列表，移除商品树相关代码：

```vue
<div class="search-dropdown product-tree-dropdown" v-if="showProductDropdown === index">
  <!-- 规格搜索结果 -->
  <template v-if="specSearchResults.length > 0">
    <div
      v-for="specResult in specSearchResults"
      :key="specResult.id"
      class="search-option spec-search-item"
      :class="{ 'inactive': !specResult.is_active }"
      @click="selectSpecFromSearch(specResult)"
    >
      <span class="spec-code">{{ specResult.spec_code }}</span>
      <span class="spec-info" v-if="specResult.packaging || specResult.sales_spec">{{ [specResult.packaging, specResult.sales_spec].filter(Boolean).join(' - ') }}</span>
      <span class="brand-name" v-if="specResult.brand_name">[{{ specResult.brand_name }}]</span>
      <span class="product-name-small">{{ specResult.product_name }}</span>
      <span class="spec-price">¥{{ specResult.price.toFixed(2) }}</span>
      <span class="spec-status" v-if="!specResult.is_active">停用</span>
    </div>
  </template>
  <div v-if="specSearchResults.length === 0" class="search-option disabled">
    输入关键字搜索规格编号
  </div>
</div>
```

- [ ] **Step 2: 更新搜索框占位符文本**

将搜索框的 placeholder 从 "输入商品名称/编码/规格编号搜索" 改为 "输入规格编号搜索"：

```vue
<input
  type="text"
  :value="item.product_name ? (item.brand_name ? '[' + item.brand_name + '] ' + item.product_name : item.product_name) : ''"
  @focus="showProductDropdown = index; productTree = []"
  @input="handleProductSearch(($event.target as HTMLInputElement).value)"
  placeholder="输入规格编号搜索"
/>
```

---

### Task 3: 清理未使用代码

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue`

- [ ] **Step 1: 移除未使用的 `toggleProductExpand` 函数**

删除 `toggleProductExpand` 函数（约第 438-442 行）：

```typescript
// 删除以下代码
// 展开/收起商品规格
const toggleProductExpand = async (index: number) => {
  const item = productTree.value[index]
  item.expanded = !item.expanded
}
```

- [ ] **Step 2: 移除未使用的 `selectSpec` 函数**

删除 `selectSpec` 函数（约第 444-487 行），因为现在只使用 `selectSpecFromSearch`。

- [ ] **Step 3: 保留必要的变量和接口**

确认保留：
- `productTree` 变量（虽然不再使用，但避免模板报错）
- `specSearchResults` 变量
- `SpecSearchResult` 接口
- `selectSpecFromSearch` 函数

---

### Task 4: 验证

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd web && npm run dev
```

- [ ] **Step 2: 测试搜索功能**

1. 打开销售订单新建页面
2. 在商品搜索框输入规格编号关键字
3. 确认能正常返回规格列表
4. 确认不再出现 "无效的ID格式" 错误
5. 选择规格，确认能正确填充到订单行

- [ ] **Step 3: 提交修改**

```bash
git add web/src/components/workspace/SalesOrderWorkspace.vue
git commit -m "fix: 修复商品搜索ID格式错误，简化为只搜索规格编码"
```