## MODIFIED Requirements

### Requirement: 品牌管理列表展示
品牌管理页面 SHALL 使用 vxe-table 表格组件展示品牌列表数据，替代原有的卡片网格布局。

#### Scenario: 表格列展示
- **WHEN** 用户访问品牌管理页面
- **THEN** 系统 SHALL 展示包含以下列的表格：Logo、品牌名称、描述、采购人员、状态、商品数量、更新时间、操作

#### Scenario: Logo 列展示
- **WHEN** 品牌有 Logo 图片
- **THEN** 系统 SHALL 在 Logo 列展示图片缩略图（固定尺寸）
- **WHEN** 品牌无 Logo 图片
- **THEN** 系统 SHALL 展示品牌名称首字母作为占位符

#### Scenario: 描述列展示
- **WHEN** 品牌描述内容较长
- **THEN** 系统 SHALL 完整展示描述内容，超长部分自动截断并支持 tooltip 查看完整内容

#### Scenario: 状态列展示
- **WHEN** 品牌状态为启用
- **THEN** 系统 SHALL 展示"启用"标签（绿色样式）
- **WHEN** 品牌状态为停用
- **THEN** 系统 SHALL 展示"停用"标签（红色样式）

#### Scenario: 操作列展示
- **WHEN** 用户查看品牌列表
- **THEN** 系统 SHALL 在操作列提供：编辑按钮、启用/停用切换按钮、删除按钮

### Requirement: 品牌筛选和搜索
品牌管理页面 SHALL 提供筛选和搜索功能，与商品管理保持一致的交互风格。

#### Scenario: 关键词搜索
- **WHEN** 用户在搜索框输入关键词并点击搜索
- **THEN** 系统 SHALL 根据品牌名称进行模糊匹配，刷新表格展示匹配结果

#### Scenario: 状态筛选
- **WHEN** 用户选择状态筛选条件（全部/启用/停用）
- **THEN** 系统 SHALL 根据筛选条件刷新表格展示对应品牌

#### Scenario: 重置筛选
- **WHEN** 用户点击重置按钮
- **THEN** 系统 SHALL 清空所有筛选条件，展示全部品牌列表

### Requirement: 品牌分页
品牌管理页面 SHALL 使用 vxe-pager 组件提供分页功能。

#### Scenario: 分页展示
- **WHEN** 品牌总数超过当前页大小
- **THEN** 系统 SHALL 展示分页器，支持翻页、跳页、调整每页数量

#### Scenario: 翻页操作
- **WHEN** 用户点击分页器的翻页按钮或调整每页数量
- **THEN** 系统 SHALL 刷新表格展示对应页的品牌数据