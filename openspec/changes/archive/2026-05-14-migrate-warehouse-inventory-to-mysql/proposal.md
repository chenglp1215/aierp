## Why

当前仓库管理和库存管理模块仍使用 MongoDB 作为底层数据库，与已迁移到 MySQL 的客户管理、商品管理等模块存在技术栈不一致的问题。为了保持系统架构统一、简化运维、提升数据一致性保障，需要将仓库管理和库存管理模块迁移到 MySQL。

## What Changes

- **仓库管理模块（Warehouse）**: 从 MongoDB 迁移到 MySQL，使用 Tortoise ORM 实现
- **库存管理模块（Stock）**: 从 MongoDB 迁移到 MySQL，使用 Tortoise ORM 实现
- **入库批次模块（InboundBatch）**: 从 MongoDB 迁移到 MySQL
- **出库批次模块（OutboundBatch）**: 从 MongoDB 迁移到 MySQL
- **数据模型**: 创建 MySQL 版本的 Tortoise ORM 模型，替代现有的 Pydantic 模型
- **服务层**: 重写服务层代码，使用 Tortoise ORM 查询替代 MongoDB 操作
- **路由层**: 调整路由层代码，适配新的服务层接口
- **数据迁移**: 编写数据迁移脚本，将现有 MongoDB 数据迁移到 MySQL

## Capabilities

### New Capabilities

- `mysql-warehouse-module`: 仓库管理模块的 MySQL 实现，包括仓库 CRUD、状态管理、管理员分配等功能
- `mysql-inventory-module`: 库存管理模块的 MySQL 实现，包括库存查询、入库、出库、盘库等功能

### Modified Capabilities

无。本次迁移保持 API 接口不变，前端无需修改。

## Impact

### 后端影响

- `backend/models_mysql/warehouse.py`: 新增仓库、库存、入库批次、出库批次的 Tortoise ORM 模型
- `backend/services/inventory_service_mysql.py`: 新增 MySQL 版本的库存服务层
- `backend/app/routers/inventory.py`: 调整路由层，使用新的 MySQL 服务层
- `backend/models_mysql/__init__.py`: 注册新模型到 Tortoise ORM

### 前端影响

- 前端代码无需修改，API 接口保持完全兼容

### 数据库影响

- 新增 MySQL 表: `warehouses`, `stocks`, `inbound_batches`, `outbound_batches`
- 需要执行数据迁移脚本将 MongoDB 数据迁移到 MySQL

### 依赖关系

- 依赖已迁移的 `product` 模块（商品、规格信息）
- 依赖已迁移的 `auth` 模块（用户信息）
