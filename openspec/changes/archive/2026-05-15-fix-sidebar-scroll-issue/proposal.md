## Why

左侧菜单栏在菜单全部展开或部分展开超过屏幕高度后，无法通过鼠标滚轮滚动查看下方菜单项。这是因为侧边栏的 CSS 布局使用了 `min-height: 100vh` 和 `position: fixed`，导致滚动容器高度计算不正确，用户无法访问超出视口高度的菜单项。

## What Changes

- 修复 `.sidebar` 容器的滚动行为，确保菜单内容超出屏幕高度时可以正常滚动
- 调整 `.sidebar-nav` 的 `overflow-y: auto` 配合正确的高度约束
- 确保 `.sidebar` 使用 `height: 100vh` 而非 `min-height`，使子元素可以正确计算滚动区域

## Capabilities

### New Capabilities
无新增能力，此变更仅为 UI 交互修复。

### Modified Capabilities
无需求变更，仅 CSS 实现层面的修复。

## Impact

**受影响的文件：**
- `web/src/components/SidebarNav.vue` - 修改 CSS 样式

**影响范围：**
- 仅影响前端侧边栏组件的滚动行为
- 不影响任何 API 或业务逻辑
- 不影响移动端响应式布局