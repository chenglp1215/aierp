## Context

当前 customer 模块使用 MongoDB 存储，数据结构为嵌套文档模式：
- Customer 文档内嵌 invoice_infos（开票信息）和 shipping_addresses（收货地址）
- CustomerDiscount 作为独立集合存储

product 模块已成功迁移到 MySQL（Tortoise ORM），提供了成熟的参考实现：
- `backend/models_mysql/product.py` - 模型定义
- `backend/services/product_service_mysql.py` - 服务层实现
- 使用外键关联（Product → Brand, Category）
- 使用 `to_dict()` 方法统一输出格式

## Goals / Non-Goals

**Goals:**
- 将 customer 模块数据存储从 MongoDB 迁移到 MySQL
- 使用 Tortoise ORM 定义数据模型，保持与 product 模块一致的风格
- 拆分嵌套文档为独立表（customers, invoice_infos, shipping_addresses, customer_discounts）
- 保持 API 接口格式完全兼容，前端无需修改
- 提供数据迁移脚本

**Non-Goals:**
- 不修改前端代码
- 不修改 API 接口路径和参数
- 不修改验证规则
- 不重构业务逻辑

## Decisions

### 1. 数据模型设计

**决策**: 拆分为 4 张独立表，使用外键关联

```
customers (主表)
├── invoice_infos (一对多，外键 customer_id)
├── shipping_addresses (一对多，外键 customer_id)
└── customer_discounts (一对多，外键 customer_id)
```

**理由**:
- MongoDB 嵌套文档在 MySQL 中需要拆分为独立表
- 外键关联保证数据完整性，支持级联删除
- 与 product 模块的 Product → ProductSpec 结构一致

**备选方案**:
- JSON 字段存储嵌套数据 → 查询和更新不便，无法使用外键约束

### 2. 主键类型

**决策**: 使用自增整型主键 (IntField, pk=True)

**理由**:
- 与 product 模块保持一致（Brand, Category, Product 都使用 IntField）
- MySQL 自增主键性能优于 UUID
- 前端 API 返回的 id 字段需要从字符串改为整数

**备选方案**:
- UUID 主键 → 与现有 MongoDB 字符串 ID 兼容，但性能较差且与项目风格不一致

### 3. 服务层设计

**决策**: 创建 `CustomerServiceMySQL` 类，参考 `ProductService` 实现

**理由**:
- 保持与 product_service_mysql.py 一致的代码风格
- 使用 Tortoise ORM 的 async 方法
- `to_dict()` 方法返回包含关联数据的字典

### 4. API 兼容性

**决策**: 保持 API 响应格式不变，在服务层处理数据转换

**理由**:
- 前端代码无需修改
- 列表接口返回 `items` 数组，详情接口返回完整对象
- 开票信息和收货地址作为嵌套数组返回

### 5. 数据迁移

**决策**: 编写独立迁移脚本，支持增量迁移和验证

**理由**:
- 可在服务运行期间迁移，不影响业务
- 支持迁移后数据校验
- 可回滚

## Risks / Trade-offs

**风险 1: ID 类型变更**
- MongoDB 使用字符串 ID（如 "507f1f77bcf86cd799439011"）
- MySQL 使用整数 ID
- **缓解**: 迁移脚本建立旧 ID 到新 ID 的映射，更新关联表（如 sales_orders 中的 customer_id）

**风险 2: 数据一致性**
- 迁移期间可能有新数据写入 MongoDB
- **缓解**: 迁移脚本支持增量同步，迁移完成后切换服务层

**风险 3: 关联模块影响**
- sales_orders、accounts_receivable 等模块引用 customer_id
- **缓解**: 迁移脚本更新所有关联表的 customer_id 字段

**权衡: 查询性能**
- MongoDB 嵌套文档一次查询获取所有数据
- MySQL 需要关联查询或多次查询
- **权衡**: 使用 `prefetch_related` 优化查询，性能差异可接受