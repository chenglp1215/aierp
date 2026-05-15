## ADDED Requirements

### Requirement: Stock detail shows check records
库存详情弹窗 SHALL 展示盘库记录，与入库记录、出库记录并列。

#### Scenario: 查看库存详情
- **WHEN** 用户点击库存列表中的"详情"按钮
- **THEN** 弹窗显示三个 Tab：入库记录、出库记录、盘库记录
- **AND** 盘库记录 Tab 显示该库存的所有盘库历史

#### Scenario: 盘库记录列表展示
- **WHEN** 用户切换到"盘库记录" Tab
- **THEN** 显示盘库记录列表
- **AND** 每条记录显示：操作人、盘点前数量、盘点数量、差异、时间
- **AND** 差异为正数显示绿色（盘盈），为负数显示红色（盘亏）

### Requirement: Stock detail has check button
库存详情弹窗 SHALL 提供"盘库"操作按钮。

#### Scenario: 从详情弹窗执行盘库
- **WHEN** 用户在库存详情弹窗中点击"盘库"按钮
- **THEN** 弹出盘库表单
- **AND** 表单显示当前库存信息（商品、规格、仓库、当前数量）
- **AND** 用户可录入盘点数量
