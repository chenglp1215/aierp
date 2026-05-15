# 采购单管理 API

本文档描述采购单管理模块的所有 REST API 接口。

**模块路径**: `/api/v1/purchase-orders`

**权限要求**:
- `purchase.view`: 查看采购单
- `purchase.create`: 创建采购单
- `purchase.edit`: 编辑采购单
- `purchase.delete`: 删除采购单

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

**注意：** 创建时只需传入外键 ID（`spec_id`、`warehouse_id`），名称字段由系统通过关联查询自动填充。

---

### 采购单创建模型

创建采购单时只需要提供以下字段，其他字段由系统自动生成：

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
  "freight_amt": 100.00,
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

### 字段说明

#### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| purchase_type | string | 采购类型：direct=直运采购 / warehouse=仓库采购 |
| settle_type | string | 结算方式：月结/货到付款/款到发货 |
| items | array | 商品明细 |

#### 明细字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| row_no | int | 是 | 行号 |
| spec_id | int | 是 | 规格ID（外键关联 ProductSpec） |
| warehouse_id | int | 是 | 仓库ID（外键关联 Warehouse） |
| product_id | int | 否 | 商品ID（可选，通过 spec 关联获取） |
| brand_id | int | 否 | 品牌ID（可选，通过 spec 关联获取） |
| purchase_qty | int | 是 | 采购数量 |
| purchase_price | float | 是 | 采购单价 |
| discount | float | 否 | 折扣系数（默认 1.0） |
| amt | float | 否 | 行金额（自动计算） |
| shipping_method | string | 否 | 发货方式 |
| source_sale_row_no | int | 否 | 关联源销售单明细行号 |

**注意：** `brand_name`、`warehouse_name` 不再作为传入参数，通过外键关联查询自动获取。

#### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| supplier_id | int | 供应商ID |
| source_sale_order_no | string | 关联源销售订单号 |
| source_sale_order_id | int | 关联源销售订单主键ID |
| brand_id | int | 品牌ID |
| purchase_user_id | int | 采购员用户ID |
| expect_arrive_date | string | 预计到货日期（YYYY-MM-DD） |
| freight_amt | float | 运费总金额（默认0） |
| remark | string | 备注 |

#### 系统自动计算字段（不需要传入）

| 字段 | 类型 | 说明 |
|------|------|------|
| purchase_no | string | 采购单号（系统生成） |
| total_amt | float | 物料不含税总金额（根据商品明细自动计算） |
| tax_rate | float | 税率（默认 0.13） |
| tax_amt | float | 税额（自动计算） |
| total_tax_amt | float | 含税总金额（自动计算） |
| purchase_status | string | 采购状态（默认 draft） |
| in_status | string | 入库状态（默认 none） |
| pay_status | string | 付款状态（默认 none） |
| creator_id | int | 创建人ID |
| created_at | datetime | 创建时间 |

### 采购单完整模型（响应示例）

```json
{
  "id": 1,
  "purchase_no": "PO202504200001",
  "purchase_type": "direct",
  "source_sale_order_id": 1,
  "source_sale_order_no": "SO202501010001",
  "brand_id": 1,
  "brand_name": "品牌名称",
  "supplier_id": 1,
  "supplier_name": "供应商名称（快照）",
  "purchase_user_id": 1,
  "expect_arrive_date": "2025-04-30",
  "settle_type": "月结",
  "total_amt": 8000.00,
  "freight_amt": 100.00,
  "tax_rate": 0.13,
  "tax_amt": 1040.00,
  "total_tax_amt": 9140.00,
  "purchase_status": "audited",
  "in_status": "none",
  "pay_status": "none",
  "creator_id": 1,
  "created_at": "2025-04-20T15:00:00",
  "updated_at": "2025-04-20T15:00:00",
  "remark": "由销售单SO202501010001自动生成-直运采购",
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
      "shipping_method": "直运",
      "created_at": "2025-04-20T15:00:00",
      "updated_at": "2025-04-20T15:00:00"
    }
  ]
}
```

**字段来源说明：**
- `brand_name`：通过 `brand_id` 外键关联 Brand 表查询获取
- `product_name`、`product_code`：通过 `spec_id` → ProductSpec → Product 关联查询获取
- `brand_name`（明细）：通过 `spec_id` → ProductSpec → Product → Brand 关联查询获取
- `warehouse_name`：通过 `warehouse_id` 外键关联 Warehouse 表查询获取

