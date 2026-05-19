## Why

当前销售单列表展示信息不够完整，缺少成本、利润、财务状态等关键业务数据，无法支持业务人员快速评估订单盈利情况。同时列表缺少展开行功能，无法在列表页直接查看商品明细，需要跳转到详情页，操作效率低。

## What Changes

### 主表新增字段
- 新增 `finance_status` 字段（财务状态：未付款/部分付款/已付款/已对账）
- 新增 `SalesOrderCostItem` 模型（成本明细表），支持记录采购成本、运费、调货费等
- 列表接口返回实时计算的 `cost_amt`（成本总额）和 `profit_amt`（利润）

### 明细新增字段
- 新增 `exchange_qty` 字段（换货数量）
- 新增 `supplement_qty` 字段（补货数量）

### 前端列表改造
- 列表列配置调整为：订单日期、订单编号、客户名称、订单金额、订单状态、成本、利润、财务状态、发票状态、发货状态、收货状态、业务员、操作
- 新增展开行功能，展开显示商品明细（品牌名、规格编号、产品名称、规格、包装单位、数量、原价、退/换/补货数量、含税单价、合计）
- 新增行选中功能，支持批量操作

### 成本明细自动创建
- 采购单审核通过时，自动为关联销售单创建成本明细：
  - 采购成本（cost_type=purchase）：金额为采购单含税总金额
  - 运费成本（cost_type=freight）：金额为采购单运费（如有）

### 利润计算公式
- 利润 = 含税销售额 - 含税成本

### 采购单运费支持
- 采购单已有 `freight_amt` 字段支持录入运费
- 预留：物流单号对接快递平台接口自动获取运费（待后续实现）

## Capabilities

### New Capabilities
- `sales-order-cost-tracking`: 销售单成本明细管理，支持记录采购成本、运费、调货费等，实时计算利润
- `sales-order-list-expand`: 销售单列表展开行功能，在列表页直接查看商品明细
- `sales-order-row-selection`: 销售单列表行选中功能，支持批量操作

### Modified Capabilities
- `sales-order-list`: 列表接口返回数据增强，新增 cost_amt、profit_amt、finance_status 字段，返回商品明细用于展开展示

## Impact

### 后端影响
- `models_mysql/sales_order.py`: 新增 SalesOrderCostItem 模型，SalesOrder 和 SalesOrderItem 新增字段
- `services/sales_order_service_mysql.py`: 列表接口增强，成本明细 CRUD 服务
- `services/purchase_order_service_mysql.py`: 审核通过时创建成本明细（采购成本+运费）
- `app/routers/sales_order.py`: 新增成本明细 API 路由
- 数据库迁移脚本

### 前端影响
- `web/src/components/workspace/SalesOrderList.vue`: 列表改造，展开行、选中功能
- `web/src/services/api.ts`: 新增成本明细 API 调用

### 数据库影响
- 新增表 `sales_order_cost_items`
- `sales_orders` 表新增 `finance_status` 字段
- `sales_order_items` 表新增 `exchange_qty`、`supplement_qty` 字段
