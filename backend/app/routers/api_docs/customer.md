# 客户管理 API

> 全新设计的客户管理接口，含客户折扣管理

## 基础信息

- **客户管理基础路径**: `/api/v1/customers`
- **客户折扣管理基础路径**: `/api/v1/customer-discounts`
- **认证方式**: Bearer Token (JWT)
- **权限说明**: 需要携带有效 Token 访问

---

## 目录

### 客户管理

- [创建客户](#51-创建客户)
- [获取客户列表](#52-获取客户列表)
- [获取客户统计](#53-获取客户统计)
- [获取客户详情](#54-获取客户详情)
- [更新客户](#55-更新客户)
- [删除客户](#56-删除客户)
- [更新客户状态](#57-更新客户状态)
- [转移客户](#58-转移客户)

### 客户折扣管理

- [创建客户折扣](#61-创建客户折扣)
- [获取客户折扣列表](#62-获取客户折扣列表)
- [获取客户折扣详情](#63-获取客户折扣详情)
- [按客户和品牌获取折扣](#64-按客户和品牌获取折扣)
- [更新客户折扣](#65-更新客户折扣)
- [删除客户折扣](#66-删除客户折扣)
- [切换客户折扣状态](#67-切换客户折扣状态)

---

## 5.1 创建客户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/customers/` |
| **Method** | POST |
| **权限** | `customer.create` |

### 请求头

```
Authorization: Bearer <token>
Content-Type: application/json
```

### 请求体

```json
{
  "name": "string",
  "customer_type": "terminal|dealer",
  "research_group": "string",
  "contact_person": "string",
  "contact_phone": "string",
  "contact_email": "string",
  "invoice_infos": [
    {
      "invoice_title": "string",
      "invoice_type": "增值税|普通发票|增值税专用发票|不开票",
      "tax_number": "string",
      "bank_name": "string",
      "bank_account": "string",
      "is_default": false
    }
  ],
  "shipping_addresses": [
    {
      "recipient_name": "string",
      "recipient_phone": "string",
      "province": "string",
      "city": "string",
      "address": "string",
      "is_default": false
    }
  ]
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 客户名称 |
| customer_type | string | 是 | 客户类型：`terminal`(终端客户) / `dealer`(经销商) |
| research_group | string | 条件 | 课题组信息，仅 `terminal` 类型必填 |
| contact_person | string | 否 | 联系人姓名 |
| contact_phone | string | 否 | 联系人电话 |
| contact_email | string | 否 | 联系人邮箱 |
| invoice_infos | array | 否 | 开票信息列表，可在创建时一并添加 |
| shipping_addresses | array | 否 | 收货地址列表，可在创建时一并添加 |

**说明**:
- `customer_code` 由系统自动生成，格式：`CUST{日期}{4位随机数}`
- `sales_user_id` 和 `sales_user_name` 由系统自动设置为当前登录用户

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": 1,
    "customer_code": "CUST202605111234",
    "name": "某医院检验科",
    "customer_type": "terminal",
    "research_group": "检验科课题组",
    "contact_person": "张三",
    "contact_phone": "13800138000",
    "contact_email": "zhangsan@example.com",
    "invoice_infos": [],
    "shipping_addresses": [],
    "sales_user_id": "user123",
    "sales_user_name": "李经理",
    "status": "normal",
    "created_at": "2026-05-11T10:30:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  }
}
```

**错误响应（验证失败）**:
```json
{
  "status": "error",
  "message": "参数验证失败",
  "validation_errors": [
    {
      "field": "name",
      "message": "客户名称为必填"
    }
  ]
}
```

---

## 5.2 获取客户列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers/` |
| **Method** | GET |
| **权限** | `customer.view` |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| status | string | 否 | - | 客户状态：`normal` / `inactive` / `blacklisted` |
| customer_type | string | 否 | - | 客户类型：`terminal` / `dealer` |
| sales_user_id | string | 否 | - | 销售人ID |
| keyword | string | 否 | - | 搜索关键词（客户名称、客户编码） |

### 请求示例

```
GET /api/v1/customers/?page=1&page_size=20&customer_type=terminal
```

### 响应

**成功响应**:
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
        "customer_code": "CUST202605110001",
        "name": "某医院检验科",
        "customer_type": "terminal",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "status": "normal",
        "sales_user_name": "李经理",
        "created_at": "2026-05-11T10:30:00Z",
        "updated_at": "2026-05-11T10:30:00Z"
      }
    ]
  }
}
```

---

## 5.3 获取客户统计

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers/stats` |
| **Method** | GET |
| **权限** | `customer.view` |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 100,
    "terminal_count": 80,
    "dealer_count": 20
  }
}
```

---

## 5.4 获取客户详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers/{customer_id}` |
| **Method** | GET |
| **权限** | `customer.view` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": 1,
    "customer_code": "CUST202605110001",
    "name": "某医院检验科",
    "customer_type": "terminal",
    "research_group": "检验科课题组",
    "contact_person": "张三",
    "contact_phone": "13800138000",
    "contact_email": "zhangsan@example.com",
    "invoice_infos": [
      {
        "id": 1,
        "invoice_title": "某医院",
        "invoice_type": "增值税",
        "tax_number": "91110000000000000X",
        "bank_name": "中国工商银行",
        "bank_account": "6222021234567890",
        "is_default": true
      }
    ],
    "shipping_addresses": [
      {
        "id": 1,
        "recipient_name": "张三",
        "recipient_phone": "13800138000",
        "province": "北京市",
        "city": "北京市",
        "address": "某街道某号",
        "is_default": true
      }
    ],
    "sales_user_id": "user123",
    "sales_user_name": "李经理",
    "status": "normal",
    "created_at": "2026-05-11T10:30:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  }
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在",
  "result": null
}
```

---

## 5.5 更新客户

> 通过 PUT 更新客户时，可以一并更新开票信息和收货地址

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/customers/{customer_id}` |
| **Method** | PUT |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

```json
{
  "name": "string",
  "customer_type": "terminal|dealer",
  "research_group": "string",
  "contact_person": "string",
  "contact_phone": "string",
  "contact_email": "string",
  "invoice_infos": [
    {
      "id": 1,
      "invoice_title": "string",
      "invoice_type": "增值税|普通发票|增值税专用发票|不开票",
      "tax_number": "string",
      "bank_name": "string",
      "bank_account": "string",
      "is_default": false
    }
  ],
  "shipping_addresses": [
    {
      "id": 1,
      "recipient_name": "string",
      "recipient_phone": "string",
      "province": "string",
      "city": "string",
      "address": "string",
      "is_default": false
    }
  ]
}
```

**说明**:
- 支持部分更新，只发送需要更新的字段
- `invoice_infos` 和 `shipping_addresses` 会整体替换现有数据
- 如需单独添加/删除/更新某个地址，请使用完整的数组替换

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户更新成功",
  "result": null
}
```

---

## 5.6 删除客户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/customers/{customer_id}` |
| **Method** | DELETE |
| **权限** | `customer.delete` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户删除成功",
  "result": null
}
```

---

## 5.7 更新客户状态

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/customers/{customer_id}/status` |
| **Method** | PATCH |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

```json
{
  "status": "normal"
}
```

**status 可选值**:
| 值 | 描述 |
|-----|------|
| normal | 正常 |
| inactive | 停用 |
| blacklisted | 黑名单 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户状态更新成功",
  "result": null
}
```

---

## 5.8 转移客户

> 将属于自己的客户转移给其他销售员

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/customers/{customer_id}/transfer` |
| **Method** | PATCH |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

```json
{
  "new_user_id": "string"
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户转移成功",
  "result": null
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "目标销售不存在或客户转移失败",
  "result": null
}
```

### 业务规则

1. **权限控制**：只有客户当前负责人才能转移，`super_admin` 角色可以转移任何客户
2. **数据更新**：`sales_user_id` 和 `sales_user_name` 更新为目标销售员信息

---

## 客户折扣管理

> 客户折扣独立路由，前缀为 `/api/v1/customer-discounts`

---

## 6.1 创建客户折扣

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/customer-discounts/` |
| **Method** | POST |
| **权限** | `customer_discount.create` |

### 请求体

```json
{
  "customer_id": "string",
  "brand_id": "string",
  "discount_value": 0.85,
  "is_active": true
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| brand_id | string | 是 | 品牌ID |
| discount_value | float | 是 | 折扣值（0-1之间，如0.85表示85折） |
| is_active | boolean | 否 | 是否生效，默认true |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": 1,
    "customer_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "brand_id": "brand001",
    "brand_name": "品牌A",
    "discount_value": 0.85,
    "is_active": true,
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-01T10:00:00Z"
  }
}
```

**错误响应（重复配置）**:
```json
{
  "status": "error",
  "message": "该客户和品牌的折扣配置已存在",
  "result": null
}
```

---

## 6.2 获取客户折扣列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customer-discounts/` |
| **Method** | GET |
| **权限** | `customer_discount.view` |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| customer_id | string | 否 | - | 客户ID |
| brand_id | string | 否 | - | 品牌ID |
| is_active | boolean | 否 | - | 是否生效 |

### 响应

**成功响应**:
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
        "customer_id": "64a1b2c3d4e5f6a7b8c9d0e1",
        "brand_id": "brand001",
        "brand_name": "品牌A",
        "discount_value": 0.85,
        "is_active": true,
        "created_at": "2026-05-01T10:00:00Z",
        "updated_at": "2026-05-01T10:00:00Z"
      }
    ]
  }
}
```

---

## 6.3 获取客户折扣详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customer-discounts/{discount_id}` |
| **Method** | GET |
| **权限** | `customer_discount.view` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| discount_id | string | 是 | 折扣记录ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": 1,
    "customer_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "brand_id": "brand001",
    "brand_name": "品牌A",
    "discount_value": 0.85,
    "is_active": true,
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-01T10:00:00Z"
  }
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户折扣不存在",
  "result": null
}
```

---

## 6.4 按客户和品牌获取折扣

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customer-discounts/customer/{customer_id}/brand/{brand_id}` |
| **Method** | GET |
| **权限** | `customer_discount.view` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| brand_id | string | 是 | 品牌ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": 1,
    "customer_id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "brand_id": "brand001",
    "brand_name": "品牌A",
    "discount_value": 0.85,
    "is_active": true,
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-01T10:00:00Z"
  }
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "该客户和品牌的折扣配置不存在",
  "result": null
}
```

---

## 6.5 更新客户折扣

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/customer-discounts/{discount_id}` |
| **Method** | PUT |
| **权限** | `customer_discount.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| discount_id | string | 是 | 折扣记录ID |

### 请求体

```json
{
  "discount_value": 0.8,
  "is_active": false
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户折扣更新成功",
  "result": null
}
```

---

## 6.6 删除客户折扣

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/customer-discounts/{discount_id}` |
| **Method** | DELETE |
| **权限** | `customer_discount.delete` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| discount_id | string | 是 | 折扣记录ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户折扣删除成功",
  "result": null
}
```

---

## 6.7 切换客户折扣状态

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/customer-discounts/{discount_id}/status` |
| **Method** | PATCH |
| **权限** | `customer_discount.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| discount_id | string | 是 | 折扣记录ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_active | boolean | 是 | 是否生效 |

### 请求示例

```
PATCH /api/v1/customer-discounts/DIS001/status?is_active=false
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户折扣状态更新成功",
  "result": null
}
```

---

## 数据结构

### 客户 (Customer)

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 否 | 客户ID（创建时由系统自动生成） |
| customer_code | string | 是 | 客户编码（系统自动生成，格式：`CUST{日期}{4位随机数}`） |
| name | string | 是 | 客户名称 |
| customer_type | string | 是 | 客户类型：`terminal`(终端) / `dealer`(经销商) |
| research_group | string | 条件 | 课题组信息（终端客户时必填） |
| contact_person | string | 否 | 联系人姓名 |
| contact_phone | string | 否 | 联系人电话 |
| contact_email | string | 否 | 联系人邮箱 |
| sales_user_id | string | 否 | 销售负责人ID（系统自动设置） |
| sales_user_name | string | 否 | 销售负责人姓名（系统自动设置） |
| status | string | 否 | 客户状态：`normal` / `inactive` / `blacklisted` |
| invoice_infos | array | 否 | 开票信息列表 |
| shipping_addresses | array | 否 | 收货地址列表 |
| created_at | datetime | 否 | 创建时间 |
| updated_at | datetime | 否 | 更新时间 |

### 开票信息 (InvoiceInfo)

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 否 | 开票信息ID（更新时需提供） |
| invoice_title | string | 是 | 开票抬头 |
| invoice_type | string | 是 | 开票类型：`增值税` / `普通发票` / `增值税专用发票` / `不开票` |
| tax_number | string | 是 | 税务登记号 |
| bank_name | string | 是 | 开户银行 |
| bank_account | string | 是 | 银行账号 |
| is_default | boolean | 否 | 是否默认（默认 false） |

### 收货地址 (ShippingAddress)

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 否 | 地址ID（更新时需提供） |
| recipient_name | string | 是 | 收货人姓名 |
| recipient_phone | string | 是 | 收货人电话 |
| province | string | 是 | 省份 |
| city | string | 是 | 城市 |
| address | string | 是 | 详细地址 |
| is_default | boolean | 否 | 是否默认（默认 false） |

### 客户折扣 (CustomerDiscount)

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | integer | 否 | 折扣记录ID（系统自动生成） |
| customer_id | string | 是 | 客户ID |
| brand_id | string | 是 | 品牌ID |
| brand_name | string | 否 | 品牌名称 |
| discount_value | float | 是 | 折扣值（0-1之间，如0.85表示85折） |
| is_active | boolean | 否 | 是否生效（默认 true） |
| created_at | datetime | 否 | 创建时间 |
| updated_at | datetime | 否 | 更新时间 |

---

## 权限代码

| 权限 | 描述 |
|------|------|
| customer.view | 查看客户 |
| customer.create | 创建客户 |
| customer.edit | 编辑客户 |
| customer.delete | 删除客户 |
| customer_discount.view | 查看客户折扣 |
| customer_discount.create | 创建客户折扣 |
| customer_discount.edit | 编辑客户折扣 |
| customer_discount.delete | 删除客户折扣 |

---

## 变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-05-11 | 重构客户管理模块，移除独立的开票/收货地址CRUD接口，改为在客户create/update时整体处理 |
| 2026-05-11 | 客户折扣管理合并到客户模块 |
