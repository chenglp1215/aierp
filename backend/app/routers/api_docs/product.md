# 商品管理 API

> 用于管理商品信息及商品规格，支持商品的完整 CRUD 操作

## 基础信息

- **基础路径**: `/api/v1/products`
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

### 7.X.1 创建商品

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/products/` |
| **Method** | POST |
| **认证** | 需要认证 |

### 请求体

```json
{
  "product_code": "PROD20260420001",
  "name": "有机红茶",
  "image_url": "https://example.com/images/red-tea.jpg",
  "brand_id": "507f1f77bcf86cd799439011",
  "category_id": "507f1f77bcf86cd799439011",
  "tax_code": "TAX001",
  "is_active": true,
  "specs": [
    {
      "spec_code": "SPEC20260420001",
      "packaging": "100g/罐",
      "sales_spec": "100g*24罐/箱",
      "price": 128.00,
      "cas_number": "68917-21-1",
      "is_active": true
    }
  ]
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_code | string | 是 | 商品编号（1-50字符） |
| name | string | 是 | 商品名称（1-200字符） |
| image_url | string | 否 | 商品图片URL（最大500字符） |
| brand_id | string | 否 | 品牌ID |
| category_id | string | 否 | 分类ID |
| tax_code | string | 否 | 税务编码（最大50字符） |
| is_active | boolean | 否 | 是否有效（默认true） |
| specs | array | 否 | 商品规格列表 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "商品创建成功",
  "result": {
    "id": "507f1f77bcf86cd799439012",
    "product_code": "PROD20260420001",
    "name": "有机红茶",
    "image_url": "https://example.com/images/red-tea.jpg",
    "brand_id": "507f1f77bcf86cd799439011",
    "brand_name": "茶语轩",
    "category_id": "507f1f77bcf86cd799439011",
    "tax_code": "TAX001",
    "is_active": true,
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:00:00"
  }
}
```

**错误响应**（数据校验失败）:
```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

---

### 7.X.2 获取商品列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/` |
| **Method** | GET |
| **认证** | 需要认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| keyword | string | 否 | 搜索关键词（商品名称或编号模糊匹配） |
| brand_id | string | 否 | 品牌ID筛选 |
| category_id | string | 否 | 分类ID筛选 |

### 请求示例

```
GET /api/v1/products/?page=1&page_size=20&keyword=红茶
```

### 响应

**成功响应**:
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
        "product_code": "PROD20260420001",
        "name": "有机红茶",
        "image_url": "https://example.com/images/red-tea.jpg",
        "brand_id": "507f1f77bcf86cd799439011",
        "brand_name": "茶语轩",
        "category_id": "507f1f77bcf86cd799439011",
        "category_name": "茶叶",
        "tax_code": "TAX001",
        "is_active": true,
        "created_at": "2026-04-20T10:00:00",
        "updated_at": "2026-04-20T10:00:00",
        "specs": [
          {
            "id": "507f1f77bcf86cd799439013",
            "product_id": "507f1f77bcf86cd799439012",
            "spec_code": "SPEC20260420001",
            "packaging": "100g/罐",
            "sales_spec": "100g*24罐/箱",
            "price": 128.00,
            "cas_number": "68917-21-1",
            "is_active": true,
            "stock_quantity": 500,
            "stock_status": "normal"
          }
        ]
      }
    ]
  }
}
```

**返回值字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 固定为 "success" |
| result.total | integer | 总记录数 |
| result.page | integer | 当前页码 |
| result.page_size | integer | 每页记录数 |
| result.items | array | 商品列表 |
| result.items[].id | string | 商品ID |
| result.items[].product_code | string | 商品编号 |
| result.items[].name | string | 商品名称 |
| result.items[].image_url | string | 商品图片URL |
| result.items[].brand_id | string | 品牌ID |
| result.items[].brand_name | string | 品牌名称 |
| result.items[].category_id | string | 分类ID |
| result.items[].category_name | string | 分类名称 |
| result.items[].tax_code | string | 税务编码 |
| result.items[].is_active | boolean | 是否有效 |
| result.items[].created_at | datetime | 创建时间 |
| result.items[].updated_at | datetime | 更新时间 |
| result.items[].specs | array | 商品规格列表 |

---

### 7.X.3 获取商品统计信息

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/stats` |
| **Method** | GET |
| **认证** | 需要认证 |

### 请求示例

```
GET /api/v1/products/stats
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": {
    "total_products": 100,
    "active_products": 80,
    "inactive_products": 20,
    "total_specs": 300,
    "active_specs": 250
  }
}
```

---

