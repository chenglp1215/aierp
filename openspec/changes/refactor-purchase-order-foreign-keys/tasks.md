## 1. 准备工作

- [ ] 1.1 备份数据库：导出 purchase_orders、purchase_order_items 表结构和数据
- [ ] 1.2 确认 ProductSpec、Warehouse、Brand 模型已存在且可关联

## 2. 修改 PurchaseOrder 模型

- [ ] 2.1 在 PurchaseOrder 模型中添加 Brand 外键关联
- [ ] 2.2 更新 PurchaseOrder.to_dict() 方法，通过关联获取 brand_name
- [ ] 2.3 验证模型语法正确

## 3. 修改 PurchaseOrderItem 模型

- [ ] 3.1 添加 ProductSpec 外键关联（spec 字段）
- [ ] 3.2 添加 Warehouse 外键关联（warehouse 字段）
- [ ] 3.3 移除 brand_name、warehouse_name 冗余字段定义
- [ ] 3.4 更新 PurchaseOrderItem.to_dict() 方法，通过关联链获取名称
- [ ] 3.5 验证模型语法正确

## 4. 更新 Service 层

- [ ] 4.1 更新 get_order_by_no 方法，使用 prefetch_related 预加载关联数据
- [ ] 4.2 更新 create_from_sales_order 方法，移除冗余字段赋值
- [ ] 4.3 更新 list_orders 方法（如有需要）
- [ ] 4.4 验证服务层语法正确

## 5. 数据库迁移

- [ ] 5.1 创建迁移 SQL 脚本，删除冗余字段列
- [ ] 5.2 执行迁移脚本
- [ ] 5.3 验证表结构正确

## 6. 测试验证

- [ ] 6.1 启动后端服务
- [ ] 6.2 测试采购单创建功能
- [ ] 6.3 测试采购单查询功能（验证关联数据返回正确）
- [ ] 6.4 测试采购单列表功能
- [ ] 6.5 关闭后端服务

## 7. 提交变更

- [ ] 7.1 检查变更状态
- [ ] 7.2 提交代码变更