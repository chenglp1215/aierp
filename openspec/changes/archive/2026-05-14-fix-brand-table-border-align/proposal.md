## Why

品牌管理页面表格中"描述"列的下边框与其他列不对齐，整体高度不一致，影响表格的视觉一致性和用户体验。这是一个 CSS 样式问题，需要修复 vxe-table 列的垂直对齐问题。

## What Changes

- 修复品牌管理表格中"描述"列的垂直对齐问题
- 移除描述列的 `show-overflow="tooltip"` 属性，避免自动添加 `col--ellipsis` 类

## Capabilities

### New Capabilities
无

### Modified Capabilities
无（此为纯样式修复，不涉及需求变更）

## Impact

- **前端代码**: `web/src/components/workspace/BrandWorkspace.vue`
- **影响范围**: 仅影响品牌管理页面的表格展示样式
- **依赖**: 无

## 修复过程记录

### 问题根因

描述列设置了 `show-overflow="tooltip"` 属性，vxe-table 会自动为该列添加 `col--ellipsis` 类。全局样式 `.vxe-table .vxe-body--column.col--ellipsis { display: flex; }` 导致该列使用 flex 布局，与其他列的 `display: table-cell` 不一致，造成边框不对齐。

### 错误尝试

1. **错误尝试 1**: 移除 `class-name="col--middle"` - 无效，因为问题不在这个类
2. **错误尝试 2**: 删除组件内的 `.vxe-body--column.col--ellipsis { display: block !important; }` 样式 - 无效，因为全局样式在其他文件中
3. **错误尝试 3**: 尝试用 CSS 覆盖 `.col--ellipsis` 的 display 属性 - 方向错误

### 正确方案

**直接移除 `show-overflow="tooltip"` 属性**，这样 vxe-table 就不会为描述列添加 `col--ellipsis` 类，从而避免全局样式的影响。

### 教训

1. **vxe-table 的 `show-overflow` 属性会自动添加类名**：设置 `show-overflow="tooltip"` 时，vxe-table 会自动为该列添加 `col--ellipsis` 类
2. **全局样式影响范围难以追踪**：全局样式 `.vxe-table .vxe-body--column.col--ellipsis` 定义在 `CrmWorkspace.vue` 中，但影响了所有使用 vxe-table 的页面
3. **修复样式问题应从源头入手**：不要尝试用更多样式覆盖来修复，应找到导致问题的根本原因（自动添加的类名）并移除
