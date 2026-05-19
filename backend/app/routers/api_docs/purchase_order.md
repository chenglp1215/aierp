# 采购单管理 API

本文档描述采购单管理模块的所有 REST API 接口。

**模块路径**: `/api/v1/purchase-orders`

**权限要求**:
- `purchase.view`: 查看采购单
- `purchase.create`: 创建采购单
- `purchase.edit`: 编辑采购单
- `purchase.delete`: 删除采购单

---

## 状态流转

### 采购单状态流转图

```
pending_review (待审核)
      │
      ├── [审核通过] ──→ ready_purchase (准备采购)
      │                        │
      │                        ├── [开始采购] ──→ purchasing (采购中)
      │                        │                        │
      │                        │                        └── [采购完成] ──→ completed (采购完成)
      │                        │
      │                        └── [回退] ──→ pending_review
      │
      └── [撤回] ──→ 删除采购单，回退销售单状态
```

### 状态枚举 (purchase_status)

| 值 | 说明 | 可执行操作 |
|------|------|-----------|
| `pending_review` | 待审核 | 审核通过、撤回 |
| `ready_purchase` | 准备采购 | 开始采购、回退 |
| `purchasing` | 采购中 | 采购完成、回退 |
| `completed` | 采购完成 | - |
| `closed` | 已关闭 | - |
| `cancelled` | 已取消 | - |

### 入库状态 (in_status)

| 值 | 说明 |
|------|------|
| `none` | 未入库 |
| `partial` | 部分入库 |
| `full` | 全部入库 |

### 付款状态 (pay_status)

| 值 | 说明 |
|------|------|
| `none` | 未付款 |
| `partial` | 部分付款 |
| `full` | 全部结清 |

### 采购类型 (purchase_type)

| 值 | 说明 |
|------|------|
| `direct` | 直运采购 |
| `warehouse` | 仓库采购 |

---

## 数据模型

### 外键关联说明

采购单模块使用外键关联查询获取名称字段：

**PurchaseOrder（采购单主表）**：
- `brand_id` → 关联 Brand 表，获取 `brand_name`

**PurchaseOrderItem（采购单明细）**：
- `spec_id` → 关联 ProductSpec 表，获取 `spec_code`
- ProductSpec → 关联 Product 表，获取 `product_id`、`product_code`、`product_name`
- Product → 关联 Brand 表，获取 `brand_id`、`brand_name`
- `warehouse_id` → 关联 Warehouse 表，获取 `warehouse_name`

### 采购单完整模型（响应示例）

```json
{
  "id": 1,
  "purchase_no": "PO202605150001",
  "purchase_type": "direct",
  "source_sale_order_id": 1,
  "source_sale_order_no": "SO202605150001",
  "brand_id": 1,
  "brand_name": "品牌名称",
  "supplier_id": 1,
  "supplier_name": "供应商名称",
  "purchase_user_id": 1,
  "expect_arrive_date": "2026-05-20",
  "settle_type": "月结",
  "total_amt": 8000.00,
  "freight_amt": 100.00,
  "tax_rate": 0.13,
  "tax_amt": 1040.00,
  "total_tax_amt": 9140.00,
  "purchase_status": "pending_review",
  "in_status": "none",
  "pay_status": "none",
  "logistics_company": "顺丰速运",
  "logistics_no": "SF1234567890",
  "source_purchase_order_id": "1688-ORDER-001",
  "creator_id": 1,
  "created_at": "2026-05-15T15:00:00",
  "updated_at": "2026-05-15T15:00:00",
  "remark": "由销售单下推生成",
  "items": [
    {
      "id": 1,
      "purchase_order_id": 1,
      "row_no": 1,
      "product_id": 1,
      "product_code": "PROD001",
      "product_name": "商品名称",
      "spec_id": 1,
      "spec_code": "SPEC001",
      "brand_id": 1,
      "brand_name": "品牌名称",
      "warehouse_id": 1,
      "warehouse_name": "仓库名称",
      "purchase_qty": 2,
      "purchase_price": 4000.00,
      "discount": 1.0,
      "amt": 8000.00,
      "in_qty": 0,
      "return_qty": 0,
      "source_sale_row_no": 1,
      "shipping_method": "直运"
    }
  ]
}
```

---

## API 接口

### 1. 获取采购单列表

**GET** `/api/v1/purchase-orders/`

