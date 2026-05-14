## 1. 后端接口实现

- [x] 1.1 在 `backend/app/routers/product.py` 的 `brand_router` 中添加 `GET /purchaser-candidates` 路由
- [x] 1.2 实现路由处理函数，调用 `mysql_user_service.list_users()` 并传入 `role='purchaser_group'` 参数
- [x] 1.3 格式化返回数据，仅保留 `id`、`full_name`、`username` 字段
- [x] 1.4 添加权限检查，要求 `brand.view` 权限

## 2. 测试验证

- [x] 2.1 启动后端服务，验证接口返回正确的采购组用户列表
- [x] 2.2 验证前端品牌管理页面采购人员下拉框正常加载
- [x] 2.3 验证编辑品牌时可以正常选择采购人员