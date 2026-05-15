## MODIFIED Requirements

### Requirement: Customer 数据模型

系统 SHALL 使用外键关联替代冗余字段存储。

#### Scenario: 销售人员关联
- **WHEN** 客户关联销售人员
- **THEN** 使用 ForeignKeyField 关联 User 模型，移除 sales_user_name 冗余字段

### Requirement: CustomerDiscount 数据模型

系统 SHALL 使用外键关联替代冗余字段存储。

#### Scenario: 品牌关联
- **WHEN** 客户折扣关联品牌
- **THEN** 使用 ForeignKeyField 关联 Brand 模型，移除 brand_name 冗余字段