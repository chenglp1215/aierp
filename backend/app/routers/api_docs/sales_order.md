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
- [7.7.12 下推采购](#7712-下推采购)
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
  "customer_id": "客户ID",
  "sale_user_id": "销售人员ID（可选）",
  "settle_type": "月结",
  "tax_rate": 0.13,
  "deliver_info": {
    "addr": "详细地址",
    "province": "省",
    "city": "市",
    "person_name": "收货人",
    "person_tel": "联系电话"
  },
  "expect_deliver_date": "2025-01-10",
  "invoice_info": {
    "invoice_title": "公司全称",
    "invoice_type": "增值税",
    "tax_number": "纳税人识别号",
    "bank_name": "开户行",
    "bank_account": "银行账号"
  },
  "remark": "备注",
  "items": [
    {
      "row_no": 1,
      "product_code": "PRD001",
      "spec_code": "SP001",
      "brand_id": "品牌ID（可选，不传则自动从商品获取）",
      "qty": 2,
      "price": 5000,
      "discount": 0.8,
      "warehouse_id": "仓库ID（可选）",
      "shipping_method": "直运"
    }
  ]
}
```

**商品明细分项说明**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| row_no | int | 是 | 行号（≥1） |
| product_code | string | 是 | 商品编码 |
| qty | int | 是 | 数量（≥1） |
| price | float | 是 | 单价（≥0） |
| discount | float | 是 | 折扣率（0-1） |
| shipping_method | string | 是 | 发货方式：直运/物流/自提/送货 |
| spec_code | string | 否 | 规格编码 |
| brand_id | string | 否 | 品牌ID（不传则自动从商品获取） |
| warehouse_id | string | 否 | 仓库ID |

> **说明**: `order_no` 由系统自动生成（格式 `SO{YYYYMMDD}{4位序号}`），`total_amt`、`tax_amt`、`total_tax_amt` 由系统自动计算。`cost_details`（成本明细）不在创建时填写，而是在后续业务流转过程中增加

**成功响应**

```json
{
  "status": "success",
  "result": {
    "order_no": "SO202501010001",
    "id": "507f1f77bcf86cd799439011"
  }
}
```

**错误响应**

| 场景 | message |
|------|---------|
| 订单明细为空 | `"订单明细不能为空"` |
| 商品编码为空 | `"商品编码不能为空"` |
| 数量非法 | `"商品 xxx 的数量必须大于0"` |
| 参数校验失败 | `"参数验证失败"` |

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
  "result": {
    "order_no": "SO202501010001",
    "id": "507f1f77bcf86cd799439011"
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
| status | string | 否 | — | 订单状态筛选 |
| customer_id | string | 否 | — | 客户ID筛选 |
| order_no | string | 否 | — | 订单号模糊搜索 |
| keyword | string | 否 | — | 订单号/客户名/商品名/规格编号模糊搜索 |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439011",
        "order_no": "SO202501010001",
        "order_date": "2025-01-01",
        "customer_id": "客户ID",
        "settle_type": "月结",
        "total_amt": 8000.00,
        "tax_rate": 0.13,
        "tax_amt": 1040.00,
        "total_tax_amt": 9040.00,
        "status": {
          "order_status": "audited",
          "delivery_status": "none",
          "receive_status": "none",
          "invoice_status": "none"
        },
        "items": [
          {
            "row_no": 1,
            "product_code": "PRD001",
            "product_name": "有机红茶",
            "brand_name": "品牌A",
            "qty": 2,
            "price": 5000,
            "discount": 0.8,
            "discounted_price": 4000,
            "amt": 8000,
            "shipping_method": "直运"
          }
        ]
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
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "order_no": "SO202501010001",
    "order_date": "2025-01-01",
    "customer_id": "客户ID",
    "settle_type": "月结",
    "total_amt": 8000.00,
    "tax_rate": 0.13,
    "tax_amt": 1040.00,
    "total_tax_amt": 9040.00,
    "status": {
      "order_status": "draft",
      "delivery_status": "none",
      "receive_status": "none",
      "invoice_status": "none"
    },
    "items": [],
    "cost_details": []
  }
}
```

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
  "customer_id": "新客户ID",
  "settle_type": "货到付款",
  "remark": "更新后的备注"
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

> 将订单状态变更为 cancelled（仅特定状态可取消）

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
  "result": [
    {
      "id": "记录ID",
      "order_no": "SO202501010001",
      "field": "order_status",
      "old_value": "draft",
      "new_value": "audited",
      "operator": "张三",
      "operate_time": "2025-01-01 10:30:00"
    }
  ]
}
```

---

## 采购下推

### 7.7.12 下推采购

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/push-to-purchase` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**请求体**

```json
{
  "items": [
    {"row_no": 1},
    {"row_no": 2}
  ]
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| items | array | 是 | 要下推的商品行号列表 |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "purchase_orders": [
      {
        "purchase_order_id": "采购单ID",
        "supplier_id": "供应商ID",
        "items_count": 2
      }
    ]
  }
}
```

---

## 数据模型

### SalesOrder（销售订单）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 订单ID（MySQL 自增主键） |
| order_no | string | 订单号（系统自动生成，格式 SO{YYYYMMDD}{4位序号}） |
| order_date | string | 订单日期 |
| customer_id | int | 客户ID |
| customer_name | string | 客户名称 |
| sale_user_id | int | 销售人员ID |
| sale_user_name | string | 销售人员名称 |
| order_status | string | 订单状态（draft/pending/audited/...） |
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
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| items | SalesOrderItem[] | 商品明细 |
| deliver_info | SalesDeliverInfo | 发货信息 |

### SalesOrderItem（商品明细）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 明细ID |
| sales_order_id | int | 关联订单ID |
| row_no | int | 行号 |
| product_id | int | 商品ID |
| product_code | string | 商品编码 |
| product_name | string | 商品名称 |
| spec_id | int | 规格ID |
| spec_code | string | 规格编码 |
| brand_id | int | 品牌ID |
| brand_name | string | 品牌名称 |
| warehouse_id | int | 仓库ID |
| warehouse_name | string | 仓库名称 |
| qty | int | 订购数量 |
| price | float | 原始单价 |
| discount | float | 折扣率 |
| discounted_price | float | 折后单价 |
| amt | float | 行金额 |
| shipping_method | string | 发货方式（direct/warehouse） |
| pushed | boolean | 是否已下推采购 |
| out_qty | int | 已发货数量 |
| return_qty | int | 已退货数量 |

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
4. **商品信息富化**: 创建订单时按 `product_code` 自动从商品库获取商品名称、品牌等信息

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

#### 结算方式 (settle_type)
| 值 | 说明 |
|------|------|
| 月结 | 月结 |
| 货到付款 | 货到付款 |
| 款到发货 | 款到发货 |

#### 发货方式 (shipping_method)
| 值 | 说明 |
|------|------|
| 直运 | 直运 |
| 物流 | 物流 |
| 自提 | 自提 |
| 送货 | 送货 |

---

## 权限说明

| 接口 | 所需权限 |
|------|----------|
| 创建/创建并提交销售订单 | `order.create` |
| 获取列表/详情/状态流转记录 | `order.view` |
| 更新订单/状态更新/下推采购 | `order.edit` |
| 删除销售订单 | `order.delete` |
