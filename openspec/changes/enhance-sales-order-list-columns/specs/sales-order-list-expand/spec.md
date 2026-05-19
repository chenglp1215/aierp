## ADDED Requirements

### Requirement: Expandable row UI
系统 SHALL 在销售单列表提供展开行功能，点击展开按钮可查看商品明细。

#### Scenario: Expand row to show items
- **WHEN** 用户点击销售单行的展开按钮
- **THEN** 系统在该行下方展开显示商品明细子表格

#### Scenario: Collapse row
- **WHEN** 用户点击已展开行的收起按钮
- **THEN** 系统收起商品明细子表格

### Requirement: Item detail columns
展开的商品明细 SHALL 显示以下列：
- 品牌名（brand_name）
- 规格编号（spec_code）
- 产品名称（product_name）
- 规格（sales_spec）
- 包装单位（packaging）
- 数量（qty）
- 原价（price）
- 退货数量（return_qty）
- 换货数量（exchange_qty）
- 补货数量（supplement_qty）
- 含税单价（price * (1 + tax_rate)）
- 合计（amt）

#### Scenario: Display item details
- **WHEN** 用户展开销售单行
- **THEN** 系统显示商品明细，包含上述所有列

### Requirement: Tax-inclusive price calculation
系统 SHALL 在前端计算含税单价。

#### Scenario: Calculate tax-inclusive price
- **WHEN** 显示商品明细
- **THEN** 含税单价 = price * (1 + sales_order.tax_rate)

### Requirement: List API returns items
销售单列表接口 SHALL 返回商品明细数据用于展开展示。

#### Scenario: API returns items for expansion
- **WHEN** GET /api/v1/sales-orders/
- **THEN** 每个销售单返回 `items` 数组，包含展开所需的所有字段
