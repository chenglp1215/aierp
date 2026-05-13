## ADDED Requirements

### Requirement: Brand 数据模型
系统 SHALL 使用 MySQL 存储 Brand（品牌）数据，使用 Tortoise ORM 模型。

#### Scenario: 创建品牌
- **WHEN** 创建品牌时
- **THEN** 系统 SHALL 在 brands 表中插入记录
- **AND** 自动生成 int 类型 ID
- **AND** 自动设置 created_at 和 updated_at

#### Scenario: 品牌名称唯一
- **WHEN** 创建或更新品牌时
- **THEN** 系统 SHALL 验证品牌名称唯一性

### Requirement: Category 数据模型
系统 SHALL 使用 MySQL 存储 Category（分类）数据，支持树形结构。

#### Scenario: 创建分类
- **WHEN** 创建分类时
- **THEN** 系统 SHALL 在 categories 表中插入记录
- **AND** 支持 parent_id 自关联实现树形结构

#### Scenario: 分类层级计算
- **WHEN** 查询分类时
- **THEN** 系统 SHALL 自动计算分类层级（level）

### Requirement: Product 数据模型
系统 SHALL 使用 MySQL 存储 Product（商品）数据，关联品牌和分类。

#### Scenario: 创建商品
- **WHEN** 创建商品时
- **THEN** 系统 SHALL 在 products 表中插入记录
- **AND** brand_id 关联 brands 表
- **AND** category_id 关联 categories 表

#### Scenario: 商品编号自动生成
- **WHEN** 创建商品未提供 product_code 时
- **THEN** 系统 SHALL 自动生成格式为 PROD{YYYYMMDD}{随机6位} 的编号

### Requirement: ProductSpec 数据模型
系统 SHALL 使用 MySQL 存储 ProductSpec（商品规格）数据，关联商品。

#### Scenario: 创建商品规格
- **WHEN** 创建商品规格时
- **THEN** 系统 SHALL 在 product_specs 表中插入记录
- **AND** product_id 关联 products 表

#### Scenario: 规格编号自动生成
- **WHEN** 创建规格未提供 spec_code 时
- **THEN** 系统 SHALL 自动生成格式为 SPEC{YYYYMMDD}{随机6位} 的编号
