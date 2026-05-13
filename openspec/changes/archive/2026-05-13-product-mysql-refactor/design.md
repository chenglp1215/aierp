## Context

当前 product 模块使用 MongoDB 存储，包含四个核心实体：
- **Brand（品牌）**: 品牌信息，关联采购人员
- **Category（分类）**: 商品分类，支持多级树形结构
- **Product（商品）**: 商品信息，关联品牌和分类
- **ProductSpec（商品规格）**: 商品规格信息，关联商品

项目正在从 MongoDB 迁移到 MySQL，auth 模块已完成迁移。本次需要将 product 模块迁移到 MySQL，使用 Tortoise ORM。

## Goals / Non-Goals

**Goals:**
- 创建 MySQL 数据模型（Brand、Category、Product、ProductSpec）
- 重写服务层使用 MySQL/Tortoise ORM
- 保持 API 接口兼容性（前端无需修改）
- 支持数据迁移（从 MongoDB 到 MySQL）

**Non-Goals:**
- 不修改前端代码
- 不新增 API 接口
- 不修改 API 响应格式

## Decisions

### 1. 数据模型设计

**决定**: 使用 Tortoise ORM 定义 MySQL 模型，ID 类型使用 int（自增主键）

**理由**:
- 与 auth 模块保持一致
- MySQL 自增主键性能优于 ObjectId
- 外键关联更清晰

**模型结构**:

```
Brand (brands 表)
├── id: IntField (PK)
├── name: CharField (unique)
├── logo_url: CharField (nullable)
├── description: CharField (nullable)
├── purchaser_id: IntField (nullable, FK -> User)
├── is_active: BooleanField
├── created_at: DatetimeField
└── updated_at: DatetimeField

Category (categories 表)
├── id: IntField (PK)
├── name: CharField (unique)
├── parent_id: IntField (nullable, FK -> Category)
├── tax_code: CharField (nullable)
├── sort_order: IntField
├── is_shop_display: BooleanField
├── level: IntField (computed)
├── created_at: DatetimeField
└── updated_at: DatetimeField

Product (products 表)
├── id: IntField (PK)
├── product_code: CharField (unique)
├── name: CharField
├── image_url: CharField (nullable)
├── brand_id: IntField (FK -> Brand)
├── category_id: IntField (FK -> Category)
├── tax_code: CharField (nullable)
├── is_active: BooleanField
├── created_at: DatetimeField
└── updated_at: DatetimeField

ProductSpec (product_specs 表)
├── id: IntField (PK)
├── product_id: IntField (FK -> Product)
├── spec_code: CharField (unique)
├── packaging: CharField (nullable)
├── sales_spec: CharField (nullable)
├── price: FloatField
├── cas_number: CharField (nullable)
├── is_active: BooleanField
├── created_at: DatetimeField
├── updated_at: DatetimeField
```

### 2. 服务层重构方式

**决定**: 创建新的 MySQL 服务层文件，保持原有 MongoDB 服务层不变

**理由**:
- 避免一次性大规模修改
- 可以逐步迁移，降低风险
- 原有 MongoDB 服务可作为备份

**替代方案**:
- 直接修改原有服务层：风险高，难以回滚

### 3. API 兼容性处理

**决定**: 在路由层进行 ID 类型转换，保持 API 使用 string 类型 ID

**理由**:
- 前端代码无需修改
- MongoDB ObjectId 是 string，MySQL int 需转换
- 在路由层转换，服务层使用原生类型

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| MongoDB 数据迁移丢失 | 编写迁移脚本，验证数据完整性 |
| ID 类型转换错误 | 路由层统一处理，添加类型验证 |
| 分类树形结构查询性能 | 使用递归查询或缓存优化 |
| 外键约束影响删除 | 使用级联删除或软删除 |