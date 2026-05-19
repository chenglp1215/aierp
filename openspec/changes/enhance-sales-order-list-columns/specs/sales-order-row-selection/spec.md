## ADDED Requirements

### Requirement: Row selection UI
系统 SHALL 在销售单列表提供行选中功能，支持单选和多选。

#### Scenario: Select single row
- **WHEN** 用户点击销售单行的复选框
- **THEN** 系统选中该行，高亮显示

#### Scenario: Select multiple rows
- **WHEN** 用户点击多个销售单行的复选框
- **THEN** 系统选中所有点击的行

#### Scenario: Select all rows
- **WHEN** 用户点击表头的全选复选框
- **THEN** 系统选中当前页所有行

#### Scenario: Deselect row
- **WHEN** 用户再次点击已选中行的复选框
- **THEN** 系统取消选中该行

### Requirement: Selection state management
系统 SHALL 维护选中行的状态。

#### Scenario: Track selected orders
- **WHEN** 用户选中销售单
- **THEN** 系统记录选中的 order_no 列表

#### Scenario: Clear selection
- **WHEN** 用户点击"取消选择"按钮
- **THEN** 系统清除所有选中状态

### Requirement: Batch operations on selected rows
系统 SHALL 支持对选中行执行批量操作。

#### Scenario: Batch submit for approval
- **WHEN** 用户选中多个草稿状态的订单
- **AND** 点击"批量提交审核"按钮
- **THEN** 系统批量提交选中的订单

#### Scenario: Batch operation validation
- **WHEN** 用户选中不同状态的订单
- **AND** 执行批量操作
- **THEN** 系统仅对符合条件的状态执行操作，返回跳过数量提示
