## Why

销售订单详情页面存在多个显示问题：
1. **商品规格信息不全**：新建订单时，前端未将 `product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name` 等关键字段提交到后端，导致订单明细中这些字段为空
2. **发货方式显示英文**：后端 `SalesOrderItem.to_dict()` 返回 `shipping_method.value`（英文枚举值 "direct"/"warehouse"），前端未进行中文映射
3. **直发时仓库信息未处理**：当明细发货方式为直发时，仓库相关字段应显示为 "--"

这些问题影响用户体验和数据可读性，需要修复。

## What Changes

- **前端创建订单**：`SalesOrderCreate.vue` 的 `handleSaveOrder` 函数需要将完整的商品信息（`product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name`）提交到后端
- **后端**：`SalesOrderItem.to_dict()` 方法中 `shipping_method` 返回中文映射值（"直运"/"仓库发货"）而非英文枚举值
- **前端详情页**：
  - 在 `SalesOrderDetail.vue` 商品明细表格中添加仓库列，直发时显示 "--"
  - 移除 `handlePushPurchase` 中冗余的品牌信息查询逻辑（后端已返回）
  - 确保发货方式正确显示中文

## Capabilities

### New Capabilities
无新增能力

### Modified Capabilities
- `sales-order-detail-display`: 修改销售订单详情页面的数据展示逻辑，包括发货方式中文映射、仓库信息条件显示

## Impact

- **前端创建订单**：`web/src/components/workspace/SalesOrderCreate.vue` - `handleSaveOrder` 函数，提交完整的商品信息
- **后端**：`backend/models_mysql/sales_order.py` - `SalesOrderItem.to_dict()` 方法
- **前端详情页**：
  - `web/src/components/workspace/SalesOrderDetail.vue` - 商品明细表格、发货方式显示
  - `web/src/components/workspace/PushPurchaseItemSelectModal.vue` - 发货方式判断逻辑
