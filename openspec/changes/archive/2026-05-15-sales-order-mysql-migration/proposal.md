## Why

销售订单管理系统当前使用 MongoDB 实现，需要迁移到 MySQL 以保持与其他已迁移模块（客户、库存、商品、认证）的一致性。同时完善订单状态流转逻辑（增加待审核状态）和下推采购功能（库存判断、采购单撤销），提升业务流程的完整性和可控性。

## What Changes

- **BREAKING**: 将销售订单和采购单从 MongoDB 迁移到 MySQL（Tortoise ORM）
- 新增订单"待审核"状态，完善状态流转：草稿 → 待审核 → 已审核
- 新增"提交并审核通过"快捷功能，创建订单时可直接跳到已审核状态
- 完善下推采购逻辑：仓库发货商品需判断库存是否充足，只下推库存不足部分
- 实现采购单撤销功能：撤销后删除采购单，回退销售订单状态和商品下推标记
- 订单详情接口增加商品库存信息展示

## Capabilities

### New Capabilities
- `sales-order-mysql`: 销售订单 MySQL 模型和服务层实现
- `purchase-order-mysql`: 采购单 MySQL 模型和服务层实现
- `order-status-flow-mysql`: 订单状态流转记录 MySQL 实现
- `order-approval`: 订单审核流程（待审核状态、审核通过、驳回）
- `purchase-order-recall`: 采购单撤销功能

### Modified Capabilities
- `sales-order-status`: 订单状态流转增加 pending 状态和驳回逻辑
- `sales-order-push-purchase`: 下推采购增加库存判断逻辑

## Impact

**受影响的文件：**
- `backend/models/sales_order.py` → 迁移到 `backend/models_mysql/sales_order.py`
- `backend/models/purchase_order.py` → 迁移到 `backend/models_mysql/purchase_order.py`
- `backend/services/sales_order_service.py` → 重写为 `backend/services/sales_order_service_mysql.py`
- `backend/services/purchase_order_service.py` → 重写为 `backend/services/purchase_order_service_mysql.py`
- `backend/services/order_status_flow_service.py` → 迁移到 MySQL
- `backend/app/routers/sales_order.py` - 更新路由使用新服务
- `backend/app/routers/purchase_order.py` - 更新路由使用新服务
- `backend/app/agent/tools/sales_order.py` - 更新 agent 工具
- `backend/app/agent/tools/inventory.py` - 更新 agent 工具

**数据库影响：**
- 新增 MySQL 表：sales_orders, sales_order_items, sales_deliver_infos, purchase_orders, purchase_order_items, order_status_flows
- MongoDB collections sales_orders, purchaseOrders, order_status_flows 将不再使用（不迁移历史数据）

**API 影响：**
- 新增接口：POST /sales-orders/{order_no}/submit（提交审核）
- 新增接口：POST /sales-orders/{order_no}/approve（审核通过）
- 新增接口：POST /sales-orders/{order_no}/reject（驳回）
- 新增接口：POST /sales-orders/create-and-approve（创建并审核通过）
- 新增接口：POST /purchase-orders/{purchase_no}/recall（撤销采购单）
- 修改接口：GET /sales-orders/{order_no} 返回商品库存信息