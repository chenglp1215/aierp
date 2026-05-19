## 1. 数据库模型

- [ ] 1.1 在 `models_mysql/sales_order.py` 新增枚举 `CostType`（purchase/freight/transfer/other）
- [ ] 1.2 在 `models_mysql/sales_order.py` 新增枚举 `CostSourceType`（purchase_order/manual）
- [ ] 1.3 在 `models_mysql/sales_order.py` 新增枚举 `FinanceStatus`（unpaid/partial_paid/paid/reconciled）
- [ ] 1.4 在 `models_mysql/sales_order.py` 新增 `SalesOrderCostItem` 模型
- [ ] 1.5 在 `SalesOrder` 模型新增 `finance_status` 字段
- [ ] 1.6 在 `SalesOrderItem` 模型新增 `exchange_qty` 和 `supplement_qty` 字段
- [ ] 1.7 更新 `SalesOrder.to_dict()` 方法返回 `finance_status`
- [ ] 1.8 更新 `SalesOrderItem.to_dict()` 方法返回 `exchange_qty` 和 `supplement_qty`

## 2. 数据库迁移

- [ ] 2.1 创建迁移脚本 `scripts/migrate_sales_order_cost_fields.py`
- [ ] 2.2 迁移脚本创建 `sales_order_cost_items` 表
- [ ] 2.3 迁移脚本为 `sales_orders` 表新增 `finance_status` 字段（默认 unpaid）
- [ ] 2.4 迁移脚本为 `sales_order_items` 表新增 `exchange_qty` 和 `supplement_qty` 字段（默认 0）
- [ ] 2.5 执行迁移脚本验证数据库变更

## 3. 销售单服务层增强

- [ ] 3.1 在 `sales_order_service_mysql.py` 新增成本明细计算方法 `_calculate_cost_amt`
- [ ] 3.2 在 `sales_order_service_mysql.py` 新增利润计算方法 `_calculate_profit_amt`
- [ ] 3.3 修改 `list_orders` 方法返回 `cost_amt` 和 `profit_amt`
- [ ] 3.4 修改 `list_orders` 方法返回商品明细 `items`（用于展开）
- [ ] 3.5 修改 `get_order_by_no` 方法返回 `finance_status`
- [ ] 3.6 新增成本明细 CRUD 方法：`create_cost_item`, `list_cost_items`, `delete_cost_item`
- [ ] 3.7 新增财务状态更新方法：`update_finance_status`

## 4. 采购单服务层触发

- [ ] 4.1 在 `purchase_order_service_mysql.py` 新增付款完成方法 `complete_payment`
- [ ] 4.2 付款完成方法调用销售单服务创建成本明细
- [ ] 4.3 创建成本明细前检查是否已存在（防重复）
- [ ] 4.4 成本明细关联采购单 ID 和采购单号

## 5. API 路由

- [ ] 5.1 在 `sales_order.py` 路由新增成本明细子路由
- [ ] 5.2 实现 GET `/sales-orders/{order_no}/cost-items` 获取成本明细列表
- [ ] 5.3 实现 POST `/sales-orders/{order_no}/cost-items` 手动添加成本明细
- [ ] 5.4 实现 DELETE `/sales-orders/{order_no}/cost-items/{id}` 删除成本明细（仅 manual 类型）
- [ ] 5.5 实现 PUT `/sales-orders/{order_no}/finance-status` 更新财务状态
- [ ] 5.6 在 `purchase_order.py` 路由新增 POST `/purchase-orders/{purchase_no}/complete-payment` 付款完成接口

## 6. 前端 API 服务

- [ ] 6.1 在 `api.ts` 新增 `salesOrderApi.getCostItems(orderNo)` 方法
- [ ] 6.2 在 `api.ts` 新增 `salesOrderApi.createCostItem(orderNo, data)` 方法
- [ ] 6.3 在 `api.ts` 新增 `salesOrderApi.deleteCostItem(orderNo, id)` 方法
- [ ] 6.4 在 `api.ts` 新增 `salesOrderApi.updateFinanceStatus(orderNo, status)` 方法
- [ ] 6.5 在 `api.ts` 新增 `purchaseOrderApi.completePayment(purchaseNo)` 方法

## 7. 前端列表组件改造

- [ ] 7.1 修改 `SalesOrderList.vue` 表头列配置（新增成本、利润、财务状态列）
- [ ] 7.2 修改表格数据渲染，显示新列数据
- [ ] 7.3 新增展开/收起按钮列
- [ ] 7.4 实现展开行状态管理（expandedRows 数组）
- [ ] 7.5 实现展开行子表格渲染（商品明细）
- [ ] 7.6 子表格列配置：品牌名、规格编号、产品名称、规格、包装单位、数量、原价、退/换/补货数量、含税单价、合计
- [ ] 7.7 实现含税单价前端计算（price * (1 + tax_rate)）
- [ ] 7.8 新增选中列（复选框）
- [ ] 7.9 实现选中状态管理（selectedOrders 数组）
- [ ] 7.10 实现全选/取消全选功能
- [ ] 7.11 新增批量操作按钮（批量提交审核）
- [ ] 7.12 实现批量操作逻辑

## 8. 验证测试

- [ ] 8.1 验证数据库迁移成功，新字段存在
- [ ] 8.2 验证销售单列表接口返回 cost_amt、profit_amt、items
- [ ] 8.3 验证成本明细 CRUD API 功能正常
- [ ] 8.4 验证采购单付款完成自动创建成本明细
- [ ] 8.5 验证前端列表显示新列数据
- [ ] 8.6 验证前端展开行功能正常
- [ ] 8.7 验证前端选中功能正常
- [ ] 8.8 验证含税单价计算正确