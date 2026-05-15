## Why

项目已完成从 MongoDB 到 MySQL 的迁移，但数据模型设计中仍保留了大量的冗余字段（如 `brand_name`、`warehouse_name`、`product_name`、`customer_name` 等）。这些冗余字段是 MongoDB 时代无法做外键关联时的妥协方案，现在使用 MySQL + Tortoise ORM 后，应该通过表关联查询获取这些信息，而不是冗余存储。

**问题影响：**
1. 数据不一致风险：冗余字段可能与源数据不同步
2. 存储空间浪费：重复存储大量字符串数据
3. 维护成本高：更新名称时需要同步多处
4. API 设计混乱：前端需要传入冗余字段

## What Changes

### 识别到的冗余字段

**1. SalesOrder 主表**
- `customer_name` → 可通过 `customer_id` 关联查询
- `sale_user_name` → 可通过 `sale_user_id` 关联查询
- `creator_name` → 可通过 `creator_id` 关联查询

**2. SalesOrderItem 明细表**
- `product_code` → 可通过 `product_id` 关联查询
- `product_name` → 可通过 `product_id` 关联查询
- `spec_code` → 可通过 `spec_id` 关联查询
- `brand_name` → 可通过 `brand_id` 关联查询
- `warehouse_name` → 可通过 `warehouse_id` 关联查询

**3. PurchaseOrder 主表**
- `brand_name` → 可通过 `brand_id` 关联查询
- `supplier_name` → 可通过 `supplier_id` 关联查询

**4. PurchaseOrderItem 明细表**
- `brand_name` → 可通过 `brand_id` 关联查询
- `warehouse_name` → 可通过 `warehouse_id` 关联查询

**5. Customer 表**
- `sales_user_name` → 可通过 `sales_user_id` 关联查询

**6. CustomerDiscount 表**
- `brand_name` → 可通过 `brand_id` 关联查询

**7. Brand 表**
- `purchaser_name` → 可通过 `purchaser_id` 关联查询

**8. Warehouse 表**
- `manager_name` → 可通过 `manager_id` 关联查询

**9. Stock/InboundBatch/OutboundBatch 表**
- `product_code`、`product_name`、`spec_code` → 可通过外键关联查询
- `user_name` → 可通过 `user_id` 关联查询

### 变更方案

**BREAKING** 这是一个破坏性变更，需要：
1. 修改数据库表结构（删除冗余字段）
2. 修改 Model 定义（添加外键关联）
3. 修改 Service 层（使用 prefetch_related 查询）
4. 修改 API 响应格式（通过关联查询返回名称）
5. 修改前端代码（移除冗余字段传入）

## Capabilities

### New Capabilities

- `mysql-relation-based-query`: MySQL 外键关联查询规范，定义如何使用 Tortoise ORM 的 ForeignKeyField 和 prefetch_related 进行关联查询

### Modified Capabilities

- `sales-order-model`: 销售订单数据模型重构，移除冗余字段，添加外键关联
- `purchase-order-model`: 采购单数据模型重构，移除冗余字段，添加外键关联
- `customer-model`: 客户数据模型重构，移除冗余字段
- `inventory-model`: 库存数据模型重构，移除冗余字段

## Impact

- **数据库**: 需要执行数据库迁移，删除冗余字段
- **后端代码**: Model、Service、API 响应格式需要修改
- **前端代码**: 移除冗余字段传入，依赖后端返回关联数据
- **API 兼容性**: 破坏性变更，需要前后端同步发布
