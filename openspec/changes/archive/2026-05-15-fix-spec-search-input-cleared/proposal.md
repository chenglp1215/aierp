## Why

销售订单商品明细搜索商品规格时，用户输入的关键字在接口返回后被清空，下拉框也不显示。问题原因是输入框使用 `:value` 绑定到 `item.product_name`（已选商品名称），而不是用户输入的搜索关键字。当用户输入时，输入框显示的仍是 `item.product_name`，导致用户输入"被清空"的错觉。

## What Changes

- 添加 `productSearchKeywords` 变量保存每个订单行的搜索关键字
- 修改输入框绑定，优先显示用户输入的搜索关键字，其次显示已选商品名称
- 修改 `handleProductSearch` 函数，接收订单行索引参数并保存搜索关键字
- 选择规格后清空对应的搜索关键字

## Capabilities

### New Capabilities
<!-- 无新增能力 -->

### Modified Capabilities
- `sales-order-workspace`: 修改商品搜索输入框绑定逻辑，正确保存和显示用户输入的搜索关键字

## Impact

- **前端**: `web/src/components/workspace/SalesOrderWorkspace.vue` 修改搜索关键字保存和显示逻辑
- **后端**: 无需修改
- **API**: 无需修改