**权限**: `purchase.view`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码（默认：1） |
| page_size | int | 否 | 每页数量（默认：20，最大：100） |
| purchase_status | string | 否 | 采购状态 |
| brand_id | int | 否 | 品牌ID |
| source_sale_order_no | string | 否 | 源销售订单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 10,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "purchase_no": "PO202605150001",
        "purchase_type": "direct",
        "purchase_status": "pending_review",
        "brand_id": 1,
        "brand_name": "品牌名称",
        "supplier_id": 1,
        "supplier_name": "供应商名称",
        "total_amt": 8000.00,
        "total_tax_amt": 9140.00,
        "created_at": "2026-05-15T15:00:00"
      }
    ]
  }
}
```

---

### 2. 获取采购单详情

**GET** `/api/v1/purchase-orders/{purchase_no}`

**权限**: `purchase.view`

#### 响应示例

返回完整采购单信息，包括：
- 基本信息
- 商品明细列表
- 关联销售单简要信息（`source_sales_order`）

---

### 3. 获取可选供应商列表

**GET** `/api/v1/purchase-orders/{purchase_no}/available-suppliers`

**权限**: `purchase.view`

根据采购单品牌筛选有供应资格的供应商，优先供应商排在前面。

#### 响应示例

```json
{
  "status": "success",
  "message": "操作成功",
  "result": [
    {
      "id": 1,
      "name": "供应商A",
      "contact_person": "张三",
      "contact_phone": "13800138000",
      "discount": 0.95,
      "is_priority": true
    }
  ]
}
```

---

### 4. 选择/修改供应商

**PUT** `/api/v1/purchase-orders/{purchase_no}/supplier`

**权限**: `purchase.edit`

#### 请求体

```json
{
  "supplier_id": 1
}
```

**状态限制**: 仅 `pending_review` 或 `ready_purchase` 状态可修改。

---

### 5. 更新物流信息

**PUT** `/api/v1/purchase-orders/{purchase_no}/logistics`

**权限**: `purchase.edit`

#### 请求体

```json
{
  "logistics_company": "顺丰速运",
  "logistics_no": "SF1234567890",
  "source_purchase_order_id": "1688-ORDER-001",
  "expect_arrive_date": "2026-05-20"
}
```

**状态限制**: 仅 `pending_review` 或 `ready_purchase` 状态可修改。

---

### 6. 审核通过

**POST** `/api/v1/purchase-orders/{purchase_no}/approve`

**权限**: `purchase.edit`

将采购单从 `pending_review` 状态变更为 `ready_purchase` 状态。

**状态限制**: 仅 `pending_review` 状态可操作。

---

### 7. 开始采购

**POST** `/api/v1/purchase-orders/{purchase_no}/start-purchase`

**权限**: `purchase.edit`

将采购单从 `ready_purchase` 状态变更为 `purchasing` 状态。

**状态限制**: 仅 `ready_purchase` 状态可操作。

---

### 8. 采购完成

**POST** `/api/v1/purchase-orders/{purchase_no}/complete`

**权限**: `purchase.edit`

将采购单从 `purchasing` 状态变更为 `completed` 状态。

**状态限制**: 仅 `purchasing` 状态可操作。

---

### 9. 状态回退

**POST** `/api/v1/purchase-orders/{purchase_no}/rollback`

**权限**: `purchase.edit`

将采购单状态回退到上一状态：
- `ready_purchase` → `pending_review`（清空物流信息和供应商信息）
- `purchasing` → `ready_purchase`

**状态限制**: `completed` 状态不可回退。

---

### 10. 撤回采购单

**POST** `/api/v1/purchase-orders/{purchase_no}/recall`

**权限**: `purchase.edit`

删除采购单，并回退关联销售单的状态。

**状态限制**: 仅 `pending_review` 状态可操作。

---

### 11. 获取状态流转记录

**GET** `/api/v1/purchase-orders/{purchase_no}/status-flows`

**权限**: `purchase.view`

#### 响应示例

```json
{
  "status": "success",
  "message": "操作成功",
  "result": [
    {
      "id": 1,
      "order_no": "PO202605150001",
      "field": "purchase_status",
      "old_value": null,
      "new_value": "pending_review",
      "operator": "admin",
      "operate_time": "2026-05-15T15:00:00",
      "remark": "从销售订单下推创建"
    }
  ]
}
```

---

## 错误响应示例

### 业务错误

```json
{
  "status": "error",
  "message": "只有待审核状态的采购单可以审核",
  "result": null
}
```

### 参数校验错误

```json
{
  "status": "error",
  "message": "参数验证失败",
  "result": null,
  "validation_errors": [
    {"field": "supplier_id", "message": "supplier_id为必填"}
  ]
}
```