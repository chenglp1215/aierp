## ADDED Requirements

### Requirement: Single stock check
系统 SHALL 支持对单个库存记录进行盘点操作，用户录入实际盘点数量，系统自动计算差异并更新库存。

#### Scenario: 成功执行单个盘库
- **WHEN** 用户在库存列表或详情中点击"盘库"按钮
- **AND** 用户录入盘点数量为 95（当前库存为 100）
- **AND** 用户点击确认
- **THEN** 系统创建盘库批次记录（check_type=single）
- **AND** 系统创建盘库记录（before_quantity=100, check_quantity=95, difference=-5）
- **AND** 系统更新库存数量为 95
- **AND** 返回盘库成功结果

#### Scenario: 盘点数量为零
- **WHEN** 用户录入盘点数量为 0
- **THEN** 系统更新库存数量为 0
- **AND** 创建盘库记录（difference = -原库存数量）

#### Scenario: 库存不存在
- **WHEN** 用户尝试对不存在的库存进行盘库
- **THEN** 返回错误"库存记录不存在"

### Requirement: Batch stock check
系统 SHALL 支持批量盘库功能，用户选择仓库并上传 Excel 文件，系统解析后批量更新库存。

#### Scenario: 成功执行批量盘库
- **WHEN** 用户选择仓库"深圳中心仓"
- **AND** 用户上传包含 50 条盘点记录的 Excel 文件
- **AND** 所有规格编码都存在且格式正确
- **THEN** 系统创建盘库批次记录（check_type=batch, batch_code=SC20260514001）
- **AND** 系统创建 50 条盘库记录
- **AND** 系统更新 50 条库存记录
- **AND** 返回成功结果（success_count=50, fail_count=0）

#### Scenario: 批量盘库部分失败
- **WHEN** 用户上传包含 50 条记录的 Excel
- **AND** 其中 2 条规格编码不存在
- **THEN** 系统创建盘库批次记录
- **AND** 系统成功处理 48 条记录
- **AND** 返回失败详情（fail_count=2, failed_items 包含行号和原因）

#### Scenario: Excel 中规格不存在于库存
- **WHEN** Excel 中的规格编码 SP-NEW 在指定仓库的库存中不存在
- **AND** 该规格在系统中存在
- **THEN** 系统自动创建库存记录
- **AND** 盘库记录标记 is_new_stock=true
- **AND** before_quantity=0, check_quantity=录入数量

#### Scenario: 未选择仓库
- **WHEN** 用户未选择仓库就上传 Excel
- **THEN** 返回错误"请选择仓库"

#### Scenario: 未上传文件
- **WHEN** 用户未上传文件就提交
- **THEN** 返回错误"请上传盘库文件"

### Requirement: Stock check template download
系统 SHALL 提供盘库 Excel 模板下载功能。

#### Scenario: 下载模板
- **WHEN** 用户点击"下载模板"按钮
- **THEN** 系统返回 Excel 文件
- **AND** 文件包含表头：规格编码、盘点数量、备注

### Requirement: Stock check records query
系统 SHALL 支持查询盘库记录列表。

#### Scenario: 按库存ID查询
- **WHEN** 用户请求 GET /api/stock-checks/records?stock_id=123
- **THEN** 返回该库存的所有盘库记录

#### Scenario: 按批次ID查询
- **WHEN** 用户请求 GET /api/stock-checks/records?batch_id=456
- **THEN** 返回该批次的所有盘库记录

#### Scenario: 分页查询
- **WHEN** 用户请求 GET /api/stock-checks/records?page=1&page_size=20
- **THEN** 返回分页结果（total, page, page_size, items）

### Requirement: Stock check batches query
系统 SHALL 支持查询盘库批次列表和详情。

#### Scenario: 查询批次列表
- **WHEN** 用户请求 GET /api/stock-checks/batches
- **THEN** 返回批次列表（包含批次号、仓库、类型、成功数、失败数、操作人、时间）

#### Scenario: 查询批次详情
- **WHEN** 用户请求 GET /api/stock-checks/batches/{batch_id}
- **THEN** 返回批次信息及关联的所有盘库记录

### Requirement: Stock check permission
盘库操作 SHALL 使用现有的 stock.edit 权限控制。

#### Scenario: 无权限用户
- **WHEN** 无 stock.edit 权限的用户尝试盘库操作
- **THEN** 返回 403 权限不足错误

#### Scenario: 有权限用户
- **WHEN** 有 stock.edit 权限的用户执行盘库操作
- **THEN** 操作正常执行
