## Context

当前销售订单详情页面存在多个显示问题：

1. **新建订单数据不完整**：`SalesOrderCreate.vue` 的 `handleSaveOrder` 函数在提交订单时，只传递了 `product_code`、`spec_code`，未传递 `product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name` 等关键字段，导致后端存储的数据不完整

2. **后端数据返回**：`SalesOrderItem.to_dict()` 方法返回 `shipping_method.value`（英文枚举值 "direct"/"warehouse"），前端需要额外处理中文映射

3. **前端展示**：`SalesOrderDetail.vue` 商品明细表格缺少仓库列，且发货方式直接展示英文值

4. **冗余查询**：`handlePushPurchase` 函数中存在冗余的品牌信息查询逻辑，但由于新建订单时未存储品牌信息，导致需要额外查询

当前数据流：
- 前端 `SalesOrderCreate.vue` → 提交订单数据（缺少关键字段）
- 后端 `create_order` → 存储订单（字段为空或不完整）
- 后端 `get_order_by_no` → 返回订单详情（字段为空）
- 前端 `loadOrder` → 获取订单详情并展示（信息缺失）
- 前端 `handlePushPurchase` → 需要重新查询商品获取品牌信息

## Goals / Non-Goals

**Goals:**
- 新建订单时提交完整的商品信息（`product_id`、`product_name`、`brand_id`、`brand_name`、`spec_id`、`warehouse_name`）
- 后端返回中文发货方式，减少前端映射负担
- 前端正确展示商品品牌、仓库信息
- 直发时仓库信息显示为 "--"
- 移除冗余的品牌信息查询逻辑

**Non-Goals:**
- 不修改数据库结构或存储逻辑（Model 已有这些字段）
- 不修改订单创建/编辑流程的其他部分
- 不影响其他模块（采购单、收款单等）

## Decisions

### 1. 新建订单数据完整性

**决策**：修改 `SalesOrderCreate.vue` 的 `handleSaveOrder` 函数，提交完整的商品信息

**理由**：
- 后端 Model 已有这些字段，只是前端未提交
- 保证数据完整性，避免后续需要额外查询
- 提升页面加载性能

**修改内容**：
```javascript
items: orderForm.value.items.map(item => ({
  row_no: item.row_no,
  product_id: item.product_id,           // 新增
  product_code: item.product_code,
  product_name: item.product_name,       // 新增
  spec_id: item.spec_id,                 // 新增
  spec_code: item.spec_code,
  brand_id: item.brand_id,               // 新增
  brand_name: item.brand_name,           // 新增
  warehouse_id: item.warehouse_id,
  warehouse_name: item.warehouse_name,   // 新增
  qty: item.qty,
  price: item.price,
  discount: item.discount,
  shipping_method: item.shipping_method
}))
```

### 2. 发货方式中文映射位置

**决策**：在后端 `SalesOrderItem.to_dict()` 中返回中文值

**理由**：
- 后端统一处理，前端无需额外映射
- 与其他状态字段（如 `order_status`）的处理方式一致
- 减少前端代码复杂度

**备选方案**：
- 前端添加映射表：需要多处维护（详情页、下推选择弹窗等），容易遗漏

### 3. 仓库信息展示逻辑

**决策**：前端根据发货方式判断是否显示仓库信息

**理由**：
- 仓库信息在数据库中可能为空（直发时不需要仓库）
- 前端展示逻辑更灵活，可根据业务需求调整
- 不影响后端数据结构

### 4. 品牌信息处理

**决策**：移除前端冗余查询，直接使用后端返回的数据

**理由**：
- 后端 `get_order_by_no` 已返回 `brand_id` 和 `brand_name`
- 减少不必要的 API 调用
- 提升页面加载性能

## Risks / Trade-offs

- **后端返回值变更**：修改 `to_dict()` 方法会影响所有使用该数据的场景 → 确认所有场景都能接受中文值
- **前端判断逻辑**：依赖发货方式判断仓库显示，需确保发货方式值正确 → 后端返回中文值后判断更直观