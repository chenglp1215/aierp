## 1. 数据模型创建

- [x] 1.1 创建 `backend/models_mysql/customer.py`，定义 Customer 模型
- [x] 1.2 定义 InvoiceInfo 模型（外键关联 Customer）
- [x] 1.3 定义 ShippingAddress 模型（外键关联 Customer）
- [x] 1.4 定义 CustomerDiscount 模型（外键关联 Customer）
- [x] 1.5 为每个模型实现 `to_dict()` 方法
- [x] 1.6 在 `backend/models_mysql/__init__.py` 中注册新模型

## 2. 服务层实现

- [x] 2.1 创建 `backend/services/customer_service_mysql.py`
- [x] 2.2 实现 CustomerService 类（CRUD、列表、统计、状态更新、转移）
- [x] 2.3 实现 InvoiceInfoService 类（增删改、设置默认）
- [x] 2.4 实现 ShippingAddressService 类（增删改、设置默认）
- [x] 2.5 实现 CustomerDiscountService 类（CRUD、查询、状态切换）
- [x] 2.6 创建服务实例导出

## 3. 路由层适配

- [x] 3.1 修改 `backend/app/routers/customer.py`，导入 MySQL 服务层
- [x] 3.2 更新客户 CRUD 接口使用 MySQL 服务
- [x] 3.3 更新客户折扣接口使用 MySQL 服务
- [x] 3.4 验证所有接口返回格式与原实现一致

## 4. API 文档更新

- [x] 4.1 检查 `backend/app/routers/api_docs/customer.md` 是否需要更新
- [x] 4.2 更新接口响应示例中的 id 字段类型（字符串 → 整数）

## 5. 数据迁移脚本

- [ ] 5.1 创建 `backend/scripts/migrate_customer_to_mysql.py`
- [ ] 5.2 实现客户数据迁移（MongoDB → MySQL）
- [ ] 5.3 实现开票信息迁移
- [ ] 5.4 实现收货地址迁移
- [ ] 5.5 实现客户折扣迁移
- [ ] 5.6 实现 ID 映射表（旧 ID → 新 ID）
- [ ] 5.7 更新关联表的 customer_id（sales_orders, accounts_receivable 等）

## 6. 测试验证

- [x] 6.1 启动后端服务，验证数据库表创建成功
- [ ] 6.2 测试客户 CRUD 接口
- [ ] 6.3 测试开票信息管理接口
- [ ] 6.4 测试收货地址管理接口
- [ ] 6.5 测试客户折扣接口
- [ ] 6.6 验证前端客户管理功能正常
- [ ] 6.7 验证前端销售订单创建时客户选择正常