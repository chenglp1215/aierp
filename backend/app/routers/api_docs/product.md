# 商品管理 API

> 用于管理商品信息、商品规格、品牌和分类，支持商品及其关联数据的完整 CRUD 操作

## 基础信息

- **基础路径**: `/api/v1`
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

### 校验错误响应格式 (200)

当请求参数不合法时，返回结构化的验证错误列表：

```json
{
  "status": "error",
  "message": "参数验证失败",
  "result": null,
  "validation_errors": [
    {"field": "name", "message": "name为必填"},
    {"field": "price", "message": "price不能小于0"}
  ]
}
```

---

## 目录

- [商品管理](#商品管理)
  - [创建商品](#7-x-1-创建商品)
  - [获取商品列表](#7-x-2-获取商品列表)
  - [获取商品详情](#7-x-3-获取商品详情)
  - [更新商品](#7-x-4-更新商品)
  - [删除商品](#7-x-5-删除商品)
  - [获取商品的所有规格](#7-x-6-获取商品的所有规格)
  - [为商品创建规格](#7-x-7-为商品创建规格)
- [商品规格管理](#商品规格管理)
  - [搜索商品规格](#7-x-8-搜索商品规格)
  - [获取规格详情](#7-x-9-获取规格详情)
  - [更新规格](#7-x-10-更新规格)
  - [删除规格](#7-x-11-删除规格)
- [品牌管理](#品牌管理)
  - [获取品牌列表](#7-x-12-获取品牌列表)
  - [创建品牌](#7-x-13-创建品牌)
  - [获取品牌详情](#7-x-14-获取品牌详情)
  - [更新品牌](#7-x-15-更新品牌)
  - [删除品牌](#7-x-16-删除品牌)
- [分类管理](#分类管理)
  - [获取分类树](#7-x-17-获取分类树)
  - [创建分类](#7-x-18-创建分类)
  - [获取分类详情](#7-x-19-获取分类详情)
  - [更新分类](#7-x-20-更新分类)
  - [删除分类](#7-x-21-删除分类)
- [数据模型](#数据模型)
- [业务规则](#业务规则)
- [权限说明](#权限说明)

---

## 商品管理

### 7.X.1 创建商品

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/products/` |
| **Method** | POST |
| **认证** | 需要认证 |

**请求体**

```json
{
  "name": "有机红茶",
  "image_url": "https://example.com/images/red-tea.jpg",
  "brand_id": "507f1f77bcf86cd799439011",
  "category_id": "507f1f77bcf86cd799439011",
  "tax_code": "TAX001",
  "is_active": true
}
```

**请求体字段说明**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 商品名称（1-200字符） |
| image_url | string | 否 | 商品图片URL（最大500字符） |
| brand_id | string | 是 | 品牌ID（必须为已存在的品牌） |
| category_id | string | 是 | 分类ID（必须为已存在的分类） |
| tax_code | string | 否 | 税务编码（最大50字符） |
| is_active | boolean | 否 | 是否有效（默认true） |

> **说明**: `product_code` 由系统自动生成，格式为 `PROD{日期}{6位随机数}`

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439012",
    "product_code": "PROD202605080001",
    "name": "有机红茶",
    "image_url": "https://example.com/images/red-tea.jpg",
    "brand_id": "507f1f77bcf86cd799439011",
    "brand_name": "茶语轩",
    "category_id": "507f1f77bcf86cd799439011",
    "category_name": "茶叶",
    "tax_code": "TAX001",
    "is_active": true,
    "created_at": "2026-05-08T10:00:00",
    "updated_at": "2026-05-08T10:00:00"
  }
}
```

**错误响应**

| 场景 | message | validation_errors |
|------|---------|-------------------|
| 品牌不存在 | `"品牌不存在"` | — |
| 分类不存在 | `"分类不存在"` | — |
| 参数校验失败 | `"参数验证失败"` | `[{field, message}, ...]` |

---

### 7.X.2 获取商品列表

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/` |
| **Method** | GET |
| **认证** | 需要认证 |

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| keyword | string | 否 | 搜索关键词（商品名称或编号模糊匹配） |
| brand_id | string | 否 | 品牌ID筛选 |
| category_id | string | 否 | 分类ID筛选 |

**请求示例**

```
GET /api/v1/products/?page=1&page_size=20&keyword=红茶
```

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
        "id": "507f1f77bcf86cd799439012",
        "product_code": "PROD202605080001",
        "name": "有机红茶",
        "image_url": "https://example.com/images/red-tea.jpg",
        "brand_id": "507f1f77bcf86cd799439011",
        "brand_name": "茶语轩",
        "category_id": "507f1f77bcf86cd799439011",
        "category_name": "茶叶",
        "tax_code": "TAX001",
        "is_active": true,
        "created_at": "2026-05-08T10:00:00",
        "updated_at": "2026-05-08T10:00:00",
        "specs": [
          {
            "id": "507f1f77bcf86cd799439013",
            "product_id": "507f1f77bcf86cd799439012",
            "spec_code": "SPEC202605080001",
            "packaging": "100g/罐",
            "sales_spec": "100g*24罐/箱",
            "price": 128.00,
            "cas_number": "68917-21-1",
            "is_active": true
          }
        ]
      }
    ]
  }
}
```

---

### 7.X.3 获取商品详情

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/{product_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439012",
    "product_code": "PROD202605080001",
    "name": "有机红茶",
    "image_url": "https://example.com/images/red-tea.jpg",
    "brand_id": "507f1f77bcf86cd799439011",
    "brand_name": "茶语轩",
    "category_id": "507f1f77bcf86cd799439011",
    "category_name": "茶叶",
    "tax_code": "TAX001",
    "is_active": true,
    "created_at": "2026-05-08T10:00:00",
    "updated_at": "2026-05-08T10:00:00",
    "specs": [
      {
        "id": "507f1f77bcf86cd799439013",
        "product_id": "507f1f77bcf86cd799439012",
        "spec_code": "SPEC202605080001",
        "packaging": "100g/罐",
        "sales_spec": "100g*24罐/箱",
        "price": 128.00,
        "cas_number": "68917-21-1",
        "is_active": true
      }
    ]
  }
}
```

**错误响应**（商品不存在）:

```json
{
  "status": "error",
  "message": "商品不存在",
  "result": null
}
```

---

### 7.X.4 更新商品

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/products/{product_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

**请求体**（所有字段可选）

```json
{
  "name": "有机红茶（新版）",
  "image_url": "https://example.com/images/red-tea-new.jpg",
  "brand_id": "507f1f77bcf86cd799439011",
  "category_id": "507f1f77bcf86cd799439011",
  "tax_code": "TAX001",
  "is_active": true
}
```

**成功响应**

```json
{
  "status": "success",
  "message": "商品更新成功",
  "result": null
}
```

**错误响应**

| 场景 | message |
|------|---------|
| 商品不存在 | `"商品不存在"` |
| 品牌不存在 | `"品牌不存在"` |
| 分类不存在 | `"分类不存在"` |

---

### 7.X.5 删除商品

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/products/{product_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

**成功响应**

```json
{
  "status": "success",
  "message": "商品删除成功",
  "result": null
}
```

> **业务说明**: 删除商品时，会同时删除该商品下的所有关联规格。

---

### 7.X.6 获取商品的所有规格

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/{product_id}/specs` |
| **Method** | GET |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "total": 2,
    "items": [
      {
        "id": "507f1f77bcf86cd799439013",
        "product_id": "507f1f77bcf86cd799439012",
        "spec_code": "SPEC202605080001",
        "packaging": "100g/罐",
        "sales_spec": "100g*24罐/箱",
        "price": 128.00,
        "cas_number": "68917-21-1",
        "is_active": true
      }
    ]
  }
}
```

---

### 7.X.7 为商品创建规格

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/products/{product_id}/specs` |
| **Method** | POST |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

**请求体**

```json
{
  "spec_code": "SPEC202605080001",
  "packaging": "100g/罐",
  "sales_spec": "100g*24罐/箱",
  "price": 128.00,
  "cas_number": "68917-21-1",
  "is_active": true
}
```

**请求体字段说明**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_code | string | 是 | 规格编号（1-50字符） |
| packaging | string | 否 | 包装（最大100字符） |
| sales_spec | string | 否 | 销售规格（最大100字符） |
| price | float | 是 | 价格（必须大于等于0） |
| cas_number | string | 否 | CAS号（最大50字符） |
| is_active | boolean | 否 | 是否有效（默认true） |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439013",
    "product_id": "507f1f77bcf86cd799439012",
    "spec_code": "SPEC202605080001",
    "packaging": "100g/罐",
    "sales_spec": "100g*24罐/箱",
    "price": 128.00,
    "cas_number": "68917-21-1",
    "is_active": true,
    "created_at": "2026-05-08T10:00:00",
    "updated_at": "2026-05-08T10:00:00"
  }
}
```

**错误响应**（商品不存在）:

```json
{
  "status": "error",
  "message": "商品不存在",
  "result": null
}
```

---

## 商品规格管理

### 7.X.8 搜索商品规格

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/specs/search` |
| **Method** | GET |
| **认证** | 需要认证 |

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（最小1字符） |
| limit | integer | 否 | 返回数量（默认20，最大50） |

**请求示例**

```
GET /api/v1/products/specs/search?keyword=SPEC001&limit=20
```

**成功响应**

```json
{
  "status": "success",
  "result": {
    "total": 1,
    "items": [
      {
        "id": "507f1f77bcf86cd799439013",
        "spec_code": "SPEC202605080001",
        "packaging": "100g/罐",
        "sales_spec": "100g*24罐/箱",
        "price": 128.00,
        "product_id": "507f1f77bcf86cd799439012",
        "product_name": "有机红茶",
        "product_code": "PROD202605080001"
      }
    ]
  }
}
```

---

### 7.X.9 获取规格详情

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/specs/{spec_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439013",
    "product_id": "507f1f77bcf86cd799439012",
    "spec_code": "SPEC202605080001",
    "packaging": "100g/罐",
    "sales_spec": "100g*24罐/箱",
    "price": 128.00,
    "cas_number": "68917-21-1",
    "is_active": true
  }
}
```

**错误响应**（规格不存在）:

```json
{
  "status": "error",
  "message": "规格不存在",
  "result": null
}
```

---

### 7.X.10 更新规格

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/products/specs/{spec_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

**请求体**（所有字段可选）

```json
{
  "spec_code": "SPEC202605080001",
  "packaging": "100g/罐（新版）",
  "sales_spec": "100g*24罐/箱",
  "price": 138.00,
  "cas_number": "68917-21-1",
  "is_active": true
}
```

**请求体字段说明**（所有字段可选）

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_code | string | 否 | 规格编号（1-50字符） |
| packaging | string | 否 | 包装（最大100字符） |
| sales_spec | string | 否 | 销售规格（最大100字符） |
| price | float | 否 | 价格（必须大于等于0） |
| cas_number | string | 否 | CAS号（最大50字符） |
| is_active | boolean | 否 | 是否有效 |

**成功响应**

```json
{
  "status": "success",
  "message": "规格更新成功",
  "result": null
}
```

---

### 7.X.11 删除规格

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/products/specs/{spec_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

**成功响应**

```json
{
  "status": "success",
  "message": "规格删除成功",
  "result": null
}
```

---

## 品牌管理

### 7.X.12 获取品牌列表

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/brands/` |
| **Method** | GET |
| **认证** | 需要认证 |

**查询参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| keyword | string | 否 | 搜索关键词（品牌名称或描述模糊匹配） |

**请求示例**

```
GET /api/v1/brands/?page=1&page_size=20&keyword=茶语
```

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
        "name": "茶语轩",
        "logo_url": "https://example.com/images/brand-logo.png",
        "description": "知名茶叶品牌",
        "purchaser_id": "507f1f77bcf86cd799439020",
        "purchaser_name": "张三",
        "is_active": true,
        "created_at": "2026-05-01T10:00:00",
        "updated_at": "2026-05-01T10:00:00"
      }
    ]
  }
}
```

---

### 7.X.13 创建品牌

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/brands/` |
| **Method** | POST |
| **认证** | 需要认证 |

**请求体**

```json
{
  "name": "茶语轩",
  "logo_url": "https://example.com/images/brand-logo.png",
  "description": "知名茶叶品牌",
  "purchaser_id": "507f1f77bcf86cd799439020",
  "is_active": true
}
```

**请求体字段说明**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 品牌名称（1-100字符） |
| logo_url | string | 否 | 品牌Logo URL（最大500字符） |
| description | string | 否 | 品牌描述（最大500字符） |
| purchaser_id | string | 否 | 采购人员ID |
| is_active | boolean | 否 | 是否有效（默认true） |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "茶语轩",
    "logo_url": "https://example.com/images/brand-logo.png",
    "description": "知名茶叶品牌",
    "purchaser_id": "507f1f77bcf86cd799439020",
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

### 7.X.14 获取品牌详情

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/brands/{brand_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "茶语轩",
    "logo_url": "https://example.com/images/brand-logo.png",
    "description": "知名茶叶品牌",
    "purchaser_id": "507f1f77bcf86cd799439020",
    "purchaser_name": "张三",
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

### 7.X.15 更新品牌

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/brands/{brand_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

**请求体**（所有字段可选）

```json
{
  "name": "茶语轩旗舰店",
  "logo_url": "https://example.com/images/new-logo.png",
  "description": "更新后的品牌描述",
  "purchaser_id": "507f1f77bcf86cd799439020",
  "is_active": true
}
```

**请求体字段说明**（所有字段可选）

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 品牌名称（1-100字符） |
| logo_url | string | 否 | 品牌Logo URL（最大500字符） |
| description | string | 否 | 品牌描述（最大500字符） |
| purchaser_id | string | 否 | 采购人员ID |
| is_active | boolean | 否 | 是否有效 |

**成功响应**

```json
{
  "status": "success",
  "message": "品牌更新成功",
  "result": null
}
```

**错误响应**

| 场景 | message |
|------|---------|
| 品牌名称已存在 | `"品牌名称已存在"` |
| 品牌不存在 | `"品牌不存在"` |

---

### 7.X.16 删除品牌

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/brands/{brand_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

**成功响应**

```json
{
  "status": "success",
  "message": "品牌删除成功",
  "result": null
}
```

**错误响应**

| 场景 | message |
|------|---------|
| 品牌下存在商品 | `"该品牌下有商品，不能删除"` |
| 品牌不存在 | `"品牌不存在"` |

---

## 分类管理

### 7.X.17 获取分类树

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/categories/` |
| **Method** | GET |
| **认证** | 需要认证 |

> **说明**: 该接口返回完整的分类树形结构，不支持分页。

**成功响应**

```json
{
  "status": "success",
  "result": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "电子产品",
      "parent_id": null,
      "tax_code": "TAX001",
      "sort_order": 1,
      "is_shop_display": true,
      "level": 1,
      "children": [
        {
          "id": "507f1f77bcf86cd799439012",
          "name": "手机",
          "parent_id": "507f1f77bcf86cd799439011",
          "tax_code": "TAX002",
          "sort_order": 1,
          "is_shop_display": true,
          "level": 2,
          "children": []
        }
      ]
    }
  ]
}
```

---

### 7.X.18 创建分类

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/categories/` |
| **Method** | POST |
| **认证** | 需要认证 |

**请求体**

```json
{
  "name": "电子产品",
  "parent_id": null,
  "tax_code": "TAX001",
  "sort_order": 1,
  "is_shop_display": true
}
```

**请求体字段说明**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 分类名称（1-100字符） |
| parent_id | string | 否 | 父分类ID，为空则为顶层分类 |
| tax_code | string | 否 | 税务编码（最大50字符） |
| sort_order | integer | 否 | 排序，数字越小越靠前（默认0） |
| is_shop_display | boolean | 否 | 是否商城展示（默认true） |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "电子产品",
    "parent_id": null,
    "tax_code": "TAX001",
    "sort_order": 1,
    "is_shop_display": true,
    "level": 1,
    "created_at": "2026-05-08T10:00:00",
    "updated_at": "2026-05-08T10:00:00"
  }
}
```

**错误响应**

| 场景 | message |
|------|---------|
| 分类名称已存在 | `"分类名称已存在"` |

---

### 7.X.19 获取分类详情

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/categories/{category_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| category_id | string | 是 | 分类ID |

**成功响应**

```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "电子产品",
    "parent_id": null,
    "tax_code": "TAX001",
    "sort_order": 1,
    "is_shop_display": true,
    "level": 1,
    "created_at": "2026-05-08T10:00:00",
    "updated_at": "2026-05-08T10:00:00"
  }
}
```

**错误响应**（分类不存在）:

```json
{
  "status": "error",
  "message": "分类不存在",
  "result": null
}
```

---

### 7.X.20 更新分类

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/categories/{category_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| category_id | string | 是 | 分类ID |

**请求体**（所有字段可选）

```json
{
  "name": "电子产品",
  "parent_id": "507f1f77bcf86cd799439010",
  "tax_code": "TAX001",
  "sort_order": 1,
  "is_shop_display": true
}
```

**请求体字段说明**（所有字段可选）

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 分类名称（1-100字符） |
| parent_id | string | 否 | 父分类ID，为空则为顶层分类 |
| tax_code | string | 否 | 税务编码（最大50字符） |
| sort_order | integer | 否 | 排序，数字越小越靠前 |
| is_shop_display | boolean | 否 | 是否商城展示 |

**成功响应**

```json
{
  "status": "success",
  "message": "分类更新成功",
  "result": null
}
```

**错误响应**

| 场景 | message |
|------|---------|
| 分类名称已存在 | `"分类名称已存在"` |
| 分类不存在 | `"分类不存在"` |

---

### 7.X.21 删除分类

**接口信息**

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/categories/{category_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

**路径参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| category_id | string | 是 | 分类ID |

**成功响应**

```json
{
  "status": "success",
  "message": "分类删除成功",
  "result": null
}
```

**错误响应**

| 场景 | message |
|------|---------|
| 分类下存在子分类 | `"该分类下有子分类，不能删除"` |
| 分类下存在商品 | `"该分类下有商品，不能删除"` |
| 分类不存在 | `"分类不存在"` |

---

## 数据模型

### Product（商品）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 商品ID（MongoDB ObjectId） |
| product_code | string | 商品编号（系统自动生成，格式 `PROD{日期}{6位随机数}`） |
| name | string | 商品名称 |
| image_url | string | 商品图片URL |
| brand_id | string | 品牌ID |
| brand_name | string | 品牌名称（关联查询时自动填充） |
| category_id | string | 分类ID |
| category_name | string | 分类名称（关联查询时自动填充） |
| tax_code | string | 税务编码 |
| is_active | boolean | 是否有效 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| specs | array | 商品规格列表 |

### ProductSpec（商品规格）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 规格ID（MongoDB ObjectId） |
| product_id | string | 关联商品ID |
| spec_code | string | 规格编号 |
| packaging | string | 包装 |
| sales_spec | string | 销售规格 |
| price | float | 价格 |
| cas_number | string | CAS号 |
| is_active | boolean | 是否有效 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Brand（品牌）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 品牌ID（MongoDB ObjectId） |
| name | string | 品牌名称 |
| logo_url | string | 品牌Logo URL |
| description | string | 品牌描述 |
| purchaser_id | string | 采购人员ID |
| purchaser_name | string | 采购人员名称（关联查询时自动填充） |
| is_active | boolean | 是否有效 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Category（分类）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 分类ID（MongoDB ObjectId） |
| name | string | 分类名称 |
| parent_id | string | 父分类ID，顶级分类为 null |
| tax_code | string | 税务编码 |
| sort_order | integer | 排序权重，数字越小越靠前 |
| is_shop_display | boolean | 是否在商城展示 |
| level | integer | 分类层级（自动计算，1为一级分类，2为二级分类，以此类推，最多5级） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 业务规则

### 商品

1. **商品编号**: 由系统自动生成，格式为 `PROD{日期YYYYMMDD}{6位随机数}`，不可手动修改
2. **品牌和分类关联**: 创建或更新商品时，`brand_id` 和 `category_id` 对应的品牌/分类必须存在
3. **级联删除**: 删除商品时，会同时删除该商品下的所有关联规格
4. **商品规格关联**: 每个商品可以拥有多个规格，规格与商品是一对多关系

### 品牌

5. **品牌名称唯一**: 品牌名称不可重复
6. **删除约束**: 品牌下存在商品时不允许删除

### 分类

7. **分类树结构**: 分类层级不限制（数据层级限制5层以下），以树形结构管理
8. **分类名称唯一**: 同级分类名称不可重复
9. **删除约束**: 存在子分类或商品的分类不允许删除
10. **排序规则**: 分类按 `sort_order` 字段升序排列，数字越小越靠前

---

## 权限说明

### 商品管理权限

| 接口 | 所需权限 |
|------|----------|
| 创建商品 | `product.create` |
| 获取商品列表 | `product.view` |
| 获取商品详情 | `product.view` |
| 更新商品 | `product.edit` |
| 删除商品 | `product.delete` |
| 获取商品规格列表 | `product.view` |
| 创建商品规格 | `product.create` |
| 搜索商品规格 | `product.view` |
| 获取规格详情 | `product.view` |
| 更新规格 | `product.edit` |
| 删除规格 | `product.delete` |

### 品牌管理权限

| 接口 | 所需权限 |
|------|----------|
| 获取品牌列表 | `brand.view` |
| 创建品牌 | `brand.create` |
| 获取品牌详情 | `brand.view` |
| 更新品牌 | `brand.edit` |
| 删除品牌 | `brand.delete` |

### 分类管理权限

| 接口 | 所需权限 |
|------|----------|
| 获取分类树 | `category.view` |
| 创建分类 | `category.create` |
| 获取分类详情 | `category.view` |
| 更新分类 | `category.edit` |
| 删除分类 | `category.delete` |
