## 1. 前端修改

- [x] 1.1 修改 `SalesOrderWorkspace.vue` 中的 `handleProductSearch` 函数，移除对 `productApi.search` 的调用
- [x] 1.2 简化搜索逻辑，只使用 `productApi.searchSpecs` 搜索规格
- [x] 1.3 移除商品树构建逻辑，直接使用规格搜索结果
- [x] 1.4 调整搜索结果展示，确保规格列表正确显示

## 2. 验证

- [x] 2.1 测试商品搜索功能，输入关键字能正确返回规格列表
- [x] 2.2 验证选择规格后能正确填充到订单行
- [x] 2.3 验证不再出现 "无效的ID格式" 错误