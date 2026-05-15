## 1. 后端 - 修复空字符串整数字段处理

- [ ] 1.1 在 `backend/services/sales_order_service_mysql.py` 的 `create_order` 方法中，添加辅助函数处理空字符串整数字段
- [ ] 1.2 在创建订单明细时，对 `warehouse_id`、`product_id`、`spec_id`、`brand_id` 等整数字段进行空字符串转换

## 2. 验证

- [ ] 2.1 测试直运订单创建（无仓库ID）
- [ ] 2.2 测试正常仓库发货订单创建
