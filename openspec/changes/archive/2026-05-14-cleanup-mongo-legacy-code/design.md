## Context

项目已完成从 MongoDB 到 MySQL 的迁移，`auth` 和 `product` 模块已有完整的 MySQL 版本实现：
- **MySQL 模型**：`backend/models_mysql/auth.py`、`backend/models_mysql/product.py`
- **MySQL 服务**：`backend/services/auth_service.py`（MySQL 版服务类）、`backend/services/product_service_mysql.py`

但历史 MongoDB 版本代码仍保留在代码库中，包括：
- Pydantic 模型（`backend/models/auth.py`、`backend/models/product.py`）
- MongoDB 服务层（`backend/services/product_service.py`）
- `auth_service.py` 中的 MongoDB 版服务类（AuthService、RoleService、PermissionService）

当前状态：
- API 路由已使用 MySQL 版服务
- 部分业务模块（sales_order、customer、inventory）仍依赖 MongoDB 版 product_service
- 中间件和 WebSocket 路由仍使用 MongoDB 版 auth_service

## Goals / Non-Goals

**Goals:**
1. 删除不再使用的 MongoDB 版 Pydantic 模型文件
2. 删除 MongoDB 版 product_service.py
3. 重构 auth_service.py，移除 MongoDB 版服务类
4. 迁移依赖 MongoDB 服务的模块到 MySQL 版本
5. 更新中间件和 WebSocket 路由使用 MySQL 版服务

**Non-Goals:**
1. 不修改 MongoDB 数据库连接（其他模块仍在使用）
2. 不修改 MongoDB 版 base_service.py（其他模块仍在使用）
3. 不迁移 Agent 工具（需用户评估是否仍在使用）
4. 不迁移 init_db.py 脚本（需用户评估）

## Decisions

### 决策 1：分阶段清理

**选择**：分阶段清理，先删除明确无依赖的文件，再处理有依赖的文件

**理由**：
- 降低风险，避免一次性删除导致系统崩溃
- 便于定位和修复问题

**替代方案**：
- 一次性删除所有 MongoDB 代码 → 风险过高，不推荐

### 决策 2：保留 base_service.py 和 database.py 中的 MongoDB 连接

**选择**：保留 MongoDB 基础设施代码

**理由**：
- `sales_order_service.py`、`customer_service.py`、`inventory_service.py` 仍使用 MongoDB
- 这些模块尚未迁移到 MySQL

**替代方案**：
- 同时迁移所有模块到 MySQL → 工作量过大，超出本次清理范围

### 决策 3：auth_service.py 重构策略

**选择**：删除 MongoDB 版服务类，仅保留 MySQL 版服务类

**理由**：
- API 路由已使用 MySQL 版服务（`mysql_user_service`、`mysql_role_service`、`mysql_permission_service`）
- MongoDB 版服务类不再被主要业务流程使用

**实现**：
```python
# 删除以下类
- AuthService
- RoleService
- PermissionService

# 删除以下实例
- auth_service
- role_service
- permission_service

# 保留以下类
- MySQLUserService
- MySQLRoleService
- MySQLPermissionService

# 保留以下实例
- mysql_user_service
- mysql_role_service
- mysql_permission_service
```

### 决策 4：依赖模块迁移策略

**选择**：将依赖模块迁移到 MySQL 版服务

**涉及文件**：
| 文件 | 当前依赖 | 迁移目标 |
|------|---------|---------|
| `middleware.py` | `auth_service.get_user_by_id` | `mysql_user_service.get_by_id` |
| `ws.py` | `auth_service.get_user_by_id` | `mysql_user_service.get_by_id` |
| `sales_order_service.py` | `product_service.*` | `product_service_mysql.*` |
| `customer_service.py` | `auth_service.*`, `brand_service.*` | `mysql_user_service.*`, `product_service_mysql.brand_service` |
| `inventory_service.py` | `product_service.*`, `product_spec_service.*` | `product_service_mysql.*` |

## Risks / Trade-offs

### 风险 1：遗漏的依赖

**风险**：可能存在未发现的 MongoDB 服务依赖

**缓解**：
- 使用 `grep` 全面搜索所有引用
- 删除后运行测试验证

### 风险 2：ID 类型不兼容

**风险**：MongoDB 使用字符串 ID，MySQL 使用整数 ID，迁移可能导致 ID 比较失败

**缓解**：
- 确保 MySQL 版服务返回的 ID 格式一致
- 检查所有 ID 比较逻辑

### 风险 3：数据格式差异

**风险**：MongoDB 和 MySQL 返回的数据格式可能存在细微差异

**缓解**：
- 对比两版服务的返回格式
- 必要时添加格式转换逻辑

## Migration Plan

### 阶段 1：删除无依赖文件

1. 删除 `backend/models/auth.py`
2. 删除 `backend/models/product.py`
3. 删除 `backend/services/product_service.py`
4. 更新 `backend/services/__init__.py`

### 阶段 2：重构 auth_service.py

1. 删除 MongoDB 版服务类（AuthService、RoleService、PermissionService）
2. 删除 MongoDB 版服务实例
3. 保留 MySQL 版服务类和实例

### 阶段 3：迁移依赖模块

1. 更新 `backend/app/middleware.py`
2. 更新 `backend/app/routers/ws.py`
3. 更新 `backend/services/sales_order_service.py`
4. 更新 `backend/services/customer_service.py`
5. 更新 `backend/services/inventory_service.py`

### 阶段 4：验证

1. 运行测试
2. 检查 API 响应格式
3. 验证业务流程

### 回滚策略

如遇问题，可通过 Git 回滚到清理前的提交。
