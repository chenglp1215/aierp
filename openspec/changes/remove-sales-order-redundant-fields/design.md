## Context

项目已完成从 MongoDB 到 MySQL 的迁移，使用 Tortoise ORM 作为 ORM 框架。当前数据模型中存在大量冗余字段（如 `brand_name`、`customer_name` 等），这些字段在 MongoDB 时代是为了避免多次查询而冗余存储的，但在 MySQL 环境下可以通过外键关联高效查询。

**当前问题：**
- 9 个模型文件中存在冗余字段
- 数据一致性风险：源数据更新后冗余字段可能不同步
- API 设计混乱：前端需要传入 `brand_name`、`warehouse_name` 等冗余字段

**技术约束：**
- Tortoise ORM 支持 ForeignKeyField 和 prefetch_related
- 需要保证 API 响应格式向后兼容（返回关联数据）
- 需要数据库迁移脚本

## Goals / Non-Goals

**Goals:**
- 移除所有冗余的 `*_name` 字段
- 使用 Tortoise ORM 的 ForeignKeyField 建立外键关联
- 使用 prefetch_related 优化查询性能
- 保持 API 响应格式不变（仍返回关联的名称）
- 简化 API 请求格式（前端只需传入 ID）

**Non-Goals:**
- 不修改业务逻辑
- 不修改前端代码（前端适配另行处理）
- 不修改权限控制逻辑

## Decisions

### 1. 外键关联策略

**决策**：使用 Tortoise ORM 的 ForeignKeyField 建立真正的外键关联

**理由**：
- MySQL 支持外键约束，保证数据完整性
- Tortoise ORM 的 ForeignKeyField 支持 prefetch_related 预加载
- 查询性能可通过预加载优化

**替代方案**：
- 保留冗余字段 + 定时同步 → 复杂度高，仍有数据不一致风险
- 不使用外键约束，仅逻辑关联 → 无法保证数据完整性

**示例**：
```python
# 修改前
class SalesOrderItem(Model):
    brand_id = fields.IntField(null=True)
    brand_name = fields.CharField(max_length=100, null=True)

# 修改后
class SalesOrderItem(Model):
    brand: fields.ForeignKeyRelation[Brand] = fields.ForeignKeyField(
        "models.Brand", related_name="sales_order_items", null=True
    )
```

### 2. API 响应格式策略

**决策**：API 响应中仍返回关联的名称，通过 prefetch_related 查询

**理由**：
- 保持 API 向后兼容
- 前端无需修改即可获取完整数据
- prefetch_related 可避免 N+1 查询问题

**示例**：
```python
# Service 层查询
orders = await SalesOrder.filter(...).prefetch_related("items__brand", "items__warehouse")

# to_dict 中返回关联数据
async def to_dict(self):
    brand = await self.brand
    return {
        "brand_id": self.brand_id,
        "brand_name": brand.name if brand else None,
        ...
    }
```

### 3. 迁移策略

**决策**：分阶段迁移，每个模块独立迁移

**理由**：
- 降低风险，可逐步验证
- 出问题可快速回滚
- 便于代码审查

**迁移顺序**：
1. SalesOrder 模块（最复杂，优先处理）
2. PurchaseOrder 模块
3. Customer 模块
4. Inventory 模块
5. Brand/Warehouse 模块

### 4. 保留部分冗余字段

**决策**：以下字段保留冗余存储

- `customer_name` 在 SalesOrder 中 → 保留（订单创建时客户名称快照，用于历史查询）
- `source_sale_order_no` 在 PurchaseOrder 中 → 保留（跨模块引用，源订单可能被删除）

**理由**：
- 订单是历史记录，需要保留创建时的数据快照
- 客户/供应商名称变更后，历史订单应显示原名称
- 符合财务审计要求

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 查询性能下降（关联查询） | 使用 prefetch_related 预加载，避免 N+1 问题 |
| 数据库迁移失败 | 先备份数据库，迁移脚本支持回滚 |
| API 响应格式变更导致前端报错 | 保持响应格式不变，名称字段通过关联查询返回 |
| 外键约束导致删除失败 | 设置 on_delete=SET_NULL 或级联删除策略 |

## Migration Plan

### Phase 1: 准备工作
1. 备份生产数据库
2. 创建数据库迁移脚本
3. 编写单元测试

### Phase 2: 模型修改
1. 修改 Model 定义，添加 ForeignKeyField
2. 移除冗余字段定义
3. 更新 to_dict 方法

### Phase 3: Service 层修改
1. 更新创建/更新逻辑，移除冗余字段处理
2. 添加 prefetch_related 查询
3. 更新列表/详情查询

### Phase 4: 数据库迁移
1. 执行 ALTER TABLE 删除冗余字段
2. 添加外键约束
3. 验证数据完整性

### Phase 5: 验证
1. 运行单元测试
2. 运行 API 测试
3. 前端功能验证

## Open Questions

1. **是否需要保留订单明细中的 `product_code`、`spec_code`？**
   - 这些编码在商品/规格被删除后仍需显示
   - 建议：保留，作为历史快照

2. **用户相关的 `*_name` 字段如何处理？**
   - `creator_name`、`sale_user_name` 等
   - 建议：通过关联查询获取，不冗余存储

3. **前端适配时机？**
   - 建议：后端完成后，前端逐步适配
   - API 响应格式不变，前端可继续使用
