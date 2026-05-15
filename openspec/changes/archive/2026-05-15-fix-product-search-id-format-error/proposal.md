## Why

新建销售订单时，商品搜索功能报错 "无效的ID格式"，导致用户无法正常选择商品。问题原因是前端 `handleProductSearch` 函数并行调用了 `productApi.search` 和 `productApi.searchSpecs`，但后端缺少 `/products/search` 路由。FastAPI 将 `/products/search` 请求错误匹配到 `/{product_id}` 路由，"search" 字符串被当作 product_id 传入 `to_int_id()` 函数导致转换失败。

根据用户需求，商品搜索只需要搜索规格编码，不需要搜索产品。因此解决方案是移除前端对 `productApi.search` 的调用。

## What Changes

- 移除前端 `SalesOrderWorkspace.vue` 中对 `productApi.search` 的调用
- 只保留 `productApi.searchSpecs` 调用，搜索规格编码
- 简化搜索逻辑，直接使用规格搜索结果

## Capabilities

### New Capabilities
<!-- 无新增能力 -->

### Modified Capabilities
- `sales-order-workspace`: 修改商品搜索逻辑，只搜索规格编码

## Impact

- **前端**: `web/src/components/workspace/SalesOrderWorkspace.vue` 修改 `handleProductSearch` 函数
- **后端**: 无需修改
- **API**: 无需新增接口