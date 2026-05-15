## Why

客户管理和库存管理模块已成功迁移到 MySQL（使用 Tortoise ORM）。MongoDB 相关的历史代码和文件已不再使用，需要清理以避免代码冗余和维护混淆。清理这些遗留代码可以：
1. 减少代码库体积，提高可维护性
2. 消除潜在的依赖混淆问题
3. 确保所有模块统一使用 MySQL 实现

## What Changes

### 删除 MongoDB 模型文件
- **BREAKING** 删除 `backend/models/customer.py` - MongoDB 客户模型（已被 `models_mysql/customer.py` 替代）
- **BREAKING** 删除 `backend/models/inventory.py` - MongoDB 库存模型（已被 `models_mysql/warehouse.py` 替代）
- 删除 `backend/models/province_city.py` - 省市数据模型（已无实际使用，数据硬编码在 service 中）

### 删除 MongoDB 服务文件
- **BREAKING** 删除 `backend/services/customer_service.py` - MongoDB 客户服务（已被 `customer_service_mysql.py` 替代）
- **BREAKING** 删除 `backend/services/inventory_service.py` - MongoDB 库存服务（已被 `inventory_service_mysql.py` 替代）
- 删除 `backend/services/province_city_service.py` - 省市服务（数据已硬编码，无需独立服务）

### 更新依赖模块的导入
- 更新 `backend/app/routers/__init__.py` - 移除 `province_city_router` 导入
- 更新 `backend/models/__init__.py` - 移除 MongoDB 模型的导出
- 更新 `backend/app/agent/tools/customer.py` - 迁移到 MySQL 服务导入
- 更新 `backend/app/agent/tools/inventory.py` - 迁移到 MySQL 服务导入
- 更新 `backend/services/sales_order_service.py` - 已使用 MySQL 服务，无需修改

### 清理 MongoDB 基础设施（可选保留）
- `backend/services/base_service.py` - MongoDB 基础服务类，保留供其他模块使用（如销售订单）
- `backend/app/database.py` - MongoDB 连接配置，保留供其他模块使用

## Capabilities

### New Capabilities
无新增能力，此变更仅为代码清理。

### Modified Capabilities
无需求变更，仅实现层面的清理。

## Impact

### 受影响的文件
**删除文件（7个）：**
- `backend/models/customer.py`
- `backend/models/inventory.py`
- `backend/models/province_city.py`
- `backend/services/customer_service.py`
- `backend/services/inventory_service.py`
- `backend/services/province_city_service.py`
- `backend/app/routers/province_city.py`

**修改文件（5个）：**
- `backend/models/__init__.py` - 移除 MongoDB 模型导出
- `backend/app/routers/__init__.py` - 移除 province_city_router
- `backend/app/agent/tools/customer.py` - 更改导入源
- `backend/app/agent/tools/inventory.py` - 更改导入源
- `backend/app/routers/prompts/province_city.py` - 检查是否需要保留

### API 影响
- `/api/province-city` 路由将被移除（数据可硬编码在前端或使用其他方式提供）

### 数据库影响
- 无数据库结构变更，MySQL 表结构已存在并正常使用