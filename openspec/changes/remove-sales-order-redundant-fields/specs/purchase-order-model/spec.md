## MODIFIED Requirements

### Requirement: PurchaseOrderItem 数据模型

系统 SHALL 使用外键关联替代冗余字段存储。

#### Scenario: 品牌关联
- **WHEN** 采购单明细关联品牌
- **THEN** 使用 ForeignKeyField 关联 Brand 模型，移除 brand_name 冗余字段

#### Scenario: 仓库关联
- **WHEN** 采购单明细关联仓库
- **THEN** 使用 ForeignKeyField 关联 Warehouse 模型，移除 warehouse_name 冗余字段

### Requirement: PurchaseOrder 数据模型

系统 SHALL 使用外键关联替代冗余字段存储，保留必要的快照字段。

#### Scenario: 品牌关联
- **WHEN** 采购单关联品牌
- **THEN** 使用 ForeignKeyField 关联 Brand 模型，移除 brand_name 冗余字段

#### Scenario: 供应商关联
- **WHEN** 采购单关联供应商
- **THEN** 使用 ForeignKeyField 关联 Supplier 模型，保留 supplier_name 作为历史快照

#### Scenario: 源订单引用
- **WHEN** 采购单引用源销售订单
- **THEN** 保留 source_sale_order_no 作为跨模块引用快照
