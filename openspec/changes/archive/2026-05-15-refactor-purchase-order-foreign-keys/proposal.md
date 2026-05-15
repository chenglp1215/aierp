## Why

参照销售订单的重构方案，采购单数据模型中仍保留了冗余字段（如 `brand_name`、`supplier_name`、`warehouse_name`）。这些冗余字段是 MongoDB 时代的妥协方案，现在使用 MySQL + Tortoise ORM 后，应通过外键关联查询获取这些信息，而不是冗余存储。

**问题影响：**
1. 数据不一致风险：冗余字段可能与源数据不同步
2. 存储空间浪费：重复存储大量字符串数据
3. 维护成本高：更新名称时需要同步多处
4. 与已重构的销售订单模型设计不一致

## What Changes

### 识别到的冗余字段

**1. PurchaseOrder 主表**
- `brand_name` → 可通过 `brand_id` 外键关联 Brand 表查询
- `supplier_name` → 可通过 `supplier_id` 外键关联 Supplier 表查询（如有）

**2. PurchaseOrderItem 明细表**
- `brand_name` → 可通过 `brand_id` 外键关联 Brand 表查询
- `warehouse_name` → 可通过 `warehouse_id` 外键关联 Warehouse 表查询
- `product_id`、`spec_id` → 应改为 ForeignKeyField 关联 Product、ProductSpec 表

### 变更方案

参照 SalesOrderItem 的重构方案：
1. 修改 PurchaseOrder 模型，添加 Brand 外键关联
2. 修改 PurchaseOrderItem 模型，添加 ProductSpec、Brand、Warehouse 外键关联
3. 移除冗余字段 `brand_name`、`warehouse_name`（保留 `supplier_name` 作为快照，因 Supplier 表可能未建立）
4. 更新 Service 层，使用 `prefetch_related` 预加载关联数据
5. 更新 `to_dict()` 方法，通过关联对象返回名称

**注意：** PurchaseOrderItem 的设计应与 SalesOrderItem 保持一致：
- 通过 `spec` 外键关联 ProductSpec，ProductSpec 关联 Product，Product 关联 Brand
- 只需直接关联 `spec` 和 `warehouse`，其他信息通过关联链获取

## Capabilities

### New Capabilities

- `purchase-order-foreign-keys`: 采购单外键关联查询规范，定义如何使用 ForeignKeyField 和 prefetch_related 进行关联查询

### Modified Capabilities

- `purchase-order-model`: 采购单数据模型重构，移除冗余字段，添加外键关联

## Impact

- **数据库**: 需要执行数据库迁移，删除冗余字段，添加外键约束
- **后端代码**: Model、Service、API 响应格式需要修改
- **API 兼容性**: 响应格式保持兼容，通过关联查询返回名称字段