### 7.X.4 搜索商品

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/search` |
| **Method** | GET |
| **认证** | 需要认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（最小1字符） |
| limit | integer | 否 | 返回数量（默认10，最大50） |

### 请求示例

```
GET /api/v1/products/search?keyword=红茶&limit=10
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": [
    {
      "id": "507f1f77bcf86cd799439012",
      "product_code": "PROD20260420001",
      "name": "有机红茶",
      "brand_id": "507f1f77bcf86cd799439011",
      "brand_name": "茶语轩"
    }
  ]
}
```

---

### 7.X.5 获取商品详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/{product_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

### 请求示例

```
GET /api/v1/products/507f1f77bcf86cd799439012
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439012",
    "product_code": "PROD20260420001",
    "name": "有机红茶",
    "image_url": "https://example.com/images/red-tea.jpg",
    "brand_id": "507f1f77bcf86cd799439011",
    "brand_name": "茶语轩",
    "category_id": "507f1f77bcf86cd799439011",
    "category_name": "茶叶",
    "tax_code": "TAX001",
    "is_active": true,
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:00:00",
    "specs": [
      {
        "id": "507f1f77bcf86cd799439013",
        "product_id": "507f1f77bcf86cd799439012",
        "spec_code": "SPEC20260420001",
        "packaging": "100g/罐",
        "sales_spec": "100g*24罐/箱",
        "price": 128.00,
        "cas_number": "68917-21-1",
        "is_active": true,
        "stock_quantity": 500,
        "stock_status": "normal"
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

### 7.X.6 更新商品

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/products/{product_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

### 请求体

```json
{
  "product_code": "PROD20260420001",
  "name": "有机红茶（新版）",
  "image_url": "https://example.com/images/red-tea-new.jpg",
  "brand_id": "507f1f77bcf86cd799439011",
  "category_id": "507f1f77bcf86cd799439011",
  "tax_code": "TAX001",
  "is_active": true
}
```

**请求体字段说明**（所有字段可选）:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_code | string | 否 | 商品编号（1-50字符） |
| name | string | 否 | 商品名称（1-200字符） |
| image_url | string | 否 | 商品图片URL（最大500字符） |
| brand_id | string | 否 | 品牌ID |
| category_id | string | 否 | 分类ID |
| tax_code | string | 否 | 税务编码（最大50字符） |
| is_active | boolean | 否 | 是否有效 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "商品更新成功",
  "result": null
}
```

**错误响应**（商品不存在）:
```json
{
  "status": "error",
  "message": "商品不存在或更新失败",
  "result": null
}
```

---

### 7.X.7 删除商品

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/products/{product_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

### 请求示例

```
DELETE /api/v1/products/507f1f77bcf86cd799439012
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "商品删除成功",
  "result": null
}
```

**错误响应**（商品不存在）:
```json
{
  "status": "error",
  "message": "商品不存在或删除失败",
  "result": null
}
```

### 业务说明

删除商品时，会同时删除该商品下的所有关联规格。

---

### 7.X.8 获取商品的所有规格

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/{product_id}/specs` |
| **Method** | GET |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认50，最大100） |

### 请求示例

```
GET /api/v1/products/507f1f77bcf86cd799439012/specs?page=1&page_size=50
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 50,
    "items": [
      {
        "id": "507f1f77bcf86cd799439013",
        "product_id": "507f1f77bcf86cd799439012",
        "spec_code": "SPEC20260420001",
        "packaging": "100g/罐",
        "sales_spec": "100g*24罐/箱",
        "price": 128.00,
        "cas_number": "68917-21-1",
        "is_active": true,
        "stock_quantity": 500,
        "stock_status": "normal",
        "created_at": "2026-04-20T10:00:00",
        "updated_at": "2026-04-20T10:00:00"
      }
    ]
  }
}
```

---

### 7.X.9 为商品创建规格

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/products/{product_id}/specs` |
| **Method** | POST |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| product_id | string | 是 | 商品ID |

### 请求体

```json
{
  "spec_code": "SPEC20260420001",
  "packaging": "100g/罐",
  "sales_spec": "100g*24罐/箱",
  "price": 128.00,
  "cas_number": "68917-21-1",
  "is_active": true
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_code | string | 是 | 规格编号（1-50字符） |
| packaging | string | 否 | 包装（最大100字符） |
| sales_spec | string | 否 | 销售规格（最大100字符） |
| price | float | 是 | 价格（必须大于等于0） |
| cas_number | string | 否 | CAS号（最大50字符） |
| is_active | boolean | 否 | 是否有效（默认true） |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "规格创建成功",
  "result": {
    "id": "507f1f77bcf86cd799439013",
    "product_id": "507f1f77bcf86cd799439012",
    "spec_code": "SPEC20260420001",
    "packaging": "100g/罐",
    "sales_spec": "100g*24罐/箱",
    "price": 128.00,
    "cas_number": "68917-21-1",
    "is_active": true,
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:00:00"
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

### 7.X.10 搜索商品规格

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/specs/search` |
| **Method** | GET |
| **认证** | 需要认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（最小1字符） |
| limit | integer | 否 | 返回数量（默认20，最大50） |

### 请求示例

```
GET /api/v1/products/specs/search?keyword=SPEC001&limit=20
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": [
    {
      "id": "507f1f77bcf86cd799439013",
      "spec_code": "SPEC20260420001",
      "packaging": "100g/罐",
      "sales_spec": "100g*24罐/箱",
      "price": 128.00,
      "product_id": "507f1f77bcf86cd799439012",
      "product_name": "有机红茶",
      "product_code": "PROD20260420001"
    }
  ]
}
```

**返回值字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 规格ID |
| spec_code | string | 规格编号 |
| packaging | string | 包装 |
| sales_spec | string | 销售规格 |
| price | float | 价格 |
| product_id | string | 关联商品ID |
| product_name | string | 关联商品名称 |
| product_code | string | 关联商品编号 |

---

### 7.X.11 获取规格详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/specs/{spec_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

### 请求示例

```
GET /api/v1/products/specs/507f1f77bcf86cd799439013
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": {
    "id": "507f1f77bcf86cd799439013",
    "product_id": "507f1f77bcf86cd799439012",
    "spec_code": "SPEC20260420001",
    "packaging": "100g/罐",
    "sales_spec": "100g*24罐/箱",
    "price": 128.00,
    "cas_number": "68917-21-1",
    "is_active": true,
    "stock_quantity": 500,
    "stock_status": "normal",
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:00:00"
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

### 7.X.12 更新规格

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/products/specs/{spec_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

### 请求体

```json
{
  "spec_code": "SPEC20260420001",
  "packaging": "100g/罐（新版）",
  "sales_spec": "100g*24罐/箱",
  "price": 138.00,
  "cas_number": "68917-21-1",
  "is_active": true
}
```

**请求体字段说明**（所有字段可选）:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_code | string | 否 | 规格编号（1-50字符） |
| packaging | string | 否 | 包装（最大100字符） |
| sales_spec | string | 否 | 销售规格（最大100字符） |
| price | float | 否 | 价格（必须大于等于0） |
| cas_number | string | 否 | CAS号（最大50字符） |
| is_active | boolean | 否 | 是否有效 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "规格更新成功",
  "result": null
}
```

**错误响应**（规格不存在）:
```json
{
  "status": "error",
  "message": "规格不存在或更新失败",
  "result": null
}
```

---

### 7.X.13 删除规格

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/products/specs/{spec_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

### 请求示例

```
DELETE /api/v1/products/specs/507f1f77bcf86cd799439013
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "规格删除成功",
  "result": null
}
```

**错误响应**（规格不存在）:
```json
{
  "status": "error",
  "message": "规格不存在或删除失败",
  "result": null
}
```

---

### 7.X.14 切换规格激活状态

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/products/specs/{spec_id}/toggle-active` |
| **Method** | PATCH |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_active | boolean | 是 | 是否激活 |

