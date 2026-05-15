## MODIFIED Requirements

### Requirement: 销售订单明细数据完整性
新建销售订单时，系统 SHALL 将完整的商品信息存储到订单明细中，包括 `product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name` 等字段。

#### Scenario: 新建订单提交完整商品信息
- **WHEN** 用户在新建销售订单页面选择商品并提交订单
- **THEN** 系统将以下字段存储到 `sales_order_items` 表：
  - `product_id`：商品ID
  - `product_name`：商品名称
  - `spec_id`：规格ID
  - `spec_code`：规格编号
  - `brand_id`：品牌ID
  - `brand_name`：品牌名称
  - `warehouse_id`：仓库ID（非直发时）
  - `warehouse_name`：仓库名称（非直发时）

### Requirement: 发货方式中文显示
销售订单明细的发货方式 SHALL 以中文形式展示，而非英文枚举值。

#### Scenario: 后端返回中文发货方式
- **WHEN** 后端 `SalesOrderItem.to_dict()` 方法被调用
- **THEN** `shipping_method` 字段返回中文值：
  - "直运" 对应 `ShippingMethod.DIRECT`
  - "仓库发货" 对应 `ShippingMethod.WAREHOUSE`

#### Scenario: 前端展示发货方式
- **WHEN** 用户查看销售订单详情页面
- **THEN** 发货方式列显示中文值（"直运" 或 "仓库发货"）

### Requirement: 直发时仓库信息显示
当订单明细的发货方式为直发时，仓库相关字段 SHALL 显示为 "--"。

#### Scenario: 详情页直发明细仓库显示
- **WHEN** 用户查看销售订单详情页面，某明细发货方式为"直运"
- **THEN** 仓库列显示 "--"

#### Scenario: 下推采购弹窗直发明细仓库显示
- **WHEN** 用户打开下推采购选择弹窗，某明细发货方式为"直运"
- **THEN** 仓库相关字段显示 "--"

## ADDED Requirements

### Requirement: 商品明细表格仓库列
销售订单详情页面的商品明细表格 SHALL 包含仓库列，展示订单明细的仓库信息。

#### Scenario: 详情页显示仓库列
- **WHEN** 用户查看销售订单详情页面
- **THEN** 商品明细表格包含"仓库"列，显示 `warehouse_name` 或 "--"（直发时）