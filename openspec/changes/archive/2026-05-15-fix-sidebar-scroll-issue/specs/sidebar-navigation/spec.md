## MODIFIED Requirements

### Requirement: Sidebar scrollable when menu items exceed viewport height

侧边栏导航菜单在菜单项超出视口高度时，系统 SHALL 允许用户通过鼠标滚轮滚动查看所有菜单项。

#### Scenario: Menu expanded beyond viewport can scroll
- **WHEN** 用户展开多个菜单项导致总高度超过视口高度
- **THEN** 系统允许通过鼠标滚轮滚动查看超出视口的菜单项

#### Scenario: Scroll position maintained during navigation
- **WHEN** 用户滚动到特定菜单项并点击导航
- **THEN** 滚动位置保持不变，用户返回时仍在相同位置
