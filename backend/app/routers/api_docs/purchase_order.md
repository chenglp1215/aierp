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

### 采购单创建模型

创建采购单时只需要提供以下字段，其他字段由系统自动生成：

```json
{
  "purchase_type": "direct",
  "source_sale_order_no": "SO202501010001",
  "source_sale_order_id": "507f1f77bcf86cd799439011",
  "brand_id": "507f1f77bcf86cd799439014",
  "supplier_id": "507f1f77bcf86cd799439032",
  "purchase_user_id": "507f1f77bcf86cd799439033",
  "receive_info": {
    "type": "customer",
    "warehouse_id": null,
    "customer_addr": "详细收货地址",
    "province": "省份",
    "city": "城市",
    "contact_person": "收货人",
    "contact_tel": "联系电话"
  },
  "expect_arrive_date": "2025-04-30",
  "settle_type": "月结",
  "freight_amt": 100.00,
  "remark": "由销售单自动生成-直运采购",
  "items": [
    {
      "row_no": 1,
      "product_id": "507f1f77bcf86cd799439012",
      "spec_id": "507f1f77bcf86cd799439013",
      "brand_id": "507f1f77bcf86cd799439014",
      "brand_name": "品牌名称",
      "purchase_qty": 2,
      "purchase_price": 4000,
      "discount": 1.0,
      "amt": 8000,
      "shipping_method": "直运",
      "source_sale_row_no": 1,
      "warehouse_id": "507f1f77bcf86cd799439020"
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

#### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| supplier_id | string | 供应商ID（可为空，系统根据品牌自动选择供应商） |
| source_sale_order_no | string | 关联源销售订单号 |
| source_sale_order_id | string | 关联源销售订单主键ID |
| brand_id | string | 品牌ID |
| purchase_user_id | string | 采购员用户ID |
| receive_info | object | 收货信息 |
| expect_arrive_date | string | 预计到货日期（YYYY-MM-DD） |
| freight_amt | float | 运费总金额（默认0） |
| remark | string | 备注 |

#### 系统自动计算字段（不需要传入）

| 字段 | 类型 | 说明 |
|------|------|------|
| purchase_no | string | 采购单号（系统生成） |
| total_amt | float | 物料不含税总金额（根据商品明细自动计算） |
| status | object | 状态信息（默认草稿） |
| creator_id | string | 创建人ID |
| create_time | string | 创建时间 |

### 采购单完整模型

```json
{
  "id": "507f1f77bcf86cd799439031",
  "purchase_no": "PO202504200001",
  "purchase_type": "direct",
  "source_sale_order_no": "SO202501010001",
  "source_sale_order_id": "507f1f77bcf86cd799439011",
  "brand_id": "507f1f77bcf86cd799439014",
  "brand_name": "品牌名称",
  "supplier_id": "507f1f77bcf86cd799439032",
  "supplier_name": "供应商名称",
  "purchase_user_id": "507f1f77bcf86cd799439033",
  "receive_info": {
    "type": "customer",
    "warehouse_id": null,
    "warehouse_name": null,
    "customer_addr": "详细收货地址",
    "province": "省份",
    "city": "城市",
    "contact_person": "收货人",
    "contact_tel": "联系电话"
  },
  "expect_arrive_date": "2025-04-30",
  "settle_type": "月结",
  "total_amt": 8000.00,
  "freight_amt": 100.00,
  "status": {
    "purchase_status": "audited",
    "in_status": "none",
    "pay_status": "none"
  },
  "creator_id": "507f1f77bcf86cd799439014",
  "create_time": "2025-04-20 15:00:00",
  "remark": "由销售单SO202501010001自动生成-直运采购",
  "items": [
    {
      "row_no": 1,
      "product_id": "507f1f77bcf86cd799439012",
      "spec_id": "507f1f77bcf86cd799439013",
      "brand_id": "507f1f77bcf86cd799439014",
      "brand_name": "品牌名称",
      "purchase_qty": 2,
      "in_qty": 0,
      "return_qty": 0,
      "purchase_price": 4000,
      "discount": 1.0,
      "amt": 8000,
      "shipping_method": "直运",
      "source_sale_row_no": 1,
      "warehouse_id": "507f1f77bcf86cd799439020"
    }
  ]
}
```

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
  "supplier_id": "507f1f77bcf86cd799439032",
  "brand_id": "507f1f77bcf86cd799439014",
  "settle_type": "月结",
  "receive_info": {
    "type": "customer",
    "customer_addr": "详细收货地址",
    "province": "省份",
    "city": "城市",
    "contact_person": "收货人",
    "contact_tel": "联系电话"
  },
  "expect_arrive_date": "2025-04-30",
  "remark": "备注",
  "items": [
    {
      "row_no": 1,
      "product_id": "507f1f77bcf86cd799439012",
      "spec_id": "507f1f77bcf86cd799439013",
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
    "id": "507f1f77bcf86cd799439031"
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
| status | string | 否 | 采购状态 |
| purchase_type | string | 否 | 采购类型 |
| brand_id | string | 否 | 品牌ID |
| supplier_id | string | 否 | 供应商ID |
| purchase_no | string | 否 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取采购单列表成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439031",
        "purchase_no": "PO202504200001",
        "purchase_type": "direct",
        "brand_name": "品牌名称",
        "supplier_name": "供应商名称",
        "settle_type": "月结",
        "total_amt": 8000.00,
        "freight_amt": 100.00,
        "status": {
          "purchase_status": "draft",
          "in_status": "none",
          "pay_status": "none"
        },
        "create_time": "2025-04-20 15:00:00",
        "items": []
      }
    ]
  }
}
```