### 状态枚举

#### 采购状态 (purchase_status)
- `draft`: 草稿
- `audited`: 已审核
- `closed`: 已结案
- `cancelled`: 已作废

#### 入库状态 (in_status)
- `none`: 未入库
- `partial`: 部分入库
- `full`: 全部入库

#### 付款状态 (pay_status)
- `none`: 未付款
- `partial`: 部分付款
- `full`: 全部结清

#### 采购类型 (purchase_type)
- `direct`: 直运采购
- `warehouse`: 仓库采购

#### 结算方式 (settle_type)
- `月结`: 月结
- `货到付款`: 货到付款
- `款到发货`: 款到发货

#### 发货方式 (shipping_method)
- `直运`: 直运
- `物流`: 物流
- `自提`: 自提
- `送货`: 送货

---

## API 接口

### 1. 创建采购单

**POST** `/api/v1/purchase-orders/`

**权限**: `purchase.create`

#### 请求参数

```json
{
  "purchase_type": "direct",
  "supplier_id": 1,
  "brand_id": 1,
  "settle_type": "月结",
  "expect_arrive_date": "2025-04-30",
  "remark": "备注",
  "items": [
    {
      "row_no": 1,
      "spec_id": 1,
      "warehouse_id": 1,
      "purchase_qty": 2,
      "purchase_price": 4000,
      "discount": 1.0,
      "shipping_method": "直运",
      "source_sale_row_no": 1
    }
  ]
}
```

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单创建成功",
  "result": {
    "purchase_no": "PO202504200001",
    "id": 1
  }
}
```

---

### 2. 获取采购单列表

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
  "message": "获取采购单列表成功",
  "result": [
    {
      "id": 1,
      "purchase_no": "PO202504200001",
      "purchase_type": "direct",
      "brand_id": 1,
      "brand_name": "品牌名称",
      "supplier_id": 1,
      "supplier_name": "供应商名称",
      "settle_type": "月结",
      "total_amt": 8000.00,
      "freight_amt": 100.00,
      "purchase_status": "draft",
      "in_status": "none",
      "pay_status": "none",
      "created_at": "2025-04-20T15:00:00",
      "updated_at": "2025-04-20T15:00:00"
    }
  ]
}
```

---

### 3. 获取采购单详情

**GET** `/api/v1/purchase-orders/{purchase_no}`

**权限**: `purchase.view`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取采购单详情成功",
  "result": {
    "id": 1,
    "purchase_no": "PO202504200001",
    "purchase_type": "direct",
    "source_sale_order_id": 1,
    "source_sale_order_no": "SO202501010001",
    "brand_id": 1,
    "brand_name": "品牌名称",
    "supplier_id": 1,
    "supplier_name": "供应商名称",
    "purchase_user_id": 1,
    "expect_arrive_date": "2025-04-30",
    "settle_type": "月结",
    "total_amt": 8000.00,
    "freight_amt": 100.00,
    "tax_rate": 0.13,
    "tax_amt": 1040.00,
    "total_tax_amt": 9140.00,
    "purchase_status": "audited",
    "in_status": "none",
    "pay_status": "none",
    "creator_id": 1,
    "created_at": "2025-04-20T15:00:00",
    "updated_at": "2025-04-20T15:00:00",
    "remark": "由销售单SO202501010001自动生成-直运采购",
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
        "shipping_method": "直运",
        "created_at": "2025-04-20T15:00:00",
        "updated_at": "2025-04-20T15:00:00"
      }
    ]
  }
}
```

---

### 4. 审核通过采购单

**POST** `/api/v1/purchase-orders/{purchase_no}/approve`

**权限**: `purchase.edit`

审核通过采购单（草稿 → 已审核）

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单审核通过"
}
```

---

### 5. 撤回采购单

**POST** `/api/v1/purchase-orders/{purchase_no}/recall`

**权限**: `purchase.edit`

撤回采购单（删除采购单，更新销售单状态）

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单撤回成功"
}
```

---

## 错误响应

### 采购单不存在

```json
{
  "status": "error",
  "message": "采购单不存在"
}
```

### 只有草稿状态可以审核

```json
{
  "status": "error",
  "message": "只有草稿状态的采购单可以审核"
}
```

### 只有草稿或已审核状态可以撤销

```json
{
  "status": "error",
  "message": "只有草稿或已审核状态的采购单可以撤销"
}
```