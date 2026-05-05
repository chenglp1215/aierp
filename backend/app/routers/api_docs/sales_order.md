# 销售订单管理 API

本文档描述销售订单管理模块的所有 REST API 接口。

**模块路径**: `/api/v1/sales-orders`

**权限要求**:
- `order.view`: 查看订单
- `order.create`: 创建订单
- `order.edit`: 编辑订单
- `order.delete`: 删除订单

---

## 数据模型

### 销售订单创建模型

创建订单时只需要提供以下字段，其他字段由系统自动生成：

```json
{
  "order_date": "2025-01-01",
  "customer_id": "507f1f77bcf86cd799439012",
  "sale_user_id": "507f1f77bcf86cd799439013",
  "deliver_info": {
    "addr": "详细地址",
    "province": "省",
    "city": "市",
    "person_name": "收货人",
    "person_tel": "联系电话"
  },
  "expect_deliver_date": "2025-01-10",
  "settle_type": "月结",
  "invoice_info": {
    "invoice_title": "公司全称",
    "invoice_type": "增值税",
    "tax_number": "纳税人识别号",
    "bank_name": "开户行",
    "bank_account": "银行账号"
  },
  "remark": "急单",
  "items": [
    {
      "row_no": 1,
      "product_id": "507f1f77bcf86cd799439012",
      "spec_id": "507f1f77bcf86cd799439013",
      "brand_id": "507f1f77bcf86cd799439014",
      "brand_name": "品牌名称",
      "qty": 2,
      "price": 5000,
      "discount": 0.8,
      "warehouse_id": "507f1f77bcf86cd799439020",
      "shipping_method": "直运"
    }
  ],
  "cost_details": [
    {
      "cost_amount": 100.00,
      "cost_type": "shipping",
      "associated_doc_type": "outbound_order",
      "associated_doc_id": "507f1f77bcf86cd799439016",
      "remark": "运费"
    }
  ]
}
```

### 字段说明

#### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| order_date | string | 订单日期（YYYY-MM-DD） |
| customer_id | string | 客户ID |
| settle_type | string | 结算方式：月结/货到付款/款到发货 |
| items | array | 商品明细 |

#### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| sale_user_id | string | 销售人员ID |
| deliver_info | object | 发货信息 |
| expect_deliver_date | string | 期望交货日（YYYY-MM-DD） |
| invoice_info | object | 开票信息 |
| remark | string | 备注 |

#### 系统自动计算字段（不需要传入）

| 字段 | 类型 | 说明 |
|------|------|------|
| order_no | string | 订单号（系统生成） |
| total_amt | float | 商品总金额（未税） |
| tax_rate | float | 税率（默认0.13） |
| tax_amt | float | 税额 |
| total_tax_amt | float | 含税总金额 |
| status | object | 订单状态信息（默认草稿） |
| creator_id | string | 创建人ID |
| create_time | string | 创建时间 |
| total_out_qty | int | 累计已出库数量（默认0） |
| total_received_amt | float | 累计已收款金额（默认0） |
| total_invoice_amt | float | 累计已开票金额（默认0） |
| total_return_qty | int | 累计退货数量（默认0） |
| total_return_amt | float | 累计退货金额（默认0） |

### 销售订单完整模型

