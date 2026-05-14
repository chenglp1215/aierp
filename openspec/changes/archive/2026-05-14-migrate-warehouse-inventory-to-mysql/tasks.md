## 1. 数据模型开发

- [ ] 1.1 创建 `backend/models_mysql/warehouse.py`，定义 Warehouse 模型（id, warehouse_code, name, address, manager_id, manager_name, status, description, created_at, updated_at）
- [ ] 1.2 在 `backend/models_mysql/warehouse.py` 中定义 Stock 模型（id, warehouse_id, product_id, product_code, product_name, spec_id, spec_code, quantity, min_stock, max_stock, status, created_at, updated_at）
- [ ] 1.3 在 `backend/models_mysql/warehouse.py` 中定义 InboundBatch 模型（id, warehouse_id, product_id, product_code, product_name, spec_id, spec_code, stock_id, quantity, user_id, user_name, remarks, created_at, updated_at）
- [ ] 1.4 在 `backend/models_mysql/warehouse.py` 中定义 OutboundBatch 模型（id, warehouse_id, product_id, product_code, product_name, spec_id, spec_code, stock_id, quantity, user_id, user_name, remarks, created_at, updated_at）
- [ ] 1.5 在 `backend/models_mysql/__init__.py` 中注册新模型到 Tortoise ORM

## 2. 服务层开发

- [ ] 2.1 创建 `backend/services/inventory_service_mysql.py`，实现 WarehouseService 类（create_warehouse, update_warehouse, get_warehouse_by_id, get_warehouse_by_code, list_warehouses, get_warehouse_by_ids）
- [ ] 2.2 在 `inventory_service_mysql.py` 中实现 StockService 类（create_stock, update_stock, get_stock_by_id, list_stocks, get_or_create_stock_by_inbound, get_stock_status_by_spec_ids）
- [ ] 2.3 在 `inventory_service_mysql.py` 中实现 InboundBatchService 类（create_inbound, update_inbound, get_inbounds_by_stock_id, get_by_id）
- [ ] 2.4 在 `inventory_service_mysql.py` 中实现 OutboundBatchService 类（create_outbound, update_outbound, get_outbounds_by_stock_id, get_by_id）
- [ ] 2.5 实现库存状态自动计算逻辑（根据 quantity、min_stock、max_stock 计算 status）
- [ ] 2.6 实现入库操作时自动增加库存数量（使用数据库事务）
- [ ] 2.7 实现出库操作时自动减少库存数量（检查库存充足性，使用数据库事务）

## 3. 路由层适配

- [ ] 3.1 修改 `backend/app/routers/inventory.py`，导入新的 MySQL 服务层
- [ ] 3.2 在路由层添加 `to_int_id()` 函数，将字符串 ID 转换为整数 ID
- [ ] 3.3 修改 warehouse_router 所有路由方法，使用新的 WarehouseService
- [ ] 3.4 修改 stock_router 所有路由方法，使用新的 StockService
- [ ] 3.5 修改 inbound_router 所有路由方法，使用新的 InboundBatchService
- [ ] 3.6 修改 outbound_router 所有路由方法，使用新的 OutboundBatchService
- [ ] 3.7 确保 API 响应格式与 MongoDB 版本一致（包含 product_info、spec_info、warehouse_info）

## 4. 数据迁移脚本

- [ ] 4.1 创建 `backend/scripts/migrate_inventory_to_mysql.py` 数据迁移脚本
- [ ] 4.2 实现仓库数据迁移逻辑（从 MongoDB inventory_warehouses 迁移到 MySQL warehouses）
- [ ] 4.3 实现库存数据迁移逻辑（从 MongoDB inventory_stocks 迁移到 MySQL stocks，建立 ID 映射）
- [ ] 4.4 实现入库批次数据迁移逻辑（从 MongoDB inventory_inbound_batches 迁移到 MySQL inbound_batches）
- [ ] 4.5 实现出库批次数据迁移逻辑（从 MongoDB inventory_outbound_batches 迁移到 MySQL outbound_batches）
- [ ] 4.6 添加数据验证逻辑（验证迁移后的数据完整性）
- [ ] 4.7 添加迁移日志输出（记录迁移进度和结果）

## 5. 测试验证

- [ ] 5.1 启动后端服务，验证数据库表自动创建
- [ ] 5.2 测试仓库管理 API（创建、查询、更新、列表）
- [ ] 5.3 测试库存管理 API（查询、更新、详情）
- [ ] 5.4 测试入库操作（创建入库批次、库存数量增加）
- [ ] 5.5 测试出库操作（创建出库批次、库存数量减少、库存不足拒绝）
- [ ] 5.6 测试前端仓库管理页面功能
- [ ] 5.7 测试前端库存管理页面功能
- [ ] 5.8 执行数据迁移脚本，验证迁移结果

## 6. 文档更新

- [ ] 6.1 更新 `.project_docs/backend/项目模块说明.md`，添加库存管理模块 MySQL 实现说明
- [ ] 6.2 更新 API 接口文档（如有）
- [ ] 6.3 归档旧的 MongoDB 服务层代码（保留备份）