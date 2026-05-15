## 1. MySQL 模型创建

- [ ] 1.1 创建 models_mysql/sales_order.py：SalesOrder、SalesOrderItem、SalesDeliverInfo 模型
- [ ] 1.2 创建 models_mysql/purchase_order.py：PurchaseOrder、PurchaseOrderItem 模型
- [ ] 1.3 创建 models_mysql/order_status_flow.py：OrderStatusFlow 模型
- [ ] 1.4 在 models_mysql/__init__.py 中注册新模型
- [ ] 1.5 在 backend/app/database.py 中注册新模型到 Tortoise ORM
- [ ] 1.6 生成数据库迁移文件

## 2. 销售订单服务层迁移

- [ ] 2.1 创建 services/sales_order_service_mysql.py：基础 CRUD 操作
- [ ] 2.2 实现订单号生成逻辑（SO + 日期 + 序列号）
- [ ] 2.3 实现订单金额计算逻辑
- [ ] 2.4 实现商品信息富化（从 product_service 获取商品名称、品牌等）
- [ ] 2.5 实现订单列表查询（分页、过滤、排序）
- [ ] 2.6 实现订单详情查询（包含明细和发货信息）

## 3. 订单状态流转实现

- [ ] 3.1 更新 OrderStatus 枚举，增加 PENDING 状态
- [ ] 3.2 实现状态转换验证逻辑 _can_transition_status
- [ ] 3.3 实现提交审核接口：POST /sales-orders/{order_no}/submit
- [ ] 3.4 实现审核通过接口：POST /sales-orders/{order_no}/approve
- [ ] 3.5 实现驳回接口：POST /sales-orders/{order_no}/reject
- [ ] 3.6 实现"创建并审核通过"功能：create_sales_order(submit=True)
- [ ] 3.7 创建 services/order_status_flow_service_mysql.py

## 4. 下推采购完善

- [ ] 4.1 实现库存查询：订单详情接口增加商品库存信息
- [ ] 4.2 实现库存不足判断逻辑（库存 < 订单数量 或 库存 ≤ min_stock）
- [ ] 4.3 修改下推采购逻辑：仓库发货商品只下推库存不足的
- [ ] 4.4 实现部分下推状态更新（partially_pushed_to_purchase）
- [ ] 4.5 实现全部下推状态更新（pushed_to_purchase）

## 5. 采购单服务层迁移

- [ ] 5.1 创建 services/purchase_order_service_mysql.py：基础 CRUD 操作
- [ ] 5.2 实现采购单号生成逻辑（PO + 日期 + 随机数）
- [ ] 5.3 实现从销售单生成采购单：generate_from_selected_items
- [ ] 5.4 实现自动选择供应商逻辑
- [ ] 5.5 实现采购单审核/结案/作废等状态操作

## 6. 采购单撤销功能

- [ ] 6.1 实现采购单撤销接口：POST /purchase-orders/{purchase_no}/recall
- [ ] 6.2 实现销售订单状态回退逻辑
- [ ] 6.3 实现销售订单商品 pushed 标志重置
- [ ] 6.4 记录状态流转日志

## 7. 路由层更新

- [ ] 7.1 更新 app/routers/sales_order.py 使用新服务
- [ ] 7.2 更新 app/routers/purchase_order.py 使用新服务
- [ ] 7.3 新增订单审核相关路由
- [ ] 7.4 新增采购单撤销路由

## 8. Agent 工具更新

- [ ] 8.1 更新 app/agent/tools/sales_order.py 使用新服务
- [ ] 8.2 更新 app/agent/tools/inventory.py 使用新服务

## 9. 清理和测试

- [ ] 9.1 更新 services/__init__.py 导出新服务
- [ ] 9.2 删除旧的 MongoDB 模型文件（models/sales_order.py、models/purchase_order.py）
- [ ] 9.3 删除旧的 MongoDB 服务文件（保留作为参考，添加 _deprecated 后缀）
- [ ] 9.4 测试订单创建、审核、下推采购、采购单撤销完整流程