```json
{
  "id": "507f1f77bcf86cd799439011",
  "order_no": "SO202501010001",
  "order_date": "2025-01-01",
  "customer_id": "507f1f77bcf86cd799439012",
  "sale_user_id": "507f1f77bcf86cd799439013",
  "deliver_info": {
    "addr": "详细地址",
    "province": "省",
    "city": "市",
    "person_name": "收货人",
    "person_tel": "联系电话"
  },
  "expect_deliver_date": "2025-01-10",
  "settle_type": "月结",
  "total_amt": 10000.00,
  "tax_rate": 0.13,
  "tax_amt": 1300.00,
  "total_tax_amt": 11300.00,
  "total_discount_amt": 0.00,
  "status": {
    "order_status": "audited",
    "delivery_status": "none",
    "receive_status": "none",
    "invoice_status": "none"
  },
  "invoice_info": {
    "invoice_title": "公司全称",
    "invoice_type": "增值税",
    "tax_number": "纳税人识别号",
    "bank_name": "开户行",
    "bank_account": "银行账号"
  },
  "creator_id": "507f1f77bcf86cd799439014",
  "create_time": "2025-01-01 10:00:00",
  "remark": "急单",
  "total_out_qty": 0,
  "total_received_amt": 0.00,
  "total_invoice_amt": 0.00,
  "total_return_qty": 0,
  "total_return_amt": 0.00,
  "items": [
    {
      "row_no": 1,
      "product_id": "507f1f77bcf86cd799439012",
      "spec_id": "507f1f77bcf86cd799439013",
      "brand_id": "507f1f77bcf86cd799439014",
      "brand_name": "品牌名称",
      "qty": 2,
      "price": 5000,
      "discount": 0.8,
      "discounted_price": 4000,
      "amt": 8000,
      "warehouse_id": "507f1f77bcf86cd799439020",
      "shipping_method": "直运",
      "out_qty": 0,
      "return_qty": 0,
      "remain_out_qty": 2
    }
  ],
  "cost_details": [
    {
      "id": "507f1f77bcf86cd799439015",
      "cost_amount": 100.00,
      "cost_type": "shipping",
      "associated_doc_type": "outbound_order",
      "associated_doc_no": "OUT202501010001",
      "associated_doc_id": "507f1f77bcf86cd799439016",
      "remark": "运费"
    }
  ]
}
```

### 状态枚举

#### 订单状态 (order_status)
- `draft`: 草稿
- `audited`: 已审核
- `closed`: 已关闭
- `cancelled`: 已取消

#### 发货状态 (delivery_status)
- `none`: 未发货
- `partial`: 部分发货
- `full`: 全部发货

#### 收货状态 (receive_status)
- `none`: 未收货
- `partial`: 部分收货
- `full`: 全部收货

#### 开票状态 (invoice_status)
- `none`: 未开票
- `partial`: 部分开票
- `full`: 全部开票

#### 结算方式 (settle_type)
- `月结`: 月结
- `货到付款`: 货到付款
- `款到发货`: 款到发货

#### 发货方式 (shipping_method)
- `直运`: 直运
- `物流`: 物流
- `自提`: 自提
- `送货`: 送货

#### 成本类型 (cost_type)
- `product`: 商品成本
- `shipping`: 运费
- `other`: 其他费用

#### 关联单据类型 (associated_doc_type)
- `outbound_order`: 出库单
- `purchase_order`: 采购单

### 成本明细模型

```json
{
  "id": "507f1f77bcf86cd799439015",
  "cost_amount": 100.00,
  "cost_type": "shipping",
  "associated_doc_type": "outbound_order",
  "associated_doc_no": "OUT202501010001",
  "associated_doc_id": "507f1f77bcf86cd799439016",
  "remark": "运费"
}
```

#### 成本明细字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 成本明细ID（系统生成） |
| cost_amount | float | 成本金额 |
| cost_type | string | 成本类型：product/shipping/other |
| associated_doc_type | string | 关联单据类型：outbound_order/purchase_order |
| associated_doc_no | string | 关联单据号（系统富化） |
| associated_doc_id | string | 关联单据ID |
| remark | string | 备注 |

---

## API 接口

### 1. 创建销售订单

**POST** `/api/v1/sales-orders/`

**权限**: `order.create`

#### 请求参数

```json
{
  "order_date": "2025-01-01",
  "customer_id": "507f1f77bcf86cd799439012",
  "sale_user_id": "507f1f77bcf86cd799439013",
  "deliver_info": {
    "addr": "详细地址",
    "province": "省",
    "city": "市",
    "person_name": "收货人",
    "person_tel": "联系电话"
  },
  "expect_deliver_date": "2025-01-10",
  "settle_type": "月结",
  "invoice_info": {
    "invoice_title": "公司全称",
    "invoice_type": "增值税",
    "tax_number": "纳税人识别号",
    "bank_name": "开户行",
    "bank_account": "银行账号"
  },
  "remark": "急单",
  "items": [
    {
      "row_no": 1,
      "product_id": "507f1f77bcf86cd799439012",
      "spec_id": "507f1f77bcf86cd799439013",
      "qty": 2,
      "price": 5000,
      "discount": 0.8,
      "warehouse_id": "507f1f77bcf86cd799439020",
      "shipping_method": "直运"
    }
  ],
  "cost_details": [
    {
      "cost_amount": 100.00,
      "cost_type": "shipping",
      "associated_doc_type": "outbound_order",
      "associated_doc_id": "507f1f77bcf86cd799439016",
      "remark": "运费"
    }
  ]
}
```

