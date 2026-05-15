## MODIFIED Requirements

### Requirement: Stock 数据模型

系统 SHALL 使用外键关联替代冗余字段存储。

#### Scenario: 商品关联
- **WHEN** 库存关联商品
- **THEN** 使用 ForeignKeyField 关联 Product 模型，移除 product_code、product_name 冗余字段

#### Scenario: 规格关联
- **WHEN** 库存关联规格
- **THEN** 使用 ForeignKeyField 关联 ProductSpec 模型，移除 spec_code 冗余字段

### Requirement: InboundBatch 数据模型

系统 SHALL 使用外键关联替代冗余字段存储。

#### Scenario: 商品和规格关联
- **WHEN** 入库批次关联商品和规格
- **THEN** 使用 ForeignKeyField 关联 Product 和 ProductSpec 模型，移除冗余字段

#### Scenario: 用户关联
- **WHEN** 入库批次关联操作用户
- **THEN** 使用 ForeignKeyField 关联 User 模型，移除 user_name 冗余字段

### Requirement: OutboundBatch 数据模型

系统 SHALL 使用外键关联替代冗余字段存储。

#### Scenario: 商品和规格关联
- **WHEN** 出库批次关联商品和规格
- **THEN** 使用 ForeignKeyField 关联 Product 和 ProductSpec 模型，移除冗余字段

#### Scenario: 用户关联
- **WHEN** 出库批次关联操作用户
- **THEN** 使用 ForeignKeyField 关联 User 模型，移除 user_name 冗余字段