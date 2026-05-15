## MODIFIED Requirements

### Requirement: SalesOrderItem 数据模型

系统 SHALL 使用外键关联替代冗余字段存储。

#### Scenario: 品牌关联
- **WHEN** 订单明细关联品牌
- **THEN** 使用 ForeignKeyField 关联 Brand 模型，移除 brand_name 冗余字段

#### Scenario: 仓库关联
- **WHEN** 订单明细关联仓库
- **THEN** 使用 ForeignKeyField 关联 Warehouse 模型，移除 warehouse_name 冗余字段

#### Scenario: 商品关联
- **WHEN** 订单明细关联商品
- **THEN** 使用 ForeignKeyField 关联 Product 模型，移除 product_name、product_code 冗余字段

#### Scenario: 规格关联
- **WHEN** 订单明细关联规格
- **THEN** 使用 ForeignKeyField 关联 ProductSpec 模型，移除 spec_code 冗余字段

### Requirement: SalesOrder 数据模型

系统 SHALL 使用外键关联替代部分冗余字段，保留必要的快照字段。

#### Scenario: 客户关联
- **WHEN** 订单关联客户
- **THEN** 使用 ForeignKeyField 关联 Customer 模型，保留 customer_name 作为历史快照

#### Scenario: 销售人员关联
- **WHEN** 订单关联销售人员
- **THEN** 使用 ForeignKeyField 关联 User 模型，移除 sale_user_name 冗余字段

#### Scenario: 创建人关联
- **WHEN** 订单关联创建人
- **THEN** 使用 ForeignKeyField 关联 User 模型，移除 creator_name 冗余字段
