## ADDED Requirements

### Requirement: Brand 服务层
系统 SHALL 提供 Brand 服务层，使用 Tortoise ORM 操作 MySQL。

#### Scenario: 创建品牌服务
- **WHEN** 调用 create_brand 方法时
- **THEN** 系统 SHALL 验证品牌名称唯一性
- **AND** 创建 Brand 记录并返回

#### Scenario: 查询品牌服务
- **WHEN** 调用 get_brand_by_id 方法时
- **THEN** 系统 SHALL 从 brands 表查询记录
- **AND** 返回品牌信息

### Requirement: Category 服务层
系统 SHALL 提供 Category 服务层，支持树形结构查询。

#### Scenario: 获取分类树
- **WHEN** 调用 get_category_tree 方法时
- **THEN** 系统 SHALL 返回完整的分类树结构
- **AND** 包含所有子分类

#### Scenario: 删除分类验证
- **WHEN** 删除分类时
- **THEN** 系统 SHALL 检查是否有子分类
- **AND** 检查是否有商品关联
- **AND** 若存在关联则拒绝删除

### Requirement: Product 服务层
系统 SHALL 提供 Product 服务层，关联品牌和分类。

#### Scenario: 创建商品服务
- **WHEN** 调用 create_product 方法时
- **THEN** 系统 SHALL 验证品牌和分类存在
- **AND** 自动填充 brand_name 和 category_name
- **AND** 创建商品及其规格

#### Scenario: 删除商品服务
- **WHEN** 删除商品时
- **THEN** 系统 SHALL 同时删除关联的商品规格

### Requirement: ProductSpec 服务层
系统 SHALL 提供 ProductSpec 服务层，关联商品。

#### Scenario: 查询商品规格
- **WHEN** 调用 get_spec_by_product_id 方法时
- **THEN** 系统 SHALL 返回指定商品的所有规格

#### Scenario: 批量查询规格
- **WHEN** 调用 get_spec_by_product_ids 方法时
- **THEN** 系统 SHALL 返回多个商品的规格映射