### 请求示例

```
PATCH /api/v1/products/specs/507f1f77bcf86cd799439013/toggle-active?is_active=false
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "规格已停用",
  "result": null
}
```

**错误响应**（规格不存在）:
```json
{
  "status": "error",
  "message": "规格不存在或更新失败",
  "result": null
}
```

---

### 7.X.15 获取规格库存明细

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/specs/{spec_id}/stock-detail` |
| **Method** | GET |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 规格ID |

### 请求示例

```
GET /api/v1/products/specs/507f1f77bcf86cd799439013/stock-detail
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": {
    "items": [
      {
        "warehouse_id": "507f1f77bcf86cd799439001",
        "warehouse_name": "北京仓库",
        "quantity": 300
      },
      {
        "warehouse_id": "507f1f77bcf86cd799439002",
        "warehouse_name": "上海仓库",
        "quantity": 200
      }
    ],
    "total_quantity": 500
  }
}
```

---

### 7.X.16 获取所有规格列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/products/all-specs/` |
| **Method** | GET |
| **认证** | 需要认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认50，最大100） |
| keyword | string | 否 | 规格编号关键词（模糊匹配） |
| product_keyword | string | 否 | 商品编码关键词（模糊匹配，筛选指定商品的规格） |

### 请求示例

```
GET /api/v1/products/all-specs/?page=1&page_size=50&keyword=SPEC
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 50,
    "items": [
      {
        "id": "507f1f77bcf86cd799439013",
        "product_id": "507f1f77bcf86cd799439012",
        "spec_code": "SPEC20260420001",
        "packaging": "100g/罐",
        "sales_spec": "100g*24罐/箱",
        "price": 128.00,
        "cas_number": "68917-21-1",
        "is_active": true,
        "stock_quantity": 500,
        "stock_status": "normal",
        "created_at": "2026-04-20T10:00:00",
        "updated_at": "2026-04-20T10:00:00"
      }
    ]
  }
}
```

