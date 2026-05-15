## Context

左侧菜单栏（Sidebar）是系统的主要导航组件，使用 `position: fixed` 固定定位。当前 CSS 使用 `min-height: 100vh` 设置最小高度，这导致子元素的 `overflow-y: auto` 无法正确计算滚动区域高度。

**当前状态：**
- `.sidebar` 使用 `min-height: 100vh` 和 `position: fixed`
- `.sidebar-nav` 使用 `flex: 1` 和 `overflow-y: auto`
- 问题：`min-height` 不会约束子元素的高度计算，导致滚动失效

**约束：**
- 保持固定定位布局不变
- 不影响响应式设计
- 不影响其他页面组件

## Goals / Non-Goals

**Goals:**
- 修复侧边栏滚动问题，确保菜单超出屏幕高度时可以正常滚动
- 保持现有布局结构和视觉样式

**Non-Goals:**
- 不修改响应式断点逻辑
- 不改变菜单展开/折叠的交互逻辑
- 不涉及移动端适配修改

## Decisions

### 决策 1：使用 `height: 100vh` 替代 `min-height: 100vh`

**理由：**
- `min-height` 只是设置最小高度，不会创建一个固定的高度约束
- 子元素 `flex: 1` 需要父元素有明确的高度才能正确计算剩余空间
- `height: 100vh` 创建固定高度，配合 `overflow-y: auto` 实现滚动

**替代方案：**
- 使用 `max-height: 100vh` + `overflow-y: auto` 在 `.sidebar` 上：会改变整体滚动行为，影响 header 和 footer
- 使用 JavaScript 动态计算高度：增加复杂度，不必要

## Risks / Trade-offs

**风险 1：内容超出视口时被截断**
- 缓解：这正是我们想要的行为，通过滚动查看被截断的内容

**风险 2：不同浏览器对 vh 单位的处理差异**
- 缓解：现代浏览器对 vh 单位支持良好，移动端 Safari 的地址栏问题不影响桌面端使用
