## Why

当前 product 模块（brand、category、product、product_spec）使用 MongoDB 存储，与项目正在进行的 MySQL 迁移方向不一致。需要将这些模块重构为 MySQL 实现，以保持数据存储的一致性，并利用 MySQL 的事务支持和关系型查询能力。

## What Changes

- **Brand（品牌）**: 从 MongoDB 迁移到 MySQL，使用 Tortoise ORM 模型
- **Category（分类）**: 从 MongoDB 迁移到 MySQL，支持树形结构（parent_id 自关联）
- **Product（商品）**: 从 MongoDB 迁移到 MySQL，关联 Brand 和 Category
- **ProductSpec（商品规格）**: 从 MongoDB 迁移到 MySQL，关联 Product

### 数据模型变更

| 模型 | MongoDB 集合 | MySQL 表 | 主要变更 |
|------|-------------|----------|---------|
| Brand | product_brands | brands | ID 类型从 ObjectId 改为 int |
| Category | product_categories | categories | ID 类型从 ObjectId 改为 int，parent_id 自关联 |
| Product | products | products | ID 类型从 ObjectId 改为 int，外键关联 |
| ProductSpec | product_specs | product_specs | ID 类型从 ObjectId 改为 int，外键关联 |

## Capabilities

### New Capabilities

- `product-mysql-models`: 商品模块 MySQL 数据模型（Brand、Category、Product、ProductSpec）
- `product-mysql-services`: 商品模块 MySQL 服务层实现

### Modified Capabilities

无（这是内部实现重构，API 接口保持不变）

## Impact

- **后端模型**: 新建 `backend/models_mysql/product.py`
- **后端服务**: 重写 `backend/services/product_service.py` 使用 MySQL
- **后端路由**: `backend/app/routers/product.py` 保持不变（API 兼容）
- **数据库迁移**: 需要创建新的 MySQL 表
- **前端**: 无影响（API 接口保持兼容）