---

## 数据模型

### Product（商品）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 商品ID（MongoDB ObjectId） |
| product_code | string | 商品编号 |
| name | string | 商品名称 |
| image_url | string | 商品图片URL |
| brand_id | string | 品牌ID |
| brand_name | string | 品牌名称 |
| category_id | string | 分类ID |
| category_name | string | 分类名称 |
| tax_code | string | 税务编码 |
| is_active | boolean | 是否有效 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| specs | array | 商品规格列表 |

### ProductSpec（商品规格）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 规格ID |
| product_id | string | 关联商品ID |
| spec_code | string | 规格编号 |
| packaging | string | 包装 |
| sales_spec | string | 销售规格 |
| price | float | 价格 |
| cas_number | string | CAS号 |
| is_active | boolean | 是否有效 |
| stock_quantity | integer | 库存数量 |
| stock_status | string | 库存状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### ProductListResponse（商品列表响应）

| 字段 | 类型 | 描述 |
|------|------|------|
| total | integer | 总记录数 |
| page | integer | 当前页码 |
| page_size | integer | 每页记录数 |
| items | array | 商品列表 |

### ProductSpecListResponse（规格列表响应）

| 字段 | 类型 | 描述 |
|------|------|------|
| total | integer | 总记录数 |
| page | integer | 当前页码 |
| page_size | integer | 每页记录数 |
| items | array | 规格列表 |

---

## 业务规则

1. **商品规格关联**: 每个商品可以拥有多个规格，规格与商品是一对多关系
2. **级联删除**: 删除商品时，会同时删除该商品下的所有关联规格
3. **规格独立管理**: 规格可以独立进行 CRUD 操作
4. **库存聚合**: 规格的库存数量是多个仓库库存的聚合总和
5. **激活状态**: 可以单独控制商品或规格的激活状态

---

## 权限说明

商品管理接口需要以下权限：

| 接口 | 所需权限 |
|------|----------|
| 创建商品 | `product.create` |
| 获取商品列表 | `product.view` |
| 获取商品统计信息 | `product.view` |
| 搜索商品 | `product.view` |
| 获取商品详情 | `product.view` |
| 更新商品 | `product.edit` |
| 删除商品 | `product.delete` |
| 获取商品规格列表 | `product.view` |
| 创建商品规格 | `product.create` |
| 搜索商品规格 | `product.view` |
| 获取规格详情 | `product.view` |
| 更新规格 | `product.edit` |
| 删除规格 | `product.delete` |
| 切换规格激活状态 | `product.edit` |
| 获取规格库存明细 | `product.view` |
| 获取所有规格列表 | `product.view` |

---

## 接口规范化说明

### 统一响应格式

所有接口均遵循统一的响应格式：

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {}
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

### 2026-05-01 规范化更新

本次更新将所有商品管理接口统一为规范化的响应格式：

| 接口 | 修复前 | 修复后 |
|------|--------|--------|
| 获取商品列表 | 直接返回 `{total, items}` | `{status: "success", result: {total, items}}` |
| 获取商品详情 | 直接返回 Product 对象 | `{status: "success", result: {...}}` |
| 获取商品规格列表 | 直接返回 `{total, items}` | `{status: "success", result: {total, items}}` |
| 获取规格详情 | 直接返回 ProductSpec 对象 | `{status: "success", result: {...}}` |
| 获取所有规格列表 | 直接返回 `{total, items}` | `{status: "success", result: {total, items}}` |

### 前端适配说明

前端代码需要按照新的响应格式访问数据：

```javascript
// 列表接口
const res = await productApi.list(params)
const items = res.result?.items || []
const total = res.result?.total || 0

// 详情接口
const res = await productApi.getById(id)
const product = res.result

// 搜索接口（已兼容）
const res = await productApi.search(keyword, limit)
const items = res.result || []
```


