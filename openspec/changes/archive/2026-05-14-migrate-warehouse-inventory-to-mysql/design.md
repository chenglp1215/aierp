## Context

当前仓库管理和库存管理模块使用 MongoDB (Motor) 作为底层数据库，数据存储在以下集合中：
- `inventory_warehouses`: 仓库信息
- `inventory_stocks`: 库存记录
- `inventory_inbound_batches`: 入库批次
- `inventory_outbound_batches`: 出库批次

现有实现使用 Pydantic 模型进行数据验证，通过 BaseService 类封装 MongoDB 操作。客户管理、商品管理等模块已完成 MySQL 迁移，使用 Tortoise ORM 作为 ORM 框架。

本次迁移需要：
1. 保持 API 接口完全兼容，前端无需修改
2. 使用整数 ID 替代 MongoDB 的字符串 ObjectId
3. 保持与已迁移模块（product、auth）的关联关系

## Goals / Non-Goals

**Goals:**
- 将仓库、库存、入库批次、出库批次四个模块迁移到 MySQL
- 使用 Tortoise ORM 实现数据模型和服务层
- 保持 API 接口签名和响应格式不变
- 实现数据迁移脚本，将 MongoDB 数据迁移到 MySQL
- 保持与商品模块、用户模块的关联关系正确映射

**Non-Goals:**
- 不修改前端代码
- 不新增业务功能
- 不修改 API 接口签名
- 不重构现有业务逻辑

## Decisions

### 1. 数据模型设计

**决策**: 使用 Tortoise ORM 创建四个数据模型，采用整数自增主键

**理由**:
- 与已迁移的 customer、product 模块保持一致
- 整数 ID 在查询和关联时性能更好
- Tortoise ORM 提供良好的异步支持和类型提示

**表结构设计**:

| 表名 | 字段 | 说明 |
|------|------|------|
| `warehouses` | id, warehouse_code, name, address, manager_id, manager_name, status, description, created_at, updated_at | 仓库信息 |
| `stocks` | id, warehouse_id, product_id, product_code, product_name, spec_id, spec_code, quantity, min_stock, max_stock, status, created_at, updated_at | 库存记录 |
| `inbound_batches` | id, warehouse_id, product_id, product_code, product_name, spec_id, spec_code, stock_id, quantity, user_id, user_name, remarks, created_at, updated_at | 入库批次 |
| `outbound_batches` | id, warehouse_id, product_id, product_code, product_name, spec_id, spec_code, stock_id, quantity, user_id, user_name, remarks, created_at, updated_at | 出库批次 |

**关联关系**:
- `stocks.warehouse_id` → `warehouses.id`
- `stocks.product_id` → `products.id`
- `stocks.spec_id` → `product_specs.id`
- `inbound_batches.stock_id` → `stocks.id`
- `outbound_batches.stock_id` → `stocks.id`

### 2. ID 映射策略

**决策**: 在数据迁移时建立 MongoDB ObjectId 到 MySQL 整数 ID 的映射表

**理由**:
- 前端可能缓存了旧的字符串 ID，需要平滑过渡
- API 层面保持字符串 ID 输入（通过转换函数转为整数）
- 迁移脚本记录映射关系，便于数据验证和回滚

**实现方案**:
```python
def to_int_id(id_str: str) -> int:
    """将字符串 ID 转换为整数 ID"""
    try:
        return int(id_str)
    except (ValueError, TypeError):
        raise ValueError("无效的ID格式")
```

### 3. 服务层重构

**决策**: 创建新的 `inventory_service_mysql.py`，保持原有服务类结构

**理由**:
- 参考已迁移的 `customer_service_mysql.py` 和 `product_service_mysql.py` 的实现模式
- 保持服务层方法签名不变，便于路由层无缝切换
- 使用 Tortoise ORM 的异步查询方法替代 MongoDB 操作

**关键改动点**:
- `WarehouseService`: 使用 `Warehouse.filter()` 替代 `find_many()`
- `StockService`: 使用 `Stock.get_or_none()` 替代 `get_by_id()`
- `InboundBatchService`: 使用 `InboundBatch.create()` 替代 MongoDB insert
- `OutboundBatchService`: 使用 `OutboundBatch.create()` 替代 MongoDB insert

### 4. 数据迁移方案

**决策**: 编写独立的数据迁移脚本，按顺序迁移数据

**迁移顺序**:
1. 迁移 `warehouses` 表（无外键依赖）
2. 迁移 `stocks` 表（依赖 warehouses、products、product_specs）
3. 迁移 `inbound_batches` 表（依赖 stocks）
4. 迁移 `outbound_batches` 表（依赖 stocks）

**ID 映射处理**:
- 迁移时生成新的整数 ID
- 建立 ObjectId → 整数 ID 的映射字典
- 更新关联字段时使用映射字典转换

### 5. 路由层适配

**决策**: 修改路由层导入，使用新的 MySQL 服务层

**改动点**:
```python
# 旧代码
from services.inventory_service import warehouse_service, stock_service

# 新代码
from services.inventory_service_mysql import warehouse_service, stock_service
```

**ID 转换**:
- 在路由层添加 `to_int_id()` 函数，将前端传入的字符串 ID 转为整数

## Risks / Trade-offs

### Risk 1: 数据迁移过程中服务中断
**Mitigation**: 在低峰期执行迁移，迁移前备份 MongoDB 数据，准备回滚脚本

### Risk 2: ID 格式变化导致前端兼容问题
**Mitigation**: API 层面保持字符串 ID 输入输出，内部转换为整数；前端 API 调用无需修改

### Risk 3: 关联数据不一致
**Mitigation**: 迁移脚本验证关联关系，确保 product_id、spec_id、warehouse_id 在目标表中存在

### Risk 4: 并发入库/出库操作的数据一致性
**Mitigation**: 使用数据库事务确保库存更新和批次记录的原子性

## Migration Plan

### Phase 1: 模型和服务层开发
1. 创建 `models_mysql/warehouse.py` 定义数据模型
2. 创建 `services/inventory_service_mysql.py` 实现服务层
3. 在 `models_mysql/__init__.py` 注册新模型
4. 编写单元测试验证服务层功能

### Phase 2: 路由层切换
1. 修改 `app/routers/inventory.py` 使用新服务层
2. 添加 ID 转换函数
3. 验证 API 接口响应格式不变

### Phase 3: 数据迁移
1. 编写数据迁移脚本 `scripts/migrate_inventory_to_mysql.py`
2. 在测试环境执行迁移并验证数据完整性
3. 在生产环境执行迁移

### Phase 4: 清理
1. 删除旧的 MongoDB 服务层代码
2. 删除 MongoDB 集合（备份后）
3. 更新项目文档

### Rollback Strategy
- 保留 MongoDB 集合数据作为备份
- 路由层可通过修改导入快速回退到 MongoDB 服务层
- MySQL 表可通过 DROP TABLE 清理

## Open Questions

- 是否需要保留 MongoDB 集合作为历史数据备份？
- 迁移期间是否需要暂停入库/出库操作？