---

### 3. 快速搜索采购单

**GET** `/api/v1/purchase-orders/search`

**权限**: `purchase.view`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（采购单号/供应商名称/品牌名称） |
| limit | int | 否 | 返回数量（默认：20，最大：100） |

#### 响应示例

```json
{
  "status": "success",
  "message": "搜索成功",
  "result": [
    {
      "id": "507f1f77bcf86cd799439031",
      "purchase_no": "PO202504200001",
      "purchase_type": "direct",
      "brand_name": "品牌名称",
      "supplier_name": "供应商名称",
      "settle_type": "月结",
      "total_amt": 8000.00,
      "freight_amt": 100.00,
      "status": {
        "purchase_status": "draft",
        "in_status": "none",
        "pay_status": "none"
      }
    }
  ]
}
```

---

### 4. 获取采购单详情

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
    "id": "507f1f77bcf86cd799439031",
    "purchase_no": "PO202504200001",
    "purchase_type": "direct",
    "source_sale_order_no": "SO202501010001",
    "brand_id": "507f1f77bcf86cd799439014",
    "brand_name": "品牌名称",
    "supplier_id": "507f1f77bcf86cd799439032",
    "supplier_name": "供应商名称",
    "purchase_user_id": "507f1f77bcf86cd799439033",
    "receive_info": {
      "type": "customer",
      "warehouse_id": null,
      "warehouse_name": null,
      "customer_addr": "详细收货地址",
      "province": "省份",
      "city": "城市",
      "contact_person": "收货人",
      "contact_tel": "联系电话"
    },
    "expect_arrive_date": "2025-04-30",
    "settle_type": "月结",
    "total_amt": 8000.00,
    "freight_amt": 100.00,
    "status": {
      "purchase_status": "draft",
      "in_status": "none",
      "pay_status": "none"
    },
    "creator_id": "507f1f77bcf86cd799439014",
    "create_time": "2025-04-20 15:00:00",
    "remark": "由销售单SO202501010001自动生成-直运采购",
    "total_in_qty": 0,
    "total_paid_amt": 0.00,
    "total_return_qty": 0,
    "total_return_amt": 0.00,
    "items": [
      {
        "row_no": 1,
        "product_id": "507f1f77bcf86cd799439012",
        "spec_id": "507f1f77bcf86cd799439013",
        "brand_id": "507f1f77bcf86cd799439014",
        "brand_name": "品牌名称",
        "purchase_qty": 2,
        "in_qty": 0,
        "return_qty": 0,
        "purchase_price": 4000,
        "discount": 1.0,
        "amt": 8000,
        "shipping_method": "直运",
        "source_sale_row_no": 1,
        "warehouse_id": "507f1f77bcf86cd799439020"
      }
    ]
  }
}
```

---

### 5. 更新采购单

**PUT** `/api/v1/purchase-orders/{purchase_no}`

**权限**: `purchase.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 请求参数

