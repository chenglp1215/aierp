## Context

采购单模块已完成从 MongoDB 到 MySQL 的迁移（Tortoise ORM），但数据模型设计仍保留 MongoDB 时代的冗余字段模式。当前 PurchaseOrder 和 PurchaseOrderItem 模型中存在以下冗余字段：

- `PurchaseOrder.brand_name` - 冗余存储品牌名称
- `PurchaseOrder.supplier_name` - 冗余存储供应商名称（暂保留，因 Supplier 表未建立）
- `PurchaseOrderItem.brand_name` - 冗余存储品牌名称
- `PurchaseOrderItem.warehouse_name` - 冗余存储仓库名称

销售订单模块已完成类似重构（SalesOrderItem 通过 `spec` 外键关联 ProductSpec，再通过关联链获取 Product 和 Brand），采购单应采用相同的设计模式以保持一致性。

## Goals / Non-Goals

**Goals:**
1. 移除 PurchaseOrderItem 中的 `brand_name`、`warehouse_name` 冗余字段
2. 添加 ForeignKeyField 关联 ProductSpec、Warehouse
3. 通过关联链获取 product、brand 信息（spec → product → brand）
4. 更新 Service 层使用 `prefetch_related` 预加载关联数据
5. 保持 API 响应格式兼容，前端无需修改

**Non-Goals:**
1. 不修改 PurchaseOrder 主表的 `supplier_name`（Supplier 表未建立）
2. 不修改前端代码（API 响应格式保持兼容）
3. 不添加新的业务功能

## Decisions

### 1. PurchaseOrderItem 外键设计

**决策：** 采用与 SalesOrderItem 相同的外键设计模式

```python
# PurchaseOrderItem 外键关联
spec: fields.ForeignKeyNullableRelation["ProductSpec"] = fields.ForeignKeyField(
    "models.ProductSpec", related_name="purchase_order_items", null=True, description="规格"
)
warehouse: fields.ForeignKeyNullableRelation["Warehouse"] = fields.ForeignKeyField(
    "models.Warehouse", related_name="purchase_order_items", null=True, description="仓库"
)
```

**理由：**
- ProductSpec 关联 Product，Product 关联 Brand
- 只需直接关联 `spec` 和 `warehouse`，其他信息通过关联链获取
- 与 SalesOrderItem 设计保持一致，便于理解和维护

**替代方案：**
- 直接关联 Product、Brand、Warehouse（不采用）
  - 缺点：冗余外键，spec 已关联 product，再关联 product 是多余的

### 2. PurchaseOrder 主表外键设计

**决策：** 添加 Brand 外键关联，保留 supplier_name 作为快照

```python
# PurchaseOrder 外键关联
brand: fields.ForeignKeyNullableRelation["Brand"] = fields.ForeignKeyField(
    "models.Brand", related_name="purchase_orders", null=True, description="品牌"
)
# 保留 supplier_name 作为快照（Supplier 表未建立）
```

**理由：**
- Brand 表已存在，可建立外键关联
- Supplier 表未建立，暂时保留 supplier_name 字段

### 3. 冗余字段处理策略

**决策：** 删除冗余字段，不保留快照

**理由：**
- 采购单明细的品牌、仓库名称可通过关联实时查询
- 不需要历史快照（品牌、仓库名称变更时应同步更新）
- 与 SalesOrderItem 的处理方式一致

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 数据库迁移失败 | 先备份数据，迁移脚本使用 `DROP COLUMN IF EXISTS` |
| 关联查询性能下降 | 使用 `prefetch_related` 预加载，避免 N+1 查询 |
| API 响应格式变化 | `to_dict()` 方法保持返回相同字段名，前端无需修改 |
| 外键约束导致删除失败 | 使用 `null=True`，`on_delete=fields.SET_NULL` |

## Migration Plan

1. **备份数据库**：导出 purchase_orders、purchase_order_items 表结构和数据
2. **修改 Model 定义**：添加 ForeignKeyField，移除冗余字段定义
3. **更新 Service 层**：使用 prefetch_related 预加载关联数据
4. **执行数据库迁移**：删除冗余字段列
5. **测试验证**：运行 API 测试确保功能正常