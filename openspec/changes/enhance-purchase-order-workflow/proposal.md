## Why

当前采购单流程过于简单，仅有 `draft` → `audited` → `closed/cancelled` 三个状态，无法满足实际业务中对采购流程的精细化管理需求。具体问题包括：

1. 缺少采购审核环节，无法在审核时选择供应商
2. 无法记录物流信息和采购源订单ID
3. 状态流转不够细化，无法区分"准备采购"、"采购中"、"采购完成"等阶段
4. 缺少状态回退机制

## What Changes

### 状态流程重构

将采购单状态从 3 个扩展为 6 个：

- `pending_review` (待审核) - 新建采购单的默认状态
- `ready_purchase` (准备采购) - 审核通过后，可录入物流信息
- `purchasing` (采购中) - 已开始采购，可跟踪进度
- `completed` (采购完成) - 采购流程结束
- `closed` (已关闭) - 订单关闭
- `cancelled` (已取消) - 订单取消

### 新增功能

- **待审核状态**：可查看采购单详情、选择供应商、输入备注、执行审核通过/撤回操作
- **供应商筛选**：根据采购单品牌筛选有该品牌供应资格的供应商，优先供应商标注显示
- **准备采购状态**：可录入物流信息（物流公司、物流单号）、采购源订单ID
- **状态回退**：各状态支持回退到上一状态
- **撤回操作**：待审核状态可撤回，删除采购单并回退关联销售单状态

### **BREAKING** 变更

- `PurchaseStatus` 枚举值变更，现有数据需迁移
- API 接口调整，前端需适配新状态

## Capabilities

### New Capabilities

- `purchase-order-workflow`: 采购单完整工作流管理，包括状态流转、供应商选择、物流信息录入
- `purchase-supplier-matching`: 采购单供应商匹配功能，根据品牌筛选优先供应商

### Modified Capabilities

- `purchase-order-api`: 采购单 API 接口调整，适配新状态和新增操作端点

## Impact

### 后端影响

- `models_mysql/purchase_order.py` - 状态枚举调整、新增物流字段
- `services/purchase_order_service_mysql.py` - 新增状态操作方法
- `app/routers/purchase_order.py` - 新增 API 端点

### 前端影响

- 采购单详情页面重构
- 采购单列表状态筛选适配
- 新增供应商选择组件

### 数据库影响

- `purchase_orders` 表新增字段：`logistics_company`、`logistics_no`、`source_purchase_order_id`
- 现有数据状态值迁移
