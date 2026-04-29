# 代码审查记录

## 2026-04-29 商品管理表格优化

### 需求背景
商品管理中，接口数据的每一条是商品数据，规格是商品中的一对多的属性。需要调整展示形式：
- 每一列是现在的属性列
- 当一个商品只有一个规格时，显示一行完整数据
- 当一个商品有多个规格时，商品4个属性列合并一行居中展示，规格列分行显示

### 涉及技术
Vue 3 + vxe-table

### 经验总结

#### 1. vxe-table 单元格合并

**需求**：表格按商品合并单元格（多规格商品）

**正确做法**：
- 使用 `span-method` 属性 + `:span-method="verticalSpanMethod"` 绑定合并方法
- 需要导入类型：`import type { VxeGridPropTypes } from 'vxe-table'`
- 合并逻辑：`productCols` 数组包含要合并的列索引，只在 `isFirst=true` 时返回 `rowspan`

```typescript
const verticalSpanMethod: VxeGridPropTypes.SpanMethod = ({ row, columnIndex }) => {
  const productCols = [0, 1, 2, 3, 4]
  if (productCols.includes(columnIndex) && row.isFirst) {
    return { rowspan: row.rowspan, colspan: 1 }
  }
  if (productCols.includes(columnIndex)) {
    return { rowspan: 0, colspan: 0 }
  }
}
```

#### 2. 序号按商品而非规格显示

**需求**：序号应该是商品的序号，不是每行的序号

**正确做法**：
- 使用 `seq-config="{ seqMethod: seqMethod }"` 绑定自定义序号方法
- 需要导入 `VxeGridPropTypes.SeqMethod` 类型
- 逻辑：只有 `isFirst=true` 的行显示序号，其他返回 0

```typescript
const seqMethod: VxeGridPropTypes.SeqMethod = ({ row }) => {
  if (!row.isFirst) return 0
  const firstRows = verticalTableData.value.filter(r => r.isFirst)
  return firstRows.findIndex(r => r._id === row._id) + 1 + (page.value - 1) * pageSize.value
}
```

#### 3. 去掉表格 hover 高亮效果

**问题**：移除了 `:row-config="{ isHover: true }"` 后仍有高亮

**原因**：hover 效果来自多层样式
1. 组件内的 `.table-row:hover` 样式
2. **全局样式** `global.css` 中的 `.vxe-table .vxe-table--body tr:hover` 和 `tr:hover > td`

**正确做法**：
- 不能只依赖移除配置属性
- 需要在组件 `<style>` 中用 `!important` 覆盖全局样式：

```css
.vxe-table .vxe-table--body tr:hover,
.vxe-table .vxe-table--body tr:hover > td {
  background-color: transparent !important;
}
```

### 关键教训

1. **定位样式来源**：修改 UI 效果时，用浏览器 DevTools 精准定位是哪个 CSS 规则生效
2. **多层样式优先级**：组件样式 → 全局样式 → 第三方库默认样式
3. **覆盖第三方库**：需要更具体的选择器 + `!important`

#### 4. vxe-table v4 loading 加载状态

**问题**：vxe-table v4 不支持 `:loading="true"` prop，报错 "不支持的参数"

**错误用法**：
```vue
<vxe-table :loading="loading">
```

**正确做法**：
1. 需要安装 `vxe-pc-ui` 包（包含 vxe-loading）：
```bash
npm install vxe-pc-ui
```

2. 在 main.ts 中导入并注册：
```typescript
// main.ts
import VXETable from 'vxe-table'
import VxeUIBase from 'vxe-pc-ui'
import 'vxe-table/lib/style.css'
import 'vxe-pc-ui/lib/style.css'

createApp(App).use(VXETable).use(VxeUIBase)
```

3. 在 vxe-table 中使用 `#loading` slot 并用 v-if 控制：
```vue
<vxe-table :data="tableData">
  <template #loading v-if="loading">
    <vxe-loading text="加载中..."></vxe-loading>
  </template>
</vxe-table>
```
