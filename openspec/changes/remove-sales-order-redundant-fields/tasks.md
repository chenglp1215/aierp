## 1. 准备工作

- [ ] 1.1 备份生产数据库
- [ ] 1.2 创建数据库迁移脚本目录
- [ ] 1.3 编写单元测试框架

## 2. SalesOrder 模块重构

- [ ] 2.1 修改 SalesOrderItem 模型，添加 ForeignKeyField 关联 Brand、Warehouse、Product、ProductSpec
- [ ] 2.2 移除 SalesOrderItem 中的冗余字段（brand_name、warehouse_name、product_name、product_code、spec_code）
- [ ] 2.3 修改 SalesOrder 模型，添加 ForeignKeyField 关联 Customer、User（sale_user、creator）
- [ ] 2.4 更新 SalesOrderItem.to_dict() 方法，通过关联查询返回名称
- [ ] 2.5 更新 SalesOrder.to_dict() 方法，通过关联查询返回名称
- [ ] 2.6 更新 sales_order_service_mysql.py，使用 prefetch_related 查询
- [ ] 2.7 更新创建订单逻辑，移除冗余字段处理
- [ ] 2.8 执行数据库迁移，删除冗余字段，添加外键约束
- [ ] 2.9 运行 API 测试验证

## 3. PurchaseOrder 模块重构

- [ ] 3.1 修改 PurchaseOrderItem 模型，添加 ForeignKeyField 关联 Brand、Warehouse
- [ ] 3.2 移除 PurchaseOrderItem 中的冗余字段（brand_name、warehouse_name）
- [ ] 3.3 修改 PurchaseOrder 模型，添加 ForeignKeyField 关联 Brand、Supplier
- [ ] 3.4 更新 to_dict() 方法
- [ ] 3.5 更新 Service 层查询逻辑
- [ ] 3.6 执行数据库迁移
- [ ] 3.7 运行测试验证

## 4. Customer 模块重构

- [ ] 4.1 修改 Customer 模型，添加 ForeignKeyField 关联 User（sales_user）
- [ ] 4.2 移除 sales_user_name 冗余字段
- [ ] 4.3 修改 CustomerDiscount 模型，添加 ForeignKeyField 关联 Brand
- [ ] 4.4 移除 brand_name 冗余字段
- [ ] 4.5 更新 to_dict() 方法
- [ ] 4.6 执行数据库迁移
- [ ] 4.7 运行测试验证

## 5. Inventory 模块重构

- [ ] 5.1 修改 Stock 模型，添加 ForeignKeyField 关联 Product、ProductSpec
- [ ] 5.2 移除冗余字段（product_code、product_name、spec_code）
- [ ] 5.3 修改 InboundBatch、OutboundBatch 模型
- [ ] 5.4 添加 ForeignKeyField 关联 User
- [ ] 5.5 更新 to_dict() 方法
- [ ] 5.6 执行数据库迁移
- [ ] 5.7 运行测试验证

## 6. Brand/Warehouse 模块重构

- [ ] 6.1 修改 Brand 模型，添加 ForeignKeyField 关联 User（purchaser）
- [ ] 6.2 移除 purchaser_name 冗余字段
- [ ] 6.3 修改 Warehouse 模型，添加 ForeignKeyField 关联 User（manager）
- [ ] 6.4 移除 manager_name 冗余字段
- [ ] 6.5 更新 to_dict() 方法
- [ ] 6.6 执行数据库迁移
- [ ] 6.7 运行测试验证

## 7. 文档更新

- [ ] 7.1 更新 API 文档，说明请求格式变更
- [ ] 7.2 更新项目模块说明文档
- [ ] 7.3 编写迁移指南