#### 响应示例

```json
{
  "status": "success",
  "message": "订单创建成功",
  "result": {
    "order_no": "SO202501010001",
    "id": "507f1f77bcf86cd799439011"
  }
}
```

---

### 2. 获取销售订单列表

**GET** `/api/v1/sales-orders/`

**权限**: `order.view`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码（默认：1） |
| page_size | int | 否 | 每页数量（默认：20，最大：100） |
| status | string | 否 | 订单状态 |
| customer_id | string | 否 | 客户ID |
| order_no | string | 否 | 订单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取订单列表成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439011",
        "order_no": "SO202501010001",
        "order_date": "2025-01-01",
        "customer_id": "507f1f77bcf86cd799439012",
        "sale_user_id": "507f1f77bcf86cd799439013",
        "deliver_info": {
          "addr": "详细地址",
          "province": "省",
          "city": "市",
          "person_name": "收货人",
          "person_tel": "联系电话"
        },
        "expect_deliver_date": "2025-01-10",
        "settle_type": "月结",
        "total_amt": 10000.00,
        "tax_rate": 0.13,
        "tax_amt": 1300.00,
        "total_tax_amt": 11300.00,
        "total_discount_amt": 0.00,
        "status": {
          "order_status": "audited",
          "delivery_status": "none",
          "receive_status": "none",
          "invoice_status": "none"
        },
        "invoice_info": {
          "invoice_title": "公司全称",
          "tax_number": "纳税人识别号",
          "bank_name": "开户行",
          "bank_account": "银行账号"
        },
        "creator_id": "507f1f77bcf86cd799439014",
        "create_time": "2025-01-01 10:00:00",
        "remark": "急单",
        "total_out_qty": 0,
        "total_received_amt": 0.00,
        "total_invoice_amt": 0.00,
        "total_return_qty": 0,
        "total_return_amt": 0.00,
        "items": [
          {
            "row_no": 1,
            "product_id": "507f1f77bcf86cd799439012",
            "spec_id": "507f1f77bcf86cd799439013",
            "brand_id": "507f1f77bcf86cd799439014",
            "brand_name": "品牌名称",
            "qty": 2,
            "price": 5000,
            "discount": 0.8,
            "discounted_price": 4000,
            "amt": 8000,
            "warehouse_id": "507f1f77bcf86cd799439020",
            "shipping_method": "直运",
            "out_qty": 0,
            "return_qty": 0,
            "remain_out_qty": 2
          }
        ],
        "cost_details": [
          {
            "id": "507f1f77bcf86cd799439015",
            "cost_amount": 100.00,
            "cost_type": "shipping",
            "associated_doc_type": "outbound_order",
            "associated_doc_no": "OUT202501010001",
            "associated_doc_id": "507f1f77bcf86cd799439016",
            "remark": "运费"
          }
        ]
      }
    ]
  }
}
```

---

### 3. 获取销售订单详情

**GET** `/api/v1/sales-orders/{order_no}`

**权限**: `order.view`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_no | string | 是 | 订单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取订单详情成功",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "order_no": "SO202501010001",
    "order_date": "2025-01-01",
    "customer_id": "507f1f77bcf86cd799439012",
    "sale_user_id": "507f1f77bcf86cd799439013",
    "deliver_info": {
      "addr": "详细地址",
      "province": "省",
      "city": "市",
      "person_name": "收货人",
      "person_tel": "联系电话"
    },
    "expect_deliver_date": "2025-01-10",
    "settle_type": "月结",
    "total_amt": 10000.00,
    "tax_rate": 0.13,
    "tax_amt": 1300.00,
    "total_tax_amt": 11300.00,
    "total_discount_amt": 0.00,
    "status": {
      "order_status": "audited",
      "delivery_status": "none",
      "receive_status": "none",
      "invoice_status": "none"
    },
    "invoice_info": {
      "invoice_title": "公司全称",
      "tax_number": "纳税人识别号",
      "bank_name": "开户行",
      "bank_account": "银行账号"
    },
    "creator_id": "507f1f77bcf86cd799439014",
    "create_time": "2025-01-01 10:00:00",
    "remark": "急单",
    "total_out_qty": 0,
    "total_received_amt": 0.00,
    "total_invoice_amt": 0.00,
    "total_return_qty": 0,
    "total_return_amt": 0.00,
    "items": [
      {
        "row_no": 1,
        "product_id": "507f1f77bcf86cd799439012",
        "spec_id": "507f1f77bcf86cd799439013",
        "brand_id": "507f1f77bcf86cd799439014",
        "brand_name": "品牌名称",
        "qty": 2,
        "price": 5000,
        "discount": 0.8,
        "discounted_price": 4000,
        "amt": 8000,
        "warehouse_id": "507f1f77bcf86cd799439020",
        "shipping_method": "直运",
        "out_qty": 0,
        "return_qty": 0,
        "remain_out_qty": 2
      }
    ],
    "cost_details": [
      {
        "id": "507f1f77bcf86cd799439015",
        "cost_amount": 100.00,
        "cost_type": "shipping",
        "associated_doc_type": "outbound_order",
        "associated_doc_no": "OUT202501010001",
        "associated_doc_id": "507f1f77bcf86cd799439016",
        "remark": "运费"
      }
    ]
  }
}
```

