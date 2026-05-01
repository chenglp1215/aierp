# API 接口文档

本文档描述 AI MDR Platform 后端所有 REST API 接口。

**基础路径**: `/api/v1`

**认证方式**: Bearer Token (JWT)

---

## HTTP 状态码规范

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 401 | 未认证或认证失效 |
| 5XX | 服务器内部错误 |

---

## 统一响应格式

### 成功响应格式 (200)

#### list 列表响应

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
        "id": "64a1b2c3d4e5f6a7b8c9d0e1",
        "customer_code": "C2024010001",
        "name": "某医院检验科",
        "customer_type": "terminal",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "status": "normal",
        "sales_user_name": "李经理",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### detail 详情响应

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "customer_code": "C2024010001",
    "name": "某医院检验科",
    "customer_type": "terminal",
    "contact_person": "张三",
    "contact_phone": "13800138000",
    "status": "normal",
    "sales_user_name": "李经理",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 错误响应格式 (200)

#### 通用错误格式

```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

#### 数据校验错误格式

当数据校验失败时（如参数验证），返回格式如下：

```json
{
  "status": "error",
  "message": "客户更新参数验证失败",
  "validation_errors": [
    {
      "field": "name",
      "message": "客户名称不能为空"
    },
    {
      "field": "contact_info.contact_phone",
      "message": "手机号格式不正确"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 固定为 `error` |
| message | string | 错误描述信息 |
| validation_errors | array | 校验错误列表 |
| validation_errors[].field | string | 错误字段路径 |
| validation_errors[].message | string | 字段错误描述 |

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | `success` 或 `error` |
| message | string | 操作结果的描述信息 |
| result | object/array/null | 返回数据，失败时为 null |
| result.total | int | 列表总记录数（仅列表接口） |
| result.page | int | 当前页码（仅列表接口） |
| result.page_size | int | 每页记录数（仅列表接口） |
| result.items | array | 数据列表（仅列表接口） |

### 无返回值的操作

对于删除等无返回值的操作：

```json
{
  "status": "success",
  "message": "删除成功",
  "result": null
}
```

---

## 通用说明

### 权限认证

大部分接口需要登录后访问，Header 中需携带 Token：

```
Authorization: Bearer <token>
```

### 日期时间格式

所有日期时间字段使用 ISO 8601 格式：
- 日期: `YYYY-MM-DD`
- 时间: `YYYY-MM-DDTHH:mm:ss`
- 带时区: `YYYY-MM-DDTHH:mm:ssZ`

---

## 文档目录

### 客户管理

| 文档 | 描述 |
|------|------|
| [customer_v2.md](./customer_v2.md) | 客户管理 v2（当前使用版本） |
| [customer_discount.md](./customer_discount.md) | 客户折扣管理 |

### 地理位置

| 文档 | 描述 |
|------|------|
| [province_city.md](./province_city.md) | 省份城市数据查询 |

### 其他模块

| 文档 | 描述 |
|------|------|
| [product.md](./product.md) | 商品管理（含商品规格） |

其他模块的 API 文档待补充。
