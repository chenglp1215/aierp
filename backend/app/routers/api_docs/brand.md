# 品牌管理 API

> 用于管理商品品牌信息

## 基础信息

- **基础路径**: `/api/v1/brands`
- **认证方式**: Bearer Token (JWT)

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

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {}
}
```

### 错误响应格式 (200)

```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

---

## 接口列表

### 5.X.1 创建品牌

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/brands/` |
| **Method** | POST |
| **认证** | 需要认证 |

### 请求体

```json
{
  "name": "茶语轩",
  "logo_url": "https://example.com/images/brand-logo.png",
  "description": "知名茶叶品牌",
  "is_active": true
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 品牌名称（1-100字符） |
| logo_url | string | 否 | 品牌Logo URL（最大500字符） |
| description | string | 否 | 品牌描述（最大500字符） |
| is_active | boolean | 否 | 是否激活（默认true） |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "品牌创建成功",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "茶语轩",
    "logo_url": "https://example.com/images/brand-logo.png",
    "description": "知名茶叶品牌",
    "is_active": true,
    "created_at": "2026-05-01T10:00:00",
    "updated_at": "2026-05-01T10:00:00"
  }
}
```

**错误响应**（品牌名称已存在）:
```json
{
  "status": "error",
  "message": "品牌名称已存在",
  "result": null
}
```

---

### 5.X.2 获取品牌列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/brands/` |
| **Method** | GET |
| **认证** | 需要认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| keyword | string | 否 | 搜索关键词（品牌名称模糊匹配） |
| is_active | boolean | 否 | 是否激活筛选 |

### 请求示例

```
GET /api/v1/brands/?page=1&page_size=20&keyword=茶语
```

### 响应

**成功响应**:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "茶语轩",
      "logo_url": "https://example.com/images/brand-logo.png",
      "description": "知名茶叶品牌",
      "is_active": true,
      "created_at": "2026-05-01T10:00:00",
      "updated_at": "2026-05-01T10:00:00"
    }
  ]
}
```

**返回值字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| total | integer | 总记录数 |
| page | integer | 当前页码 |
| page_size | integer | 每页记录数 |
| items | array | 品牌列表 |
| items[].id | string | 品牌ID |
| items[].name | string | 品牌名称 |
| items[].logo_url | string | 品牌Logo URL |
| items[].description | string | 品牌描述 |
| items[].is_active | boolean | 是否激活 |
| items[].created_at | string | 创建时间 |
| items[].updated_at | string | 更新时间 |

---

### 5.X.3 获取所有品牌

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/brands/all` |
| **Method** | GET |
| **认证** | 需要认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_active | boolean | 否 | 是否激活筛选 |

### 请求示例

```
GET /api/v1/brands/all?is_active=true
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取品牌列表成功",
  "result": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "茶语轩",
      "logo_url": "https://example.com/images/brand-logo.png",
      "description": "知名茶叶品牌",
      "is_active": true,
      "created_at": "2026-05-01T10:00:00",
      "updated_at": "2026-05-01T10:00:00"
    }
  ]
}
```

---

### 5.X.4 获取品牌详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/brands/{brand_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

### 请求示例

```
GET /api/v1/brands/507f1f77bcf86cd799439011
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取品牌详情成功",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "茶语轩",
    "logo_url": "https://example.com/images/brand-logo.png",
    "description": "知名茶叶品牌",
    "is_active": true,
    "created_at": "2026-05-01T10:00:00",
    "updated_at": "2026-05-01T10:00:00"
  }
}
```

**错误响应**（品牌不存在）:
```json
{
  "status": "error",
  "message": "品牌不存在",
  "result": null
}
```

---

### 5.X.5 更新品牌

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/brands/{brand_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

### 请求体

```json
{
  "name": "茶语轩旗舰店",
  "logo_url": "https://example.com/images/new-logo.png",
  "description": "更新后的品牌描述",
  "is_active": true
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 品牌名称（1-100字符） |
| logo_url | string | 否 | 品牌Logo URL（最大500字符） |
| description | string | 否 | 品牌描述（最大500字符） |
| is_active | boolean | 否 | 是否激活 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "品牌更新成功",
  "result": null
}
```

**错误响应**（品牌名称已存在）:
```json
{
  "status": "error",
  "message": "品牌名称已存在",
  "result": null
}
```

**错误响应**（品牌不存在）:
```json
{
  "status": "error",
  "message": "品牌不存在或更新失败",
  "result": null
}
```

---

### 5.X.6 删除品牌

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/brands/{brand_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

### 请求示例

```
DELETE /api/v1/brands/507f1f77bcf86cd799439011
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "品牌删除成功",
  "result": null
}
```

**错误响应**（品牌下存在商品）:
```json
{
  "status": "error",
  "message": "该品牌下存在 5 个商品，无法删除",
  "result": null
}
```

**错误响应**（品牌不存在）:
```json
{
  "status": "error",
  "message": "品牌不存在或删除失败",
  "result": null
}
```

---

### 5.X.7 切换品牌激活状态

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/brands/{brand_id}/toggle-active` |
| **Method** | PATCH |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_active | boolean | 是 | 是否激活 |

### 请求示例

```
PATCH /api/v1/brands/507f1f77bcf86cd799439011/toggle-active?is_active=false
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "品牌已停用",
  "result": null
}
```

**错误响应**（品牌不存在）:
```json
{
  "status": "error",
  "message": "品牌不存在或更新失败",
  "result": null
}
```

---

## 数据模型

### Brand（品牌）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 品牌ID（MongoDB ObjectId） |
| name | string | 品牌名称 |
| logo_url | string | 品牌Logo URL |
| description | string | 品牌描述 |
| is_active | boolean | 是否激活 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 权限说明

品牌管理接口需要以下权限：

| 接口 | 所需权限 |
|------|----------|
| 创建品牌 | `brand.create` |
| 获取品牌列表 | `brand.view` |
| 获取所有品牌 | `brand.view` |
| 获取品牌详情 | `brand.view` |
| 更新品牌 | `brand.edit` |
| 删除品牌 | `brand.delete` |
| 切换品牌激活状态 | `brand.edit` |