## Why

当前库存管理模块支持入库和出库操作，但缺少盘库（库存盘点）功能。实际业务中，仓库人员需要定期盘点库存，核对账面数量与实际数量，及时发现盘盈盘亏情况。缺少盘库功能导致：
1. 无法记录盘点结果和差异原因
2. 无法追溯历史盘点记录
3. 批量盘点时需要逐条手动操作，效率低下

## What Changes

### 新增功能
- **单个盘库**：在库存列表和详情中，对单条库存记录进行盘点，录入实际盘点数量，系统自动计算差异并更新库存
- **批量盘库**：选择仓库后上传 Excel 文件，系统解析后批量更新库存，支持自动创建不存在的库存记录
- **盘库记录管理**：记录每次盘库的详细信息（盘点前数量、盘点数量、差异），支持按库存/批次查询
- **盘库批次管理**：一次批量盘库生成一个批次号，便于追溯和统计
- **模板下载**：提供盘库 Excel 模板下载功能

### 数据模型
- 新增 `StockCheckBatch`（盘库批次）模型
- 新增 `StockCheckRecord`（盘库记录）模型

### API 接口
- `POST /api/stock-checks/single` - 单个盘库
- `POST /api/stock-checks/batch` - 批量盘库
- `GET /api/stock-checks/template` - 下载模板
- `GET /api/stock-checks/records` - 获取盘库记录列表
- `GET /api/stock-checks/batches` - 获取盘库批次列表
- `GET /api/stock-checks/batches/{id}` - 获取批次详情

### 前端改动
- 库存管理页面新增"批量盘库"按钮和弹窗
- 库存列表操作列新增"盘库"按钮
- 库存详情弹窗新增"盘库记录" Tab 和"盘库"操作按钮

## Capabilities

### New Capabilities
- `stock-check`: 库存盘点功能，包含单个盘库、批量盘库、盘库记录查询、模板下载

### Modified Capabilities
- `inventory`: 库存详情展示增加盘库记录 Tab

## Impact

### 后端
- 新增 `models_mysql/stock_check.py` - 盘库数据模型
- 新增 `services/stock_check_service.py` - 盘库业务逻辑
- 新增 `app/routers/stock_check.py` - API 路由
- 修改 `services/inventory_service_mysql.py` - 库存详情查询增加盘库记录

### 前端
- 修改 `components/workspace/InventoryWorkspace.vue` - 新增盘库相关 UI
- 修改 `services/api.ts` - 新增盘库 API 接口

### 数据库
- 新增 `stock_check_batches` 表
- 新增 `stock_check_records` 表

### 权限
- 复用现有 `stock.edit` 权限控制盘库操作
