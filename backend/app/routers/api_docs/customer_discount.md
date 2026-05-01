# 客户折扣管理 API

## 基础信息

- **基础路径**: `/api/v1/customer-discounts`
- **认证方式**: Bearer Token (JWT)
- **权限说明**: 需要携带有效 Token 访问

---

## 数据结构

### 客户折扣表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 折扣记录ID（自动生成） |
| customer_id | string | 客户ID |
| brand_id | string | 品牌ID |
| brand_name | string | 品牌名称（可选，由后端自动填充） |
| discount_value | float | 折扣值（0-1之间，如0.85表示85折） |
| is_active | boolean | 是否生效 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 6.1 创建客户折扣

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/customer-discounts/` |
| **Method** | POST |
| **权限** | `customer_discount.create` |

### 请求头

```
Authorization: Bearer <token>
Content-Type: application/json
```

### 请求体

```json
{
  "customer_id": "string",              // 必填，客户ID
  "brand_id": "string",                  // 必填，品牌ID
  "discount_value": 0.85,                 // 必填，折扣值（0-1之间）
  "is_active": true                       // 是否生效（默认true）
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
  "message": "客户折扣创建成功",
  "result": {
    "id": "DIS001",
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

### 请求头

```
Authorization: Bearer <token>
```

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| customer_id | string | 否 | - | 客户ID |
| brand_id | string | 否 | - | 品牌ID |
| is_active | boolean | 否 | - | 是否生效 |

### 请求示例

```
GET /api/v1/customer-discounts/?page=1&page_size=20&customer_id=64a1b2c3d4e5f6a7b8c9d0e1
```

### 响应

**成功响应**:

```json
{
  "status": "success",
  "message": "获取客户折扣列表成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "DIS001",
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

**返回值字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| result.total | int | 满足条件的总记录数 |
| result.page | int | 当前页码 |
| result.page_size | int | 每页记录数 |
| result.items | array | 客户折扣列表 |
| result.items[].id | string | 折扣记录ID |
| result.items[].customer_id | string | 客户ID |
| result.items[].brand_id | string | 品牌ID |
| result.items[].brand_name | string | 品牌名称 |
| result.items[].discount_value | float | 折扣值 |
| result.items[].is_active | boolean | 是否生效 |
| result.items[].created_at | datetime | 创建时间 |
| result.items[].updated_at | datetime | 更新时间 |

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
  "message": "获取客户折扣详情成功",
  "result": {
    "id": "DIS001",
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

## 6.4 获取指定客户和品牌的折扣

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
  "message": "获取客户折扣成功",
  "result": {
    "id": "DIS001",
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
  "discount_value": 0.8,                 // 折扣值（0-1之间）
  "is_active": false                      // 是否生效
}
```

**请求字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| discount_value | float | 否 | 折扣值（0-1之间，如0.85表示85折） |
| is_active | boolean | 否 | 是否生效 |

### 响应

**成功响应**:

```json
{
  "status": "success",
  "message": "客户折扣更新成功"
}
```

**错误响应（折扣不存在）**:

```json
{
  "status": "error",
  "message": "客户折扣不存在",
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
  "message": "客户折扣删除成功"
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
  "message": "客户折扣状态更新成功"
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

## 业务规则

1. **唯一性约束**: 同一个客户和品牌组合只能有一条生效的折扣配置
2. **折扣值范围**: discount_value 必须在 0-1 之间（0表示免费，1表示不打折，0.85表示85折）
3. **状态控制**: 可以通过 is_active 字段控制折扣是否生效，灵活支持促销活动
4. **权限控制**: 所有操作需要相应权限（customer_discount.create/view/edit/delete）