---

### 4. 更新销售订单

**PUT** `/api/v1/sales-orders/{order_no}`

**权限**: `order.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_no | string | 是 | 订单号 |

#### 请求参数

```json
{
  "order_date": "2025-01-02",
  "customer_id": "507f1f77bcf86cd799439012",
  "deliver_info": {
    "addr": "更新后的地址",
    "province": "省",
    "city": "市",
    "person_name": "收货人",
    "person_tel": "联系电话"
  },
  "expect_deliver_date": "2025-01-15",
  "settle_type": "货到付款",
  "remark": "更新后的备注"
}
```

#### 响应示例

```json
{
  "status": "success",
  "message": "订单更新成功"
}
```

---

### 5. 删除销售订单

**DELETE** `/api/v1/sales-orders/{order_no}`

**权限**: `order.delete`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_no | string | 是 | 订单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "订单删除成功"
}
```

---

### 6. 更新订单状态

**PATCH** `/api/v1/sales-orders/{order_no}/order-status`

**权限**: `order.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_no | string | 是 | 订单号 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 订单状态（draft/audited/closed/cancelled） |

#### 响应示例

```json
{
  "status": "success",
  "message": "订单状态更新成功"
}
```

---

### 7. 更新发货状态

**PATCH** `/api/v1/sales-orders/{order_no}/delivery-status`

**权限**: `order.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_no | string | 是 | 订单号 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| delivery_status | string | 是 | 发货状态（none/partial/full） |

#### 响应示例

```json
{
  "status": "success",
  "message": "发货状态更新成功"
}
```

---

### 8. 更新收货状态

**PATCH** `/api/v1/sales-orders/{order_no}/receive-status`

**权限**: `order.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_no | string | 是 | 订单号 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| receive_status | string | 是 | 收货状态（none/partial/full） |

#### 响应示例

```json
{
  "status": "success",
  "message": "收货状态更新成功"
}
```

---

### 9. 更新开票状态

**PATCH** `/api/v1/sales-orders/{order_no}/invoice-status`

**权限**: `order.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| order_no | string | 是 | 订单号 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| invoice_status | string | 是 | 开票状态（none/partial/full） |

#### 响应示例

```json
{
  "status": "success",
  "message": "开票状态更新成功"
}
```

---

## 错误响应

### 订单不存在

```json
{
  "status": "error",
  "message": "订单不存在"
}
```

### 订单更新失败

```json
{
  "status": "error",
  "message": "订单不存在或更新失败"
}
```

### 订单删除失败

```json
{
  "status": "error",
  "message": "订单不存在或删除失败"
}
```

### 状态更新失败

```json
{
  "status": "error",
  "message": "订单不存在或状态更新失败"
}
```