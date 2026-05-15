# 销售订单管理 API

> 用于管理销售订单的完整生命周期，包括创建、审核、状态流转等操作

## 基础信息

- **基础路径**: `/api/v1`
- **认证方式**: Bearer Token (JWT)

---

## 统一响应格式

### 成功响应

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {}
}
```

### 错误响应

```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

---

## 目录

- [7.7.1 创建销售订单](#771-创建销售订单)
- [7.7.2 创建并提交销售订单](#772-创建并提交销售订单直接审核通过)
- [7.7.3 获取销售订单列表](#773-获取销售订单列表)
- [7.7.4 获取销售订单详情](#774-获取销售订单详情)
- [7.7.5 更新销售订单](#775-更新销售订单)
- [7.7.6 删除销售订单](#776-删除销售订单)
- [7.7.7 提交审核](#777-提交审核)
- [7.7.8 审核通过](#778-审核通过)
- [7.7.9 驳回订单](#779-驳回订单)
- [7.7.10 取消订单](#7710-取消订单)
- [7.7.11 获取状态流转记录](#7711-获取状态流转记录)
- [数据模型](#数据模型)
- [业务规则](#业务规则)
- [权限说明](#权限说明)

---

## 订单管理

### 7.7.1 创建销售订单

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/` |
| **权限** | `order.create` |

**请求体**

```json
{
  "order_date": "2025-01-01",
  "customer_id": 1,
  "customer_name": "客户名称",
  "sale_user_id": 1,
  "settle_type": "月结",
  "tax_rate": 0.13,
  "expect_deliver_date": "2025-01-10",
  "remark": "备注",
  "deliver_info": {
    "addr": "详细地址",
    "province": "省",
    "city": "市",
    "person_name": "收货人",
    "person_tel": "联系电话"
  },
  "items": [
    {
      "row_no": 1,
      "spec_id": 1,
      "product_code": "PRD001",
      "spec_code": "SPEC001",
      "warehouse_id": 1,
      "qty": 2,
      "price": 5000,
      "discount": 0.8,
      "shipping_method": "warehouse"
    }
  ]
}
```

**商品明细分项说明**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| row_no | int | 是 | 行号（≥1） |
| spec_id | int | 否 | 规格ID（外键关联，用于获取商品、品牌信息） |
| product_code | string | 否 | 商品编码（快照） |
| spec_code | string | 否 | 规格编码（快照） |
| warehouse_id | int | 否 | 仓库ID（外键关联） |
| qty | int | 是 | 数量（≥1） |
| price | float | 是 | 单价（≥0） |
| discount | float | 否 | 折扣率（0-1，默认1.0） |
| shipping_method | string | 是 | 发货方式：`direct`（直运）/ `warehouse`（仓库发货） |

> **重要说明**:
> - `order_no` 由系统自动生成（格式 `SO{YYYYMMDD}{4位序号}`），金额由系统自动计算
> - 商品名称（product_name）、品牌名称（brand_name）通过 `spec_id` 外键关联自动获取
> - `product_code`、`spec_code` 作为历史快照保存，防止商品信息变更影响历史订单

**成功响应**

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "order_no": "SO202501010001",
    "id": 1
  }
}
```

---

### 7.7.2 创建并提交销售订单（直接审核通过）

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/create-and-submit` |
| **权限** | `order.create` |

**请求体**：与创建销售订单相同

**成功响应**

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "order_no": "SO202501010001",
    "id": 1
  }
}
```

> 创建订单后直接将订单状态设为"已审核"（audited），可直接下推采购

---

### 7.7.3 获取销售订单列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/sales-orders/` |
| **权限** | `order.view` |

**查询参数**

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| status | string | 否 | — | 订单状态筛选（draft/pending/audited/...） |
| customer_id | int | 否 | — | 客户ID筛选 |
| order_no | string | 否 | — | 订单号模糊搜索 |
| keyword | string | 否 | — | 订单号/客户名模糊搜索 |

**成功响应**

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "order_no": "SO202501010001",
        "order_date": "2025-01-01",
        "customer_id": 1,
        "customer_name": "客户名称",
        "sale_user_id": 1,
        "sale_user_name": "销售人员",
        "order_status": "audited",
        "delivery_status": "none",
        "receive_status": "none",
        "invoice_status": "none",
        "total_amt": 8000.00,
        "tax_rate": 0.13,
        "tax_amt": 1040.00,
        "total_tax_amt": 9040.00,
        "total_discount_amt": 0.00,
        "expect_deliver_date": "2025-01-10",
        "settle_type": "月结",
        "remark": "备注",
        "creator_id": 1,
        "creator_name": "创建人",
        "created_at": "2025-01-01T10:00:00+00:00",
        "updated_at": "2025-01-01T10:00:00+00:00"
      }
    ]
  }
}
```

---

### 7.7.4 获取销售订单详情

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/sales-orders/{order_no}` |
| **权限** | `order.view` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": 1,
    "order_no": "SO202501010001",
    "order_date": "2025-01-01",
    "customer_id": 1,
    "customer_name": "客户名称",
    "sale_user_id": 1,
    "sale_user_name": "销售人员",
    "order_status": "draft",
    "delivery_status": "none",
    "receive_status": "none",
    "invoice_status": "none",
    "total_amt": 8000.00,
    "tax_rate": 0.13,
    "tax_amt": 1040.00,
    "total_tax_amt": 9040.00,
    "total_discount_amt": 0.00,
    "expect_deliver_date": "2025-01-10",
    "settle_type": "月结",
    "remark": "备注",
    "creator_id": 1,
    "creator_name": "创建人",
    "created_at": "2025-01-01T10:00:00+00:00",
    "updated_at": "2025-01-01T10:00:00+00:00",
    "items": [
      {
        "id": 1,
        "sales_order_id": 1,
        "row_no": 1,
        "product_id": 1,
        "product_code": "PRD001",
        "product_name": "商品名称",
        "spec_id": 1,
        "spec_code": "SPEC001",
        "brand_id": 1,
        "brand_name": "品牌名称",
        "warehouse_id": 1,
        "warehouse_name": "仓库名称",
        "qty": 2,
        "price": 5000.00,
        "discount": 0.8,
        "discounted_price": 4000.00,
        "amt": 8000.00,
        "shipping_method": "仓库发货",
        "pushed": false,
        "out_qty": 0,
        "return_qty": 0,
        "created_at": "2025-01-01T10:00:00+00:00",
        "updated_at": "2025-01-01T10:00:00+00:00"
      }
    ],
    "deliver_info": {
      "id": 1,
      "addr": "详细地址",
      "province": "省",
      "city": "市",
      "person_name": "收货人",
      "person_tel": "联系电话"
    }
  }
}
```

> **说明**: 
> - `product_id`、`product_name`、`brand_id`、`brand_name` 通过 `spec_id` 外键关联自动获取
> - `warehouse_name` 通过 `warehouse_id` 外键关联自动获取
> - `shipping_method` 返回中文：`直运` 或 `仓库发货`

**错误响应**

| 场景 | message |
|------|---------|
| 订单不存在 | `"订单不存在"` |

---

### 7.7.5 更新销售订单

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/sales-orders/{order_no}` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**请求体**（所有字段可选，不传的字段不修改）

```json
{
  "order_date": "2025-01-02",
  "customer_id": 2,
  "customer_name": "新客户",
  "expect_deliver_date": "2025-01-15",
  "settle_type": "货到付款",
  "remark": "更新后的备注",
  "items": [
    {
      "row_no": 1,
      "spec_id": 1,
      "product_code": "PRD001",
      "qty": 3,
      "price": 5000,
      "discount": 0.9,
      "shipping_method": "warehouse"
    }
  ]
}
```

**成功响应**

```json
{
  "status": "success",
  "message": "订单更新成功",
  "result": null
}
```

> 仅草稿（draft）或已取消（cancelled）状态的订单可修改

**错误响应**

| 场景 | message |
|------|---------|
| 订单不存在 | `"订单不存在: {order_no}"` |
| 状态不允许修改 | `"只能修改草稿或已取消的订单"` |

---

### 7.7.6 删除销售订单

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/sales-orders/{order_no}` |
| **权限** | `order.delete` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单删除成功",
  "result": null
}
```

> 仅草稿（draft）或已取消（cancelled）状态的订单可删除

**错误响应**

| 场景 | message |
|------|---------|
| 订单不存在 | `"订单不存在: {order_no}"` |
| 状态不允许删除 | `"只能删除草稿或已取消的订单"` |

---

## 状态管理

### 7.7.7 提交审核

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/submit` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单已提交审核",
  "result": null
}
```

> 将订单状态从 draft 变更为 pending

**错误响应**

| 场景 | message |
|------|---------|
| 订单不存在 | `"订单不存在: {order_no}"` |
| 状态不允许提交 | `"订单状态不允许从 draft 变更为 pending"` |

---

### 7.7.8 审核通过

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/approve` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单审核通过",
  "result": null
}
```

> 将订单状态从 pending 变更为 audited

**错误响应**

| 场景 | message |
|------|---------|
| 订单不存在 | `"订单不存在: {order_no}"` |
| 状态不允许审核 | `"订单状态不允许从 pending 变更为 audited"` |

---

### 7.7.9 驳回订单

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/reject` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单已驳回",
  "result": null
}
```

> 将订单状态从 pending 变更为 draft

**错误响应**

| 场景 | message |
|------|---------|
| 订单不存在 | `"订单不存在: {order_no}"` |
| 状态不允许驳回 | `"订单状态不允许从 pending 变更为 draft"` |

---

### 7.7.10 取消订单

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/cancel` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单已取消",
  "result": null
}
```

> 将订单状态变更为 cancelled（仅 draft、pending、audited 等状态可取消）

**错误响应**

| 场景 | message |
|------|---------|
| 订单不存在 | `"订单不存在: {order_no}"` |
| 状态不允许取消 | `"订单状态不允许取消"` |

---

### 7.7.11 获取状态流转记录

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/sales-orders/{order_no}/status-flows` |
| **权限** | `order.view` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "操作成功",
  "result": [
    {
      "id": 1,
      "order_no": "SO202501010001",
      "order_type": "sales",
      "field": "order_status",
      "old_value": null,
      "new_value": "draft",
      "operator": "张三",
      "remark": "创建订单",
      "created_at": "2025-01-01T10:00:00+00:00"
    },
    {
      "id": 2,
      "order_no": "SO202501010001",
      "order_type": "sales",
      "field": "order_status",
      "old_value": "draft",
      "new_value": "pending",
      "operator": "张三",
      "remark": "提交审核",
      "created_at": "2025-01-01T10:30:00+00:00"
    }
  ]
}
```

---

## 数据模型

### SalesOrder（销售订单主表）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 订单ID（MySQL 自增主键） |
| order_no | string | 订单号（系统自动生成，格式 SO{YYYYMMDD}{4位序号}） |
| order_date | string | 订单日期 |
| customer_id | int | 客户ID |
| customer_name | string | 客户名称（快照） |
| sale_user_id | int | 销售人员ID |
| sale_user_name | string | 销售人员名称 |
| order_status | string | 订单状态（见状态枚举） |
| delivery_status | string | 发货状态（none/partial/full） |
| receive_status | string | 收货状态（none/partial/full） |
| invoice_status | string | 开票状态（none/partial/full） |
| total_amt | float | 商品总金额（未税） |
| tax_rate | float | 税率 |
| tax_amt | float | 税额 |
| total_tax_amt | float | 含税总金额 |
| total_discount_amt | float | 整单折扣金额 |
| expect_deliver_date | string | 期望交货日 |
| settle_type | string | 结算方式 |
| remark | string | 备注 |
| creator_id | int | 创建人ID |
| creator_name | string | 创建人名称 |
| created_at | string | 创建时间（ISO 8601 格式） |
| updated_at | string | 更新时间（ISO 8601 格式） |

### SalesOrderItem（订单明细）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 明细ID |
| sales_order_id | int | 关联订单ID |
| row_no | int | 行号 |
| spec_id | int | 规格ID（外键 → ProductSpec） |
| product_id | int | 商品ID（通过 spec.product 获取） |
| product_code | string | 商品编码（快照） |
| product_name | string | 商品名称（通过 spec.product.name 获取） |
| spec_code | string | 规格编码（快照） |
| brand_id | int | 品牌ID（通过 spec.product.brand 获取） |
| brand_name | string | 品牌名称（通过 spec.product.brand.name 获取） |
| warehouse_id | int | 仓库ID（外键 → Warehouse） |
| warehouse_name | string | 仓库名称（通过 warehouse.name 获取） |
| qty | int | 订购数量 |
| price | float | 原始单价 |
| discount | float | 折扣率 |
| discounted_price | float | 折后单价 |
| amt | float | 行金额 |
| shipping_method | string | 发货方式（中文：直运/仓库发货） |
| pushed | boolean | 是否已下推采购 |
| out_qty | int | 已发货数量 |
| return_qty | int | 已退货数量 |
| created_at | string | 创建时间（ISO 8601 格式） |
| updated_at | string | 更新时间（ISO 8601 格式） |

### SalesDeliverInfo（发货信息）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 发货信息ID |
| sales_order_id | int | 关联订单ID |
| addr | string | 详细地址 |
| province | string | 省 |
| city | string | 市 |
| person_name | string | 收货人 |
| person_tel | string | 联系电话 |

---

## 业务规则

### 外键关联设计

```
SalesOrderItem
    ├── spec_id → ProductSpec
    │                ├── product_id → Product
    │                │                  └── brand_id → Brand
    │                └── spec_code, packaging, price...
    └── warehouse_id → Warehouse
```

> **设计说明**: 订单明细只需关联 `spec_id` 和 `warehouse_id`，商品信息和品牌信息通过 `spec.product.brand` 链式获取，避免数据冗余。

### 订单状态流转

```
draft → pending → audited → partially_pushed_to_purchase → pushed_to_purchase → closed
  ↓        ↓         ↓                  ↓                        ↓
cancelled cancelled  cancelled          cancelled               cancelled
```

| 当前状态 | 可变更为 |
|----------|----------|
| draft（草稿） | pending, cancelled |
| pending（待审核） | audited, draft |
| audited（已审核） | partially_pushed_to_purchase, pushed_to_purchase, closed, cancelled |
| partially_pushed_to_purchase（部分下推） | pushed_to_purchase, closed, cancelled |
| pushed_to_purchase（已下推） | closed, cancelled |
| closed / cancelled | 不可变更 |

### 发货/收货/开票状态流转

| 当前状态 | 可变更为 |
|----------|----------|
| none（未） | partial（部分）, full（全部） |
| partial（部分） | full（全部） |
| full（全部） | 不可变更 |

### 订单操作约束

1. **订单号**: 格式 `SO{YYYYMMDD}{4位序号}`，系统自动生成
2. **金额计算**: `discounted_price = price × discount`，`amt = qty × discounted_price`，`total_amt = Σ amt`，`tax_amt = total_amt × tax_rate`
3. **修改/删除约束**: 仅草稿和已取消的订单可修改/删除
4. **发货方式**: `direct`（直运）/ `warehouse`（仓库发货），响应返回中文

### 状态枚举值

#### 订单状态 (order_status)
| 值 | 说明 |
|------|------|
| draft | 草稿 |
| pending | 待审核 |
| audited | 已审核 |
| partially_pushed_to_purchase | 部分下推采购 |
| pushed_to_purchase | 已下推采购 |
| closed | 已关闭 |
| cancelled | 已取消 |

#### 发货/收货/开票状态
| 值 | 说明 |
|------|------|
| none | 未 |
| partial | 部分 |
| full | 全部 |

#### 发货方式 (shipping_method)
| 请求值 | 响应值 | 说明 |
|------|------|------|
| direct | 直运 | 直运 |
| warehouse | 仓库发货 | 仓库发货 |

---

## 权限说明

| 接口 | 所需权限 |
|------|----------|
| 创建/创建并提交销售订单 | `order.create` |
| 获取列表/详情/状态流转记录 | `order.view` |
| 更新订单/提交审核/审核通过/驳回/取消 | `order.edit` |
| 删除销售订单 | `order.delete` |
