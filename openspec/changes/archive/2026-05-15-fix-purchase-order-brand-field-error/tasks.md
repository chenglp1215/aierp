## 1. 修复服务层字段访问

- [x] 1.1 修改 `purchase_order_service_mysql.py` 的 `create_from_sales_order` 方法，通过关联链获取 brand_id
- [x] 1.2 在路由层调用前添加 `select_related` 预加载关联数据

## 2. 验证修复

- [x] 2.1 测试下推采购接口，验证正常商品分组逻辑
- [x] 2.2 测试无品牌商品的下推场景
