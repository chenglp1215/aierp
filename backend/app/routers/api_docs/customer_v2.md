# 客户管理 API v2

> **推荐使用此版本** - 新版客户管理接口

## 基础信息

- **基础路径**: `/api/v1/customers-v2`
- **认证方式**: Bearer Token (JWT)
- **权限说明**: 需要携带有效 Token 访问

---

## 5.2.1 创建客户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/customers-v2/` |
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
  "name": "string",                    // 必填，客户名称
  "customer_type": "terminal|dealer",   // 必填，客户类型
  "research_group": "string",          // 课题组信息（终端客户时必填）
  "contact_info": {                     // 联系人信息
    "contact_person": "string",        // 联系人姓名
    "contact_phone": "string",          // 联系电话
    "contact_email": "string"           // 电子邮箱
  },
  "invoice_infos": [                    // 开票信息列表
    {
      "invoice_title": "string",        // 开票抬头（必填）
      "tax_number": "string",           // 税号（必填）
      "bank_name": "string",            // 开户行（必填）
      "bank_account": "string",         // 银行账号（必填）
      "is_default": false               // 是否默认
    }
  ],
  "shipping_addresses": [               // 收货地址列表
    {
      "recipient_name": "string",       // 收货人（必填）
      "recipient_phone": "string",      // 收货电话（必填）
      "province": "string",             // 收货省份（必填）
      "province_code": "string",        // 省份代码
      "city": "string",                // 城市（必填）
      "city_code": "string",           // 城市代码
      "district": "string",            // 区县
      "address": "string",             // 详细地址（必填）
      "is_default": false              // 是否默认
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
| contact_info | object | 否 | 联系人信息 |
| contact_info.contact_person | string | 否 | 联系人姓名 |
| contact_info.contact_phone | string | 否 | 联系人电话 |
| contact_info.contact_email | string | 否 | 联系人邮箱 |
| invoice_infos | array | 否 | 开票信息列表 |
| shipping_addresses | array | 否 | 收货地址列表 |

**说明**: `sales_user_id` 和 `sales_user_name` 由系统自动设置为当前登录用户，无需传入。

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户创建成功",
  "result": {
    "id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "customer_code": "C2024010001",
    "name": "某医院检验科",
    "customer_type": "terminal",
    "research_group": "检验科课题组",
    "contact_info": {
      "contact_person": "张三",
      "contact_phone": "13800138000",
      "contact_email": "zhangsan@example.com"
    },
    "invoice_infos": [],
    "shipping_addresses": [],
    "sales_user_id": "user123",
    "sales_user_name": "李经理",
    "status": "normal",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**错误响应（验证失败）**:
```json
{
  "status": "error",
  "message": "客户创建参数验证失败",
  "result": null,
  "validation_errors": [
    {
      "field": "name",
      "message": "客户名称为必填"
    }
  ]
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 客户ID（MongoDB ObjectId） |
| customer_code | string | 客户编码（自动生成） |
| name | string | 客户名称 |
| customer_type | string | 客户类型 |
| research_group | string | 课题组信息 |
| contact_info | object | 联系人信息 |
| invoice_infos | array | 开票信息列表 |
| shipping_addresses | array | 收货地址列表 |
| sales_user_id | string | 销售负责人ID（系统自动设置） |
| sales_user_name | string | 销售负责人姓名（系统自动设置） |
| status | string | 状态：`normal`(正常) / `inactive`(停用) / `blacklisted`(黑名单) |
| is_active | boolean | 是否启用 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 5.2.2 获取客户列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers-v2/` |
| **Method** | GET |
| **权限** | `customer.view` |

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| status | string | 否 | - | 客户状态：`normal` / `inactive` / `blacklisted` |
| customer_type | string | 否 | - | 客户类型：`terminal` / `dealer` |
| sales_user_id | string | 否 | - | 销售人ID |
| keyword | string | 否 | - | 搜索关键词（客户名称、客户编码、联系电话） |

### 请求示例

```
GET /api/v1/customers-v2/?page=1&page_size=20&customer_type=terminal
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取客户列表成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "64a1b2c3d4e5f6a7b8c9d0e1",
        "customer_code": "C2024010001",
        "name": "某医院检验科",
        "customer_type": "terminal",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "status": "normal",
        "sales_user_name": "李经理",
        "invoice_count": 2,
        "shipping_address_count": 1,
        "default_shipping_address": {
          "province": "北京市",
          "city": "市辖区",
          "district": "朝阳区",
          "address": "某街道某号",
          "contact_person": "张三",
          "contact_phone": "13800138000",
          "is_default": true
        },
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result.total | int | 满足条件的总记录数 |
| result.page | int | 当前页码 |
| result.page_size | int | 每页记录数 |
| result.items | array | 客户列表 |
| result.items[].id | string | 客户ID |
| result.items[].customer_code | string | 客户编码 |
| result.items[].name | string | 客户名称 |
| result.items[].customer_type | string | 客户类型 |
| result.items[].contact_person | string | 联系人姓名 |
| result.items[].contact_phone | string | 联系电话 |
| result.items[].status | string | 状态 |
| result.items[].sales_user_name | string | 销售负责人姓名 |
| result.items[].invoice_count | integer | 发票数量 |
| result.items[].shipping_address_count | integer | 收货地址数量 |
| result.items[].default_shipping_address | object | 默认收货地址（对象，包含 province/city/district/address/contact_person/contact_phone/is_default 字段） |
| result.items[].created_at | datetime | 创建时间 |
| result.items[].updated_at | datetime | 更新时间 |

---

## 5.2.3 获取客户统计

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers-v2/stats` |
| **Method** | GET |
| **权限** | `customer.view` |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取客户统计成功",
  "result": {
    "total": 100,
    "terminal_count": 80,
    "dealer_count": 20
  }
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result.total | int | 客户总数 |
| result.terminal_count | int | 终端客户数 |
| result.dealer_count | int | 经销商客户数 |

---

## 5.2.4 搜索客户

> 用于下拉选择等场景，快速搜索客户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers-v2/search` |
| **Method** | GET |
| **权限** | `customer.view` |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词 |
| limit | int | 否 | 10 | 返回数量（最大50） |

### 请求示例

```
GET /api/v1/customers-v2/search?keyword=医院&limit=5
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "搜索客户成功",
  "result": [
    {
      "id": "64a1b2c3d4e5f6a7b8c9d0e1",
      "name": "某医院检验科",
      "customer_type": "terminal",
      "contact_phone": "13800138000"
    }
  ]
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result | array | 客户列表 |
| result[].id | string | 客户ID |
| result[].name | string | 客户名称 |
| result[].customer_type | string | 客户类型 |
| result[].contact_phone | string | 联系电话 |

---

## 5.2.5 获取客户详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers-v2/{customer_id}` |
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
  "message": "获取客户详情成功",
  "result": {
    "id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "customer_code": "C2024010001",
    "name": "某医院检验科",
    "customer_type": "terminal",
    "research_group": "检验科课题组",
    "contact_info": {
      "contact_person": "张三",
      "contact_phone": "13800138000",
      "contact_email": "zhangsan@example.com"
    },
    "invoice_infos": [
      {
        "id": "inv001",
        "invoice_title": "某医院",
        "tax_number": "91110000000000000X",
        "bank_name": "中国工商银行",
        "bank_account": "6222021234567890",
        "is_default": true
      }
    ],
    "shipping_addresses": [
      {
        "id": "addr001",
        "recipient_name": "张三",
        "recipient_phone": "13800138000",
        "province": "北京市",
        "province_code": "110000",
        "city": "北京市",
        "city_code": "11010001",
        "district": "东城区",
        "address": "某街道某号",
        "is_default": true
      }
    ],
    "sales_user_id": "user123",
    "sales_user_name": "李经理",
    "status": "normal",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
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

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result | object | 客户完整信息 |
| result.id | string | 客户ID |
| result.customer_code | string | 客户编码 |
| result.name | string | 客户名称 |
| result.customer_type | string | 客户类型 |
| result.research_group | string | 课题组信息 |
| result.contact_info | object | 联系人信息 |
| result.invoice_infos | array | 开票信息列表 |
| result.shipping_addresses | array | 收货地址列表 |
| result.sales_user_id | string | 销售负责人ID |
| result.sales_user_name | string | 销售负责人姓名 |
| result.status | string | 客户状态 |
| result.is_active | boolean | 是否启用 |
| result.created_at | datetime | 创建时间 |
| result.updated_at | datetime | 更新时间 |

**开票信息字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| invoice_infos[].id | string | 开票信息ID |
| invoice_infos[].invoice_title | string | 开票抬头 |
| invoice_infos[].tax_number | string | 税务登记号 |
| invoice_infos[].bank_name | string | 开户银行 |
| invoice_infos[].bank_account | string | 银行账号 |
| invoice_infos[].is_default | boolean | 是否默认 |

**收货地址字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| shipping_addresses[].id | string | 地址ID |
| shipping_addresses[].recipient_name | string | 收货人姓名 |
| shipping_addresses[].recipient_phone | string | 收货人电话 |
| shipping_addresses[].province | string | 省份 |
| shipping_addresses[].province_code | string | 省份代码 |
| shipping_addresses[].city | string | 城市 |
| shipping_addresses[].city_code | string | 城市代码 |
| shipping_addresses[].district | string | 区县 |
| shipping_addresses[].address | string | 详细地址 |
| shipping_addresses[].is_default | boolean | 是否默认 |

---

## 5.2.6 更新客户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/customers-v2/{customer_id}` |
| **Method** | PUT |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

同创建客户，可部分更新。只发送需要更新的字段。

```json
{
  "name": "string",
  "customer_type": "terminal|dealer",
  "research_group": "string",
  "contact_info": {},
  "invoice_infos": [],
  "shipping_addresses": []
}
```

**说明**: `sales_user_id` 和 `sales_user_name` 由系统自动设置为当前登录用户，无需传入。

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户更新成功"
}
```

**错误响应（验证失败）**:
```json
{
  "status": "error",
  "message": "客户更新参数验证失败",
  "result": null,
  "validation_errors": [
    {
      "field": "name",
      "message": "客户名称为必填"
    }
  ]
}
```

**错误响应（客户不存在）**:
```json
{
  "status": "error",
  "message": "客户不存在或更新失败",
  "result": null
}
```

---

## 5.2.7 删除客户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/customers-v2/{customer_id}` |
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
  "message": "客户删除成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或删除失败",
  "result": null
}
```

---

## 5.2.8 更新客户状态

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/customers-v2/{customer_id}/status` |
| **Method** | PATCH |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

```json
{
  "status": "normal|inactive|blacklisted"
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
  "message": "客户状态更新成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或状态更新失败",
  "result": null
}
```

---

## 5.2.9 更新联系人信息

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/customers-v2/{customer_id}/contact-info` |
| **Method** | PUT |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

```json
{
  "contact_person": "string",
  "contact_phone": "string",
  "contact_email": "string"
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "联系人信息更新成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或更新失败",
  "result": null
}
```

---

## 5.2.10 添加开票信息

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/customers-v2/{customer_id}/invoice-infos` |
| **Method** | POST |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

```json
{
  "invoice_title": "string",   // 必填，开票抬头
  "tax_number": "string",      // 必填，税号
  "bank_name": "string",       // 必填，开户行
  "bank_account": "string",    // 必填，银行账号
  "is_default": false          // 是否默认
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "开票信息添加成功",
  "result": {
    "id": "inv001",
    "invoice_title": "某医院",
    "tax_number": "91110000000000000X",
    "bank_name": "中国工商银行",
    "bank_account": "6222021234567890",
    "is_default": true
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

## 5.2.11 更新开票信息

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/customers-v2/{customer_id}/invoice-infos/{invoice_id}` |
| **Method** | PUT |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| invoice_id | string | 是 | 开票信息ID |

### 请求体

```json
{
  "invoice_title": "string",
  "tax_number": "string",
  "bank_name": "string",
  "bank_account": "string",
  "is_default": false
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "开票信息更新成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或开票信息不存在",
  "result": null
}
```

---

## 5.2.12 删除开票信息

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/customers-v2/{customer_id}/invoice-infos/{invoice_id}` |
| **Method** | DELETE |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| invoice_id | string | 是 | 开票信息ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "开票信息删除成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或开票信息不存在",
  "result": null
}
```

---

## 5.2.13 设置默认开票信息

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/customers-v2/{customer_id}/invoice-infos/{invoice_id}/default` |
| **Method** | PATCH |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| invoice_id | string | 是 | 开票信息ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "默认开票信息设置成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或开票信息不存在",
  "result": null
}
```

---

## 5.2.14 添加收货地址

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/customers-v2/{customer_id}/shipping-addresses` |
| **Method** | POST |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求体

```json
{
  "recipient_name": "string",    // 必填，收货人
  "recipient_phone": "string",   // 必填，收货电话
  "province": "string",          // 必填，省份
  "province_code": "string",     // 省份代码
  "city": "string",              // 必填，城市
  "city_code": "string",         // 城市代码
  "district": "string",          // 区县
  "address": "string",           // 必填，详细地址
  "is_default": false            // 是否默认
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "收货地址添加成功",
  "result": {
    "id": "addr001",
    "recipient_name": "张三",
    "recipient_phone": "13800138000",
    "province": "北京市",
    "province_code": "110000",
    "city": "北京市",
    "city_code": "11010001",
    "district": "东城区",
    "address": "某街道某号",
    "is_default": true
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

## 5.2.15 更新收货地址

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/customers-v2/{customer_id}/shipping-addresses/{address_id}` |
| **Method** | PUT |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| address_id | string | 是 | 收货地址ID |

### 请求体

```json
{
  "recipient_name": "string",
  "recipient_phone": "string",
  "province": "string",
  "province_code": "string",
  "city": "string",
  "city_code": "string",
  "district": "string",
  "address": "string",
  "is_default": false
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "收货地址更新成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或收货地址不存在",
  "result": null
}
```

---

## 5.2.16 删除收货地址

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/customers-v2/{customer_id}/shipping-addresses/{address_id}` |
| **Method** | DELETE |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| address_id | string | 是 | 收货地址ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "收货地址删除成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或收货地址不存在",
  "result": null
}
```

---

## 5.2.17 设置默认收货地址

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/customers-v2/{customer_id}/shipping-addresses/{address_id}/default` |
| **Method** | PATCH |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |
| address_id | string | 是 | 收货地址ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "默认收货地址设置成功"
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "客户不存在或收货地址不存在",
  "result": null
}
```

---

## 5.2.18 获取销售员列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/customers-v2/sales-users/list` |
| **Method** | GET |
| **权限** | `customer.view` |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 否 | 搜索关键词（用户名、姓名） |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取销售员列表成功",
  "result": [
    {
      "id": "user123",
      "username": "lisi",
      "full_name": "李四",
      "display_name": "李经理",
      "email": "lisi@example.com"
    }
  ]
}
```

**返回值字段说明**:
| 字段 | 类型 | 描述 |
|------|------|------|
| result | array | 销售员列表 |
| result[].id | string | 用户ID |
| result[].username | string | 用户名 |
| result[].full_name | string | 姓名 |
| result[].display_name | string | 显示名称 |
| result[].email | string | 邮箱 |

---

## 5.2.19 转移客户

> 将属于自己的客户转移给其他销售员。转移后，原销售员将不再拥有该客户的操作权限。

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/customers-v2/{customer_id}/transfer` |
| **Method** | PATCH |
| **权限** | `customer.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | string | 是 | 客户ID |

### 请求头

```
Authorization: Bearer <token>
Content-Type: application/json
```

### 请求体

```json
{
  "new_sales_user_id": "string"    // 必填，目标销售员ID
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "客户转移成功"
}
```

**错误响应（无权限）**:
```json
{
  "status": "error",
  "message": "您没有权限操作该客户",
  "result": null
}
```

**错误响应（目标销售不存在）**:
```json
{
  "status": "error",
  "message": "目标销售不存在或客户转移失败",
  "result": null
}
```

### 业务规则

1. **权限控制**：
   - 只有客户当前负责人（`sales_user_id` 为当前用户ID）才能转移
   - `super_admin` 角色可以转移任何客户的负责人

2. **数据更新**：
   - `sales_user_id` 更新为目标销售员ID
   - `sales_user_name` 更新为目标销售员姓名

3. **转移记录**：
   - 系统不会保留转移历史记录，如有需要请自行扩展

### 请求示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/customers-v2/64a1b2c3d4e5f6a7b8c9d0e1/transfer" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"new_sales_user_id": "user456"}'
```
