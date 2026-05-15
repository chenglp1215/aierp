## ADDED Requirements

<!-- 无新增需求 -->

## MODIFIED Requirements

### Requirement: 商品搜索功能

系统应允许用户在新建销售订单时，通过输入关键字搜索规格编码，返回匹配的规格列表。

#### Scenario: 用户输入关键字搜索规格

- **WHEN** 用户在商品搜索框中输入关键字
- **THEN** 系统调用 `/products/specs/search` 接口搜索规格编码
- **THEN** 系统返回匹配的规格列表，包含规格信息和关联的商品名称

#### Scenario: 搜索结果展示

- **WHEN** 搜索返回结果
- **THEN** 系统展示规格列表，包含规格编码、商品名称、包装、销售规格、价格等信息
- **THEN** 用户可以选择规格填充到订单行