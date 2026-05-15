## Context

客户管理和库存管理模块已成功迁移到 MySQL（使用 Tortoise ORM）。迁移后的代码位于：
- `models_mysql/customer.py` - MySQL 客户模型
- `models_mysql/warehouse.py` - MySQL 仓库/库存模型
- `services/customer_service_mysql.py` - MySQL 客户服务
- `services/inventory_service_mysql.py` - MySQL 库存服务

当前存在以下 MongoDB 遗留代码需要清理：
- `models/customer.py` - MongoDB 客户模型（Pydantic 模型，用于 MongoDB 文档验证）
- `models/inventory.py` - MongoDB 库存模型（Pydantic 模型）
- `models/province_city.py` - 省市数据模型（已无实际使用）
- `services/customer_service.py` - MongoDB 客户服务（继承自 BaseService）
- `services/inventory_service.py` - MongoDB 库存服务（继承自 BaseService）
- `services/province_city_service.py` - 省市服务（数据已硬编码）
- `app/routers/province_city.py` - 省市路由

**约束条件：**
- MongoDB 基础设施（`base_service.py`、`database.py`）需保留，因为销售订单模块仍在使用 MongoDB
- 清理过程不能影响正在运行的业务

## Goals / Non-Goals

**Goals:**
1. 删除所有 MongoDB 相关的客户/库存模型和服务文件
2. 更新所有依赖模块的导入，指向 MySQL 实现
3. 确保清理后代码库无冗余代码
4. 保持 API 接口兼容性（除省市接口外）

**Non-Goals:**
1. 不迁移销售订单模块到 MySQL（超出范围）
2. 不删除 MongoDB 基础设施代码（`base_service.py`、`database.py`）
3. 不修改前端代码

## Decisions

### 1. 省市接口处理方式

**决定：** 删除 `/api/province-city` 路由，数据硬编码在前端或通过其他方式提供。

**理由：**
- 省市数据是静态数据，变化频率极低
- 当前实现数据已硬编码在 `province_city_service.py` 中
- 前端可以直接内嵌省市数据，减少 API 调用

**替代方案：**
- 保留路由但简化实现（增加维护成本，无实际收益）

### 2. Agent Tools 导入更新

**决定：** 更新 `app/agent/tools/customer.py` 和 `app/agent/tools/inventory.py` 的导入。

**理由：**
- Agent Tools 是 AI 助手功能的一部分，需要使用最新的服务实现
- MySQL 服务提供相同的接口签名，可直接替换

**实现方式：**
```python
# 修改前
from services.customer_service import customer_service

# 修改后
from services.customer_service_mysql import customer_service
```

### 3. models/__init__.py 清理策略

**决定：** 移除 MongoDB 模型的导出，但保留其他仍在使用的模型。

**理由：**
- `models/__init__.py` 当前导出 `CustomerBase`、`Warehouse`、`Stock` 等类型
- 这些类型可能被其他模块引用，需要检查并清理

**检查结果：**
- `CustomerBase`、`CustomerType`、`CustomerStatus`、`CustomerDiscount` - 仅在 MongoDB 服务中使用，可删除
- `Warehouse`、`Stock`、`InboundBatch`、`OutboundBatch` - 仅在 MongoDB 服务中使用，可删除
- `SalesOrder` 相关类型 - 仍在使用，保留

### 4. 清理顺序

**决定：** 按依赖关系从底层到顶层清理。

**顺序：**
1. 更新依赖模块的导入（Agent Tools、models/__init__.py）
2. 删除 MongoDB 服务文件
3. 删除 MongoDB 模型文件
4. 删除省市路由和服务
5. 更新路由注册

## Risks / Trade-offs

### 风险 1：遗漏的依赖引用
**风险：** 可能存在其他文件引用了被删除的模块。
**缓解：** 使用 grep 全局搜索所有导入引用，确保无遗漏。

### 风险 2：运行时错误
**风险：** 清理后可能出现运行时导入错误。
**缓解：** 清理后运行测试套件验证，或启动服务进行接口测试。

### 风险 3：省市接口依赖
**风险：** 前端可能依赖 `/api/province-city` 接口。
**缓解：** 检查前端代码是否使用该接口，如有依赖则保留或提供替代方案。

## Migration Plan

### 阶段 1：准备工作
1. 确认所有依赖模块已迁移到 MySQL
2. 运行现有测试确保系统正常

### 阶段 2：执行清理
1. 更新 `models/__init__.py`
2. 更新 `app/agent/tools/customer.py`
3. 更新 `app/agent/tools/inventory.py`
4. 删除 `services/customer_service.py`
5. 删除 `services/inventory_service.py`
6. 删除 `services/province_city_service.py`
7. 删除 `models/customer.py`
8. 删除 `models/inventory.py`
9. 删除 `models/province_city.py`
10. 删除 `app/routers/province_city.py`
11. 更新 `app/routers/__init__.py`

### 阶段 3：验证
1. 启动后端服务
2. 测试客户管理相关接口
3. 测试库存管理相关接口
4. 测试 Agent 工具功能

### 回滚策略
如果清理后出现问题，可以通过 Git 回滚到清理前的版本：
```bash
git checkout HEAD~1 -- backend/
```

## Open Questions

1. **省市接口是否被前端使用？** 需要检查前端代码确认。
2. **是否有测试脚本依赖这些模块？** 需要检查 `backend/scripts/` 目录下的脚本。