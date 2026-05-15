## 1. 后端数据模型

- [ ] 1.1 创建 `backend/models_mysql/stock_check.py`，定义 StockCheckBatch 和 StockCheckRecord 模型
- [ ] 1.2 在 `backend/models_mysql/__init__.py` 中注册新模型
- [ ] 1.3 运行数据库迁移，创建 stock_check_batches 和 stock_check_records 表

## 2. 后端服务层

- [ ] 2.1 创建 `backend/services/stock_check_service.py`，实现 StockCheckService 类
- [ ] 2.2 实现单个盘库方法 `create_single_check`
- [ ] 2.3 实现批量盘库方法 `create_batch_check`（含 Excel 解析）
- [ ] 2.4 实现模板下载方法 `generate_template`
- [ ] 2.5 实现盘库记录查询方法 `get_records_by_stock_id`、`get_records_by_batch_id`
- [ ] 2.6 实现批次查询方法 `list_batches`、`get_batch_detail`

## 3. 后端 API 路由

- [ ] 3.1 创建 `backend/app/routers/stock_check.py`，定义 stock_check_router
- [ ] 3.2 实现 POST /api/stock-checks/single 接口
- [ ] 3.3 实现 POST /api/stock-checks/batch 接口（multipart 文件上传）
- [ ] 3.4 实现 GET /api/stock-checks/template 接口
- [ ] 3.5 实现 GET /api/stock-checks/records 接口
- [ ] 3.6 实现 GET /api/stock-checks/batches 接口
- [ ] 3.7 实现 GET /api/stock-checks/batches/{id} 接口
- [ ] 3.8 在 `backend/app/main.py` 中注册 stock_check_router

## 4. 前端 API 服务

- [ ] 4.1 在 `web/src/services/api.ts` 中添加 stockCheckApi 接口定义
- [ ] 4.2 实现单个盘库 API 调用方法
- [ ] 4.3 实现批量盘库 API 调用方法（文件上传）
- [ ] 4.4 实现模板下载方法
- [ ] 4.5 实现盘库记录查询方法
- [ ] 4.6 实现批次查询方法

## 5. 前端 UI 组件

- [ ] 5.1 在 InventoryWorkspace.vue 中添加"批量盘库"按钮
- [ ] 5.2 创建批量盘库弹窗组件（选择仓库 + 上传文件 + 下载模板）
- [ ] 5.3 创建盘库结果弹窗组件（显示成功/失败数量和详情）
- [ ] 5.4 在库存列表操作列添加"盘库"按钮
- [ ] 5.5 创建单个盘库弹窗组件（显示当前库存 + 录入盘点数量 + 实时计算差异）
- [ ] 5.6 在库存详情弹窗中添加"盘库记录" Tab
- [ ] 5.7 在库存详情弹窗中添加"盘库"操作按钮

## 6. 测试验证

- [ ] 6.1 编写后端单元测试（test_stock_check_api.py）
- [ ] 6.2 测试单个盘库功能
- [ ] 6.3 测试批量盘库功能
- [ ] 6.4 测试 Excel 模板下载
- [ ] 6.5 测试盘库记录查询
- [ ] 6.6 测试前端 UI 交互
