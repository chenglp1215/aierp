# 更新采购单 API 文档实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 更新采购单 API 文档以反映外键关联重构后的数据结构变化

**Architecture:** 文档更新，移除冗余字段作为传入参数，添加外键关联说明，保持响应格式兼容

**Tech Stack:** Markdown 文档

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/routers/api_docs/purchase_order.md` | 修改 | 采购单 API 文档 |
| `.project_docs/backend/项目模块说明.md` | 修改 | 项目模块说明（采购单部分） |

---

## 1. 更新采购单创建模型

### Task 1: 更新创建请求参数说明

**Files:**
- Modify: `backend/app/routers/api_docs/purchase_order.md`

- [ ] **Step 1: 更新采购单创建模型示例**

将创建模型示例中的 `brand_name` 移除，更新为：

```json
{
  "purchase_type": "direct",
  "source_sale_order_no": "SO202501010001",
  "source_sale_order_id": 1,
  "brand_id": 1,
  "supplier_id": 1,
  "purchase_user_id": 1,
  "expect_arrive_date": "2025-04-30",
  "settle_type": "月结",
  "remark": "由销售单自动生成-直运采购",
  "items": [
    {
      "row_no": 1,
      "spec_id": 1,
      "product_id": 1,
      "brand_id": 1,
      "warehouse_id": 1,
      "purchase_qty": 2,
      "purchase_price": 4000,
      "discount": 1.0,
      "amt": 8000,
      "shipping_method": "直运",
      "source_sale_row_no": 1
    }
  ]
}
```

- [ ] **Step 2: 更新字段说明表格**

更新明细字段说明：

| 字段 | 类型 | 说明 |
|------|------|------|
| spec_id | int | 规格ID（外键关联 ProductSpec） |
| warehouse_id | int | 仓库ID（外键关联 Warehouse） |
| product_id | int | 商品ID（可选，通过 spec 关联获取） |
| brand_id | int | 品牌ID（可选，通过 spec 关联获取） |

注意：`brand_name`、`warehouse_name` 不再作为传入参数，通过外键关联查询获取。

---

## 2. 更新响应数据结构说明

### Task 2: 添加外键关联说明

**Files:**
- Modify: `backend/app/routers/api_docs/purchase_order.md`

- [ ] **Step 1: 在数据模型部分添加外键关联说明**

在"数据模型"部分添加：

```markdown
### 外键关联说明

采购单明细通过外键关联获取名称字段：

- `spec_id` → 关联 ProductSpec 表，获取 `spec_code`
- ProductSpec → 关联 Product 表，获取 `product_id`、`product_code`、`product_name`
- Product → 关联 Brand 表，获取 `brand_id`、`brand_name`
- `warehouse_id` → 关联 Warehouse 表，获取 `warehouse_name`

**注意：** 创建时只需传入外键 ID，名称字段由系统通过关联查询自动填充。
```

- [ ] **Step 2: 更新完整模型示例**

更新采购单完整模型示例，添加字段来源注释：

```json
{
  "id": 1,
  "purchase_no": "PO202504200001",
  "purchase_type": "direct",
  "brand_id": 1,
  "brand_name": "品牌名称（通过 brand_id 关联查询）",
  "supplier_id": 1,
  "supplier_name": "供应商名称（快照）",
  "items": [
    {
      "row_no": 1,
      "spec_id": 1,
      "spec_code": "SPEC001（通过 spec_id 关联查询）",
      "product_id": 1,
      "product_code": "PROD001（通过 spec 关联查询）",
      "product_name": "商品名称（通过 spec 关联查询）",
      "brand_id": 1,
      "brand_name": "品牌名称（通过 spec→product→brand 关联查询）",
      "warehouse_id": 1,
      "warehouse_name": "仓库名称（通过 warehouse_id 关联查询）",
      "purchase_qty": 2,
      "purchase_price": 4000,
      "discount": 1.0,
      "amt": 8000
    }
  ]
}
```

---

## 3. 更新项目模块说明

### Task 3: 更新项目模块说明文档

**Files:**
- Modify: `.project_docs/backend/项目模块说明.md`

- [ ] **Step 1: 更新采购单模块说明**

将采购单模块说明更新为：

```markdown
### 9. 采购单

**功能**：采购单创建、编辑、状态流转

**核心文件**：
- `routers/purchase_order.py` — 路由
- `services/purchase_order_service_mysql.py` — 业务服务（MySQL 版本）
- `models_mysql/purchase_order.py` — 数据模型（Tortoise ORM）

**数据模型**：
- `PurchaseOrder` — 采购单主表（purchase_orders）
  - 外键关联：`brand` → Brand 表
- `PurchaseOrderItem` — 采购单明细（purchase_order_items）
  - 外键关联：`spec` → ProductSpec 表，`warehouse` → Warehouse 表
  - 名称字段通过关联链查询：spec → product → brand

**API 文档**：`app/routers/api_docs/purchase_order.md`
```

---

## 4. 提交变更

### Task 4: 提交文档更新

**Files:**
- 无新文件

- [ ] **Step 1: 检查变更状态**

Run: `git status`
Expected: 显示修改的文档文件

- [ ] **Step 2: 提交变更**

```bash
git add backend/app/routers/api_docs/purchase_order.md .project_docs/backend/项目模块说明.md openspec/changes/update-purchase-order-api-docs/
git commit -m "docs: 更新采购单 API 文档以反映外键关联重构

- 移除 brand_name、warehouse_name 作为传入参数
- 添加外键关联说明（spec → product → brand）
- 更新响应字段来源说明
- 更新项目模块说明中的采购单部分"
```

---

## 自检清单

**1. Spec 覆盖检查：**
- [x] 采购单创建请求参数更新 → Task 1
- [x] 采购单明细数据结构说明 → Task 2
- [x] 响应格式兼容说明 → Task 2

**2. 占位符检查：**
- 无 TBD、TODO 等占位符
- 所有代码示例包含完整内容

**3. 文档一致性检查：**
- API 文档与模型定义一致
- 项目模块说明与 API 文档一致