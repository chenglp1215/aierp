# 客户管理 API

客户管理模块提供客户的增删改查、状态管理、认领转移、会员注册、账期额度、订单默认值、导出等功能，以及客户折扣的独立管理。

---

## 1. 创建客户

`POST /api/v1/customers/`

**权限**: `customer.create`

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customer_code | string | 是 | 客户编码，唯一 |
| customer_name | string | 是 | 客户名称 |
| customer_type | string | 否 | 客户类型: `terminal`=终端(默认), `dealer`=经销商 |
| contact_person | string | 否 | 联系人 |
| contact_phone | string | 否 | 联系电话 |
| email | string | 否 | 邮箱 |
| province | string | 否 | 省 |
| city | string | 否 | 市 |
| district | string | 否 | 区 |
| address | string | 否 | 详细地址 |
| settlement_method | int | 否 | 结算方式: 1=月结(默认), 2=现结, 3=预付 |
| remark | string | 否 | 备注 |

**响应**: 返回创建的客户对象

```json
{
  "status": 200,
  "message": "success",
  "result": {
    "id": 1,
    "customer_code": "C001",
    "customer_name": "测试客户",
    "customer_type": "terminal",
    "customer_status": 1,
    "sales_user_id": null,
    "sales_user_name": null,
    "settlement_method": 1,
    "account_balance": 0,
    "debt_total": 0,
    "credit_limit": 0,
    "credit_days": 0,
    "is_overdue": 0,
    "last_order_time": null,
    "total_order_amount": 0,
    "member_account": null,
    "contact_person": "张三",
    "contact_phone": "13800138000",
    "email": null,
    "province": "北京市",
    "city": "北京市",
    "district": "海淀区",
    "address": "中关村大街1号",
    "remark": null,
    "created_by": 1,
    "default_shipping_address_id": null,
    "default_invoice_info_id": null,
    "default_tax_rate": null,
    "created_at": "2026-05-28T10:00:00",
    "updated_at": "2026-05-28T10:00:00"
  }
}
```

---

## 2. 获取客户列表

`GET /api/v1/customers/`

**权限**: `customer.view`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20 |
| keyword | string | 否 | 搜索关键词(匹配编码/名称/联系人/电话) |
| customer_type | string | 否 | 客户类型筛选: `terminal` / `dealer` |
| customer_status | int | 否 | 客户状态筛选: 1=正常, 2=公共池 |

**响应**:

```json
{
  "status": 200,
  "message": "success",
  "result": {
    "items": [
      {
        "id": 1,
        "customer_code": "C001",
        "customer_name": "测试客户",
        "customer_type": "terminal",
        "customer_status": 1,
        "sales_user_id": 1,
        "sales_user_name": "管理员",
        "settlement_method": 1,
        "account_balance": 0,
        "debt_total": 0,
        "credit_limit": 0,
        "credit_days": 0,
        "is_overdue": 0,
        "last_order_time": null,
        "total_order_amount": 0,
        "member_account": null,
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "email": null,
        "province": "北京市",
        "city": "北京市",
        "district": "海淀区",
        "address": "中关村大街1号",
        "remark": null,
        "created_by": 1,
        "default_shipping_address_id": null,
        "default_invoice_info_id": null,
        "default_tax_rate": null,
        "created_at": "2026-05-28T10:00:00",
        "updated_at": "2026-05-28T10:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 3. 获取客户详情

`GET /api/v1/customers/{customer_id}`

**权限**: `customer.view`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**响应**: 返回客户对象（同创建响应结构），额外包含关联数据:

```json
{
  "status": 200,
  "message": "success",
  "result": {
    "id": 1,
    "customer_code": "C001",
    "customer_name": "测试客户",
    "...": "同上",
    "shipping_addresses": [
      {
        "id": 1,
        "customer_id": 1,
        "receiver": "张三",
        "phone": "13800138000",
        "province": "北京市",
        "province_code": "110000",
        "city": "北京市",
        "city_code": "110100",
        "district": "海淀区",
        "address": "中关村大街1号",
        "is_default": true,
        "created_at": "2026-05-28T10:00:00",
        "updated_at": "2026-05-28T10:00:00"
      }
    ],
    "invoice_infos": [
      {
        "id": 1,
        "customer_id": 1,
        "invoice_title": "XX科技有限公司",
        "tax_number": "91110000XXXXXXXX",
        "bank_name": "中国工商银行",
        "bank_account": "0200001234567890",
        "address_phone": "北京市海淀区/010-12345678",
        "is_default": true,
        "created_at": "2026-05-28T10:00:00",
        "updated_at": "2026-05-28T10:00:00"
      }
    ],
    "research_groups": [
      {
        "id": 1,
        "customer_id": 1,
        "research_group_name": "XX课题组",
        "research_leader": "李教授",
        "contact_phone": "010-87654321",
        "created_at": "2026-05-28T10:00:00"
      }
    ],
    "discounts": [
      {
        "id": 1,
        "customer_id": 1,
        "brand_id": 1,
        "brand_name": "品牌A",
        "discount_value": 0.95,
        "is_active": true,
        "created_at": "2026-05-28T10:00:00",
        "updated_at": "2026-05-28T10:00:00"
      }
    ]
  }
}
```

---

## 4. 更新客户

`PUT /api/v1/customers/{customer_id}`

**权限**: `customer.edit`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**请求体**: 同创建客户，所有字段均为可选，只传需要更新的字段。

**响应**: 返回更新后的客户对象

---

## 5. 删除客户

`DELETE /api/v1/customers/{customer_id}`

**权限**: `customer.delete`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**响应**:

```json
{
  "status": 200,
  "message": "客户删除成功",
  "result": null
}
```

---

## 6. 获取客户统计

`GET /api/v1/customers/stats`

**权限**: `customer.stats`

**响应**:

```json
{
  "status": 200,
  "message": "success",
  "result": {
    "total": 100,
    "normal": 85,
    "public_pool": 15,
    "terminal": 70,
    "dealer": 30,
    "overdue": 5
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| total | int | 客户总数 |
| normal | int | 正常状态客户数 |
| public_pool | int | 公共池客户数 |
| terminal | int | 终端客户数 |
| dealer | int | 经销商客户数 |
| overdue | int | 超账期客户数 |

---

## 7. 更新客户状态

`PATCH /api/v1/customers/{customer_id}/status`

**权限**: `customer.status`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customer_status | int | 是 | 目标状态: 1=正常, 2=公共池 |

**响应**: 返回更新后的客户对象

---

## 8. 客户认领

`POST /api/v1/customers/{customer_id}/claim`

**权限**: `customer.claim`

将公共池客户认领到当前用户名下。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**响应**: 返回更新后的客户对象

---

## 9. 客户转移

`PATCH /api/v1/customers/{customer_id}/transfer`

**权限**: `customer.transfer`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| new_user_id | int | 是 | 目标业务员用户ID |

**响应**: 返回更新后的客户对象

---

## 10. 注册会员账号

`PUT /api/v1/customers/{customer_id}/member-account`

**权限**: `customer.member`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| member_account | string | 是 | 会员账号 |

**响应**: 返回更新后的客户对象

---

## 11. 设置订单默认值

`PUT /api/v1/customers/{customer_id}/order-defaults`

**权限**: `customer.order-defaults`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| settlement_method | int | 否 | 结算方式: 1=月结, 2=现结, 3=预付 |
| default_tax_rate | float | 否 | 默认税率(百分比, 如 13.00 表示 13%) |
| default_shipping_address_id | int | 否 | 默认收货地址ID |
| default_invoice_info_id | int | 否 | 默认开票信息ID |

**响应**: 返回更新后的客户对象

---

## 12. 设置账期额度

`PUT /api/v1/customers/{customer_id}/credit`

**权限**: `customer.credit`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| customer_id | int | 客户ID |

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| credit_days | int | 是 | 账期天数 |
| credit_limit | float | 是 | 信用额度 |

**响应**: 返回更新后的客户对象

---

## 13. 批量超账期检查

`GET /api/v1/customers/check-overdue`

**权限**: `customer.check-overdue`

检查所有设置了账期的客户是否超期，自动更新 `is_overdue` 标记。

**响应**:

```json
{
  "status": 200,
  "message": "success",
  "result": {
    "checked": 50,
    "overdue_count": 5,
    "overdue_customers": [
      {
        "id": 1,
        "customer_name": "XX公司",
        "credit_days": 30,
        "credit_limit": 50000,
        "debt_total": 30000,
        "last_order_time": "2026-04-15T10:00:00"
      }
    ]
  }
}
```

---

## 14. 导出客户

`POST /api/v1/customers/export`

**权限**: `customer.export`

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customer_ids | int[] | 否 | 指定导出的客户ID列表，为空则导出全部 |

**响应**: 二进制 Excel 文件

- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename=customers_YYYYMMDD_HHMMSS.xlsx`

---

## 15. 收货地址管理

### 15.1 创建收货地址

`POST /api/v1/customers/{customer_id}/shipping-addresses`

**权限**: `customer.edit`

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| receiver | string | 是 | 收货人 |
| phone | string | 是 | 联系电话 |
| province | string | 是 | 省份 |
| province_code | string | 否 | 省份代码 |
| city | string | 是 | 城市 |
| city_code | string | 否 | 城市代码 |
| district | string | 否 | 区县 |
| address | string | 是 | 详细地址 |
| is_default | bool | 否 | 是否默认，默认 false |

**响应**: 返回创建的收货地址对象

### 15.2 更新收货地址

`PUT /api/v1/customers/{customer_id}/shipping-addresses/{address_id}`

**权限**: `customer.edit`

**请求体**: 同创建，所有字段可选。

**响应**: 返回更新后的收货地址对象

### 15.3 删除收货地址

`DELETE /api/v1/customers/{customer_id}/shipping-addresses/{address_id}`

**权限**: `customer.edit`

**响应**:

```json
{
  "status": 200,
  "message": "收货地址删除成功",
  "result": null
}
```

---

## 16. 开票信息管理

### 16.1 创建开票信息

`POST /api/v1/customers/{customer_id}/invoice-infos`

**权限**: `customer.edit`

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| invoice_title | string | 是 | 开票抬头 |
| tax_number | string | 是 | 税务编码 |
| bank_name | string | 是 | 银行开户行 |
| bank_account | string | 是 | 银行账号 |
| address_phone | string | 否 | 地址、电话 |
| is_default | bool | 否 | 是否默认，默认 false |

**响应**: 返回创建的开票信息对象

### 16.2 更新开票信息

`PUT /api/v1/customers/{customer_id}/invoice-infos/{invoice_id}`

**权限**: `customer.edit`

**请求体**: 同创建，所有字段可选。

**响应**: 返回更新后的开票信息对象

### 16.3 删除开票信息

`DELETE /api/v1/customers/{customer_id}/invoice-infos/{invoice_id}`

**权限**: `customer.edit`

**响应**:

```json
{
  "status": 200,
  "message": "开票信息删除成功",
  "result": null
}
```

---

## 17. 课题组管理

### 17.1 创建课题组

`POST /api/v1/customers/{customer_id}/research-groups`

**权限**: `customer.edit`

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| research_group_name | string | 是 | 课题组名称 |
| research_leader | string | 否 | 课题组负责人 |
| contact_phone | string | 否 | 联系电话 |

**响应**: 返回创建的课题组对象

### 17.2 更新课题组

`PUT /api/v1/customers/{customer_id}/research-groups/{group_id}`

**权限**: `customer.edit`

**请求体**: 同创建，所有字段可选。

**响应**: 返回更新后的课题组对象

### 17.3 删除课题组

`DELETE /api/v1/customers/{customer_id}/research-groups/{group_id}`

**权限**: `customer.edit`

**响应**:

```json
{
  "status": 200,
  "message": "课题组删除成功",
  "result": null
}
```

---

## 18. 客户折扣管理

折扣管理通过独立的路由前缀 `/api/v1/customer-discounts/` 提供服务。

### 18.1 创建客户折扣

`POST /api/v1/customer-discounts/`

**权限**: `customer-discount.create`

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customer_id | int | 是 | 客户ID |
| brand_id | int | 是 | 品牌ID |
| brand_name | string | 否 | 品牌名称 |
| discount_value | float | 是 | 折扣值(如 0.95 表示 95 折) |

**响应**: 返回创建的折扣对象

```json
{
  "status": 200,
  "message": "success",
  "result": {
    "id": 1,
    "customer_id": 1,
    "brand_id": 1,
    "brand_name": "品牌A",
    "discount_value": 0.95,
    "is_active": true,
    "created_at": "2026-05-28T10:00:00",
    "updated_at": "2026-05-28T10:00:00"
  }
}
```

**约束**: 同一客户同一品牌只能有一个折扣记录（`customer_id` + `brand_id` 唯一）。

### 18.2 获取折扣列表

`GET /api/v1/customer-discounts/`

**权限**: `customer-discount.view`

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customer_id | int | 否 | 按客户ID筛选 |
| brand_id | int | 否 | 按品牌ID筛选 |
| is_active | bool | 否 | 按生效状态筛选 |

**响应**:

```json
{
  "status": 200,
  "message": "success",
  "result": [
    {
      "id": 1,
      "customer_id": 1,
      "brand_id": 1,
      "brand_name": "品牌A",
      "discount_value": 0.95,
      "is_active": true,
      "created_at": "2026-05-28T10:00:00",
      "updated_at": "2026-05-28T10:00:00"
    }
  ]
}
```

### 18.3 更新折扣

`PUT /api/v1/customer-discounts/{discount_id}`

**权限**: `customer-discount.edit`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| discount_id | int | 折扣ID |

**请求体**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| discount_value | float | 否 | 折扣值 |
| brand_name | string | 否 | 品牌名称 |

**响应**: 返回更新后的折扣对象

### 18.4 切换折扣状态

`PATCH /api/v1/customer-discounts/{discount_id}/status`

**权限**: `customer-discount.edit`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| discount_id | int | 折扣ID |

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | bool | 是 | 是否生效: `true` / `false` |

**响应**: 返回更新后的折扣对象

### 18.5 删除折扣

`DELETE /api/v1/customer-discounts/{discount_id}`

**权限**: `customer-discount.delete`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| discount_id | int | 折扣ID |

**响应**:

```json
{
  "status": 200,
  "message": "折扣删除成功",
  "result": null
}
```

---

## 通用说明

### 统一响应格式

所有接口均返回统一的 JSON 格式:

```json
{
  "status": 200,
  "message": "success",
  "result": {},
  "exc": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | int | 状态码，200 表示成功 |
| message | string | 消息描述 |
| result | any | 业务数据 |
| exc | string \| null | 异常信息 |

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证（token 缺失或过期） |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

### 认证方式

所有接口需要在请求头中携带 Bearer Token:

```
Authorization: Bearer <access_token>
```

通过 `POST /api/v1/auth/login` 获取 token。

### 枚举值速查

**客户类型** (`customer_type`):

| 值 | 说明 |
|----|------|
| terminal | 终端客户 |
| dealer | 经销商 |

**客户状态** (`customer_status`):

| 值 | 说明 |
|----|------|
| 1 | 正常 |
| 2 | 公共池 |

**结算方式** (`settlement_method`):

| 值 | 说明 |
|----|------|
| 1 | 月结 |
| 2 | 现结 |
| 3 | 预付 |

**是否超账期** (`is_overdue`):

| 值 | 说明 |
|----|------|
| 0 | 否 |
| 1 | 是 |
