## 1. 后端 - 规格库存详情接口

- [ ] 1.1 在 `backend/app/routers/product.py` 中添加 `/specs/{spec_id}/stock-detail` 接口
- [ ] 1.2 接口调用 `stock_service.get_stock_status_by_spec_ids` 获取库存数据
- [ ] 1.3 返回格式包含 `spec_id`、`items`（仓库列表）和 `total_quantity`

## 2. 前端 - 销售订单提交修复

- [ ] 2.1 在 `web/src/components/workspace/SalesOrderWorkspace.vue` 的 `submitData` 中添加 `customer_name` 字段
- [ ] 2.2 在 `web/src/components/workspace/SalesOrderCreate.vue` 的提交数据中添加 `customer_name` 字段

## 3. 验证

- [ ] 3.1 测试销售订单创建并提交接口，确认 `customer_name` 正确传递
- [ ] 3.2 测试规格库存详情接口返回正确数据
