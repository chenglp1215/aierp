## Why

当前 customer 模块使用 MongoDB 实现，存在以下问题：
1. 数据一致性难以保证，嵌套文档（开票信息、收货地址）更新复杂
2. 与已迁移到 MySQL 的 product 模块数据关联不便（如 customer_discount 中的 brand_id）
3. 需要维护两套数据库连接，增加系统复杂度

product 模块已成功迁移到 MySQL（使用 Tortoise ORM），为 customer 模块迁移提供了成熟的参考实现。统一数据库架构可简化运维、提升数据一致性、便于跨模块关联查询。

## What Changes

- **数据库迁移**: 将 customer 相关数据从 MongoDB 迁移到 MySQL
- **模型重构**: 使用 Tortoise ORM 定义 Customer、InvoiceInfo、ShippingAddress、CustomerDiscount 四张独立表
- **服务层重写**: 参考 product_service_mysql.py 模式，重写 customer_service_mysql.py
- **路由层适配**: 修改 customer.py 路由，切换到 MySQL 服务层
- **接口兼容**: 保持现有 API 接口格式不变，确保前端无缝对接
- **文档更新**: 更新 customer.md API 文档（如有接口变动）

**BREAKING**: 后端数据存储从 MongoDB 切换到 MySQL，需要数据迁移脚本

## Capabilities

### New Capabilities

- `customer-mysql-models`: Customer、InvoiceInfo、ShippingAddress、CustomerDiscount 的 Tortoise ORM 模型定义
- `customer-mysql-service`: 基于 MySQL 的客户 CRUD 服务层，包括开票信息、收货地址、折扣管理

### Modified Capabilities

- `customer-api`: API 接口保持不变，但底层实现从 MongoDB 切换到 MySQL

## Impact

**后端影响**:
- `backend/models_mysql/customer.py` (新增)
- `backend/services/customer_service_mysql.py` (新增)
- `backend/app/routers/customer.py` (修改，切换服务层)
- `backend/validators/customer_validator.py` (保持不变)
- `backend/app/routers/api_docs/customer.md` (可能需要更新)

**前端影响**:
- `web/src/services/api.ts` 中的 customerApi 接口定义保持不变
- 前端组件无需修改

**数据迁移**:
- 需要编写脚本将 MongoDB 中的 customers、customer_discounts 数据迁移到 MySQL