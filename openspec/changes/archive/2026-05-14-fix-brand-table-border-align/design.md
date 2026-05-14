## Context

品牌管理页面使用 vxe-table 组件展示品牌列表。描述列设置了 `show-overflow="tooltip"` 属性，vxe-table 自动为该列添加 `col--ellipsis` 类。全局样式 `.vxe-table .vxe-body--column.col--ellipsis { display: flex; }` 导致该列使用 flex 布局，与其他列的 `display: table-cell` 不一致，造成边框不对齐。

## Goals / Non-Goals

**Goals:**
- 修复描述列的垂直对齐问题，确保所有列的下边框对齐
- 保持表格整体布局一致性

**Non-Goals:**
- 不修改表格其他列的样式
- 不改变表格的功能行为（tooltip 功能可舍弃）

## Decisions

### 决策 1: 移除 `show-overflow="tooltip"` 属性

**选择**: 直接移除描述列的 `show-overflow="tooltip"` 属性

**理由**:
- `show-overflow="tooltip"` 会让 vxe-table 自动添加 `col--ellipsis` 类
- 全局样式对 `.col--ellipsis` 类有特殊的 flex 布局处理
- 移除属性后，描述列不再有 `col--ellipsis` 类，避免全局样式影响

**替代方案**（已尝试，无效）:
1. 移除 `class-name="col--middle"` - 问题不在这个类
2. 删除组件内的 `.vxe-body--column.col--ellipsis` 样式 - 全局样式在其他文件
3. CSS 覆盖 display 属性 - 方向错误，增加复杂度

## Risks / Trade-offs

**风险**: 移除 `show-overflow="tooltip"` 后，长描述会完整显示，可能撑开行高
**缓解**: 描述内容通常较短，影响有限；如需截断可后续用其他方案

## 修复过程教训

### 问题分析错误

初始分析认为是 `class-name="col--middle"` 导致问题，实际上问题根因是 `show-overflow="tooltip"` 自动添加的 `col--ellipsis` 类。

### 全局样式追踪困难

全局样式定义在 `CrmWorkspace.vue` 中，但影响了所有使用 vxe-table 的页面。这种跨组件的全局样式增加了问题排查难度。

### 正确的排查思路

1. 检查元素实际应用的类名（使用浏览器开发者工具）
2. 搜索类名在项目中的定义位置
3. 理解类名是如何被添加到元素上的（自动添加 vs 手动添加）
4. 从源头解决问题，而非用更多样式覆盖
