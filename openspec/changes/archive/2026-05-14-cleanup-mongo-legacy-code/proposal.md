## Why

项目已从 MongoDB 迁移到 MySQL，但 `auth` 和 `product` 模块仍保留了大量 MongoDB 版本的历史代码。这些代码：
- 增加代码库维护负担
- 可能造成混淆（同时存在 MongoDB 和 MySQL 两套服务）
- 占用不必要的存储空间

清理这些历史代码将简化代码库，降低维护成本。

## What Changes

### 可直接删除的文件

| 文件 | 说明 |
|------|------|
| `backend/models/auth.py` | MongoDB 版本的 Pydantic 模型（User, Role, Permission） |
| `backend/models/product.py` | MongoDB 版本的 Pydantic 模型（Brand, Category, Product, ProductSpec） |
| `backend/services/product_service.py` | MongoDB 版本的服务层（BrandService, CategoryService, ProductService, ProductSpecService） |

### 需要重构的文件

| 文件 | 当前状态 | 处理方式 |
|------|---------|---------|
| `backend/services/auth_service.py` | 包含 MongoDB 版服务（AuthService, RoleService, PermissionService）和 MySQL 版服务 | **删除 MongoDB 版服务类**，保留 MySQL 版服务类 |
| `backend/services/base_service.py` | MongoDB 基础服务类 | **保留**，其他模块（如 sales_order）仍在使用 |
| `backend/app/database.py` | 包含 MongoDB 连接管理 | **保留**，其他模块（如 sales_order）仍在使用 |
| `backend/app/middleware.py` | 使用 `auth_service.get_user_by_id` | **需修改**：改用 `mysql_user_service.get_by_id` |
| `backend/app/routers/ws.py` | 使用 `auth_service.get_user_by_id` | **需修改**：改用 `mysql_user_service.get_by_id` |
| `backend/app/agent/tools/product.py` | 使用 MongoDB 版 `product_service` | **需用户评估**：Agent 工具是否仍在使用？ |
| `backend/scripts/init_db.py` | 使用 MongoDB 版服务初始化数据 | **需用户评估**：是否需要迁移到 MySQL？ |
| `backend/scripts/shell.py` | 调试脚本引用 MongoDB 服务 | **需用户评估**：是否需要更新？ |

### 服务实例导出变更

`backend/services/__init__.py` 当前导出的 MongoDB 版服务实例将被移除：
- `auth_service` → 删除
- `role_service` → 删除
- `permission_service` → 删除
- `product_service` → 删除（已有 MySQL 版本）
- `category_service` → 删除（已有 MySQL 版本）
- `brand_service` → 删除（已有 MySQL 版本）

## Capabilities

### New Capabilities

无新增能力。

### Modified Capabilities

无需求变更，仅清理历史代码。

## Impact

### 直接影响

1. **代码删除**：约 1000+ 行 MongoDB 版本代码将被移除
2. **导入变更**：部分文件需要更新导入语句
3. **服务实例**：`services/__init__.py` 导出列表变更

### 依赖分析

| 模块 | 依赖状态 | 处理建议 |
|------|---------|---------|
| `backend/services/sales_order_service.py` | 依赖 `product_service`, `product_spec_service`, `brand_service` | **需迁移到 MySQL 版** |
| `backend/services/customer_service.py` | 依赖 `auth_service`, `brand_service` | **需迁移到 MySQL 版** |
| `backend/services/inventory_service.py` | 依赖 `product_service`, `product_spec_service` | **需迁移到 MySQL 版** |
| `backend/app/agent/tools/product.py` | 依赖 MongoDB 版 `product_service` | **需用户评估** |

### 风险评估

- **低风险**：删除 `models/auth.py` 和 `models/product.py`（仅被 MongoDB 服务引用）
- **中风险**：重构 `auth_service.py`（需确保 MySQL 版服务完整）
- **需评估**：`sales_order_service.py`、`customer_service.py`、`inventory_service.py` 的迁移策略
