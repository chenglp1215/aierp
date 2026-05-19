## Context

当前采购单流程仅有 3 个状态（draft → audited → closed/cancelled），无法满足业务精细化管理需求。本次变更将扩展为 6 个状态，并新增供应商选择、物流信息录入、状态回退等功能。

### 现有约束

- 采购单通过销售单下推创建，按品牌分组
- SupplierBrand 表已有 `is_priority` 字段标识优先供应商
- 采购单与销售单明细通过 `source_sale_row_no` 关联

## Goals / Non-Goals

**Goals:**

- 扩展采购单状态为 6 个阶段，支持精细化流程管理
- 实现供应商智能筛选，根据品牌匹配并标注优先供应商
- 支持物流信息和采购源订单录入
- 实现灵活的状态回退机制
- 撤回操作时正确回退销售单状态

**Non-Goals:**

- 不涉及采购入库流程（已有 in_status 字段）
- 不涉及付款流程（已有 pay_status 字段）
- 不涉及价格计算逻辑调整

## Decisions

### 1. 状态流转设计

采用有限状态机模式，定义清晰的状态转换规则：

```
pending_review ──[审核通过]──→ ready_purchase ──[开始采购]──→ purchasing ──[采购完成]──→ completed
      ↑                            ↑                    │
      └────[回退]──────────────────┴──────[回退]────────┘
      │
      └──[撤回]──→ 删除采购单，回退销售单状态
```

**状态定义：**

| 状态 | 说明 | 可执行操作 |
|------|------|-----------|
| `pending_review` | 待审核 | 审核通过、撤回 |
| `ready_purchase` | 准备采购 | 开始采购、回退到待审核 |
| `purchasing` | 采购中 | 采购完成、回退到准备采购 |
| `completed` | 采购完成 | - |
| `closed` | 已关闭 | - |
| `cancelled` | 已取消 | - |

**理由：** 采购完成作为终态，不支持回退，符合业务实际（采购完成后货物已入库，需要走退货流程）。

### 2. 供应商选择时机

采用灵活选择策略：
- 待审核状态：可选择/修改供应商
- 准备采购状态：可选择/修改供应商
- 开始采购后：不可修改供应商

**理由：** 业务实际中，审核通过后可能需要调整供应商，保持灵活性。

### 3. 销售单状态回退逻辑

撤回采购单时，根据销售单商品的下推状态动态计算销售单状态：

```python
def calculate_sales_order_status(sales_order):
    all_items = sales_order.items
    pushed_items = [item for item in all_items if item.pushed]

    if len(pushed_items) == 0:
        return OrderStatus.AUDITED  # 全部未下推
    elif len(pushed_items) < len(all_items):
        return OrderStatus.PARTIALLY_PUSHED_TO_PURCHASE  # 部分下推
    else:
        return OrderStatus.PUSHED_TO_PURCHASE  # 全部已下推
```

**理由：** 销售单状态应真实反映其商品的下推情况，而非简单回退。

### 4. 数据模型变更

新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `logistics_company` | VARCHAR(100) | 物流公司 |
| `logistics_no` | VARCHAR(100) | 物流单号 |
| `source_purchase_order_id` | VARCHAR(100) | 采购源订单ID |

**理由：** 这些信息在准备采购阶段录入，用于跟踪采购进度。

## Risks / Trade-offs

### 风险1：现有数据迁移

**风险：** 现有采购单状态需要迁移到新状态值。

**缓解措施：**
- `draft` → `pending_review`
- `audited` → `ready_purchase` 或根据实际情况判断
- 编写迁移脚本，在部署前执行

### 风险2：前端兼容性

**风险：** 状态变更导致前端显示异常。

**缓解措施：**
- 后端提供状态中文映射 API
- 前端使用状态码而非状态名判断逻辑

### 风险3：并发操作

**风险：** 多人同时操作同一采购单可能导致状态不一致。

**缓解措施：**
- 使用数据库乐观锁（version 字段）
- 状态操作前检查当前状态

## Migration Plan

1. **备份数据库** - 备份 `purchase_orders` 表
2. **执行迁移脚本** - 更新状态值
3. **部署后端** - 新版本 API
4. **部署前端** - 适配新状态
5. **验证** - 检查现有采购单状态正确性

**回滚策略：**
- 恢复数据库备份
- 回滚前后端代码版本