```json
{
  "supplier_id": "507f1f77bcf86cd799439032",
  "expect_arrive_date": "2025-05-15",
  "settle_type": "货到付款",
  "remark": "更新后的备注"
}
```

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单更新成功"
}
```

---

### 6. 删除采购单

**DELETE** `/api/v1/purchase-orders/{purchase_no}`

**权限**: `purchase.delete`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单删除成功"
}
```

---

### 7. 更新采购状态

**PATCH** `/api/v1/purchase-orders/{purchase_no}/purchase-status`

**权限**: `purchase.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 采购状态（draft/audited/closed/cancelled） |

#### 响应示例

```json
{
  "status": "success",
  "message": "采购状态更新成功"
}
```

---

### 8. 更新入库状态

**PATCH** `/api/v1/purchase-orders/{purchase_no}/in-status`

**权限**: `purchase.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| in_status | string | 是 | 入库状态（none/partial/full） |

#### 响应示例

```json
{
  "status": "success",
  "message": "入库状态更新成功"
}
```

---

### 9. 更新付款状态

**PATCH** `/api/v1/purchase-orders/{purchase_no}/pay-status`

**权限**: `purchase.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pay_status | string | 是 | 付款状态（none/partial/full） |

#### 响应示例

```json
{
  "status": "success",
  "message": "付款状态更新成功"
}
```

---

### 10. 撤回采购单

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

### 11. 审核通过采购单

**POST** `/api/v1/purchase-orders/{purchase_no}/approve`

**权限**: `purchase.edit`

审核通过采购单（草稿 -> 已审核）

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

### 12. 结案采购单

**POST** `/api/v1/purchase-orders/{purchase_no}/close`

**权限**: `purchase.edit`

结案采购单（已审核 -> 已结案）

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单结案成功"
}
```

---

### 13. 重审采购单

**POST** `/api/v1/purchase-orders/{purchase_no}/reaudit`

**权限**: `purchase.edit`

重审采购单（已审核 -> 草稿）

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单重审成功（已撤回到草稿）"
}
```

---

### 14. 作废采购单

**POST** `/api/v1/purchase-orders/{purchase_no}/void`

**权限**: `purchase.edit`

作废采购单（已审核 -> 已作废）

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "采购单作废成功"
}
```

---

### 15. 获取状态流转记录

**GET** `/api/v1/purchase-orders/{purchase_no}/status-flows`

**权限**: `purchase.view`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| purchase_no | string | 是 | 采购单号 |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取状态流转记录成功",
  "result": [
    {
      "id": "507f1f77bcf86cd799439040",
      "order_no": "PO202504200001",
      "field": "purchase_status",
      "old_value": null,
      "new_value": "draft",
      "operator": "admin",
      "operate_time": "2025-04-20 15:00:00",
      "remark": "采购单创建"
    },
    {
      "id": "507f1f77bcf86cd799439041",
      "order_no": "PO202504200001",
      "field": "purchase_status",
      "old_value": "draft",
      "new_value": "audited",
      "operator": "admin",
      "operate_time": "2025-04-20 16:00:00",
      "remark": null
    }
  ]
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

### 采购单更新失败

```json
{
  "status": "error",
  "message": "采购单不存在或更新失败"
}
```

### 采购单删除失败

```json
{
  "status": "error",
  "message": "采购单不存在或删除失败"
}
```

### 状态更新失败

```json
{
  "status": "error",
  "message": "采购单不存在或状态更新失败"
}
```

### 数据验证失败

```json
{
  "status": "error",
  "message": "采购单数据验证失败",
  "validation_errors": {
    "supplier_id": ["供应商ID为必填"],
    "items": ["商品明细为必填"]
  }
}
```
