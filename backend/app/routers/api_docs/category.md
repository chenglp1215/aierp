# 商品分类管理 API

> 用于管理商品分类信息，支持三级分类树形结构

## 基础信息

- **基础路径**: `/api/v1/categories`
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

### 6.X.1 创建分类

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/categories/` |
| **Method** | POST |
| **认证** | 需要认证 |

### 请求体

```json
{
  "name": "电子产品",
  "parent_id": null,
  "tax_code": "TAX001",
  "sort_order": 1,
  "is_shop_display": true
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 分类名称（1-100字符） |
| parent_id | string | 否 | 父分类ID，为空则为顶层分类 |
| tax_code | string | 否 | 税务编码（最大50字符） |
| sort_order | integer | 否 | 排序，数字越小越靠前（默认0） |
| is_shop_display | boolean | 否 | 是否商城展示（默认true） |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "分类创建成功",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "电子产品",
    "parent_id": null,
    "tax_code": "TAX001",
    "sort_order": 1,
    "is_shop_display": true,
    "level": 1,
    "created_at": "2026-05-01T10:00:00",
    "updated_at": "2026-05-01T10:00:00"
  }
}
```

**错误响应**（超过三级分类）:
```json
{
  "status": "error",
  "message": "分类最多支持三级",
  "result": null
}
```

**错误响应**（父分类不存在）:
```json
{
  "status": "error",
  "message": "父分类不存在",
  "result": null
}
```

---

### 6.X.2 获取分类列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/categories/` |
| **Method** | GET |
| **认证** | 需要认证 |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| keyword | string | 否 | 搜索关键词（分类名称或税务编码模糊匹配） |
| parent_id | string | 否 | 父分类ID筛选，传空字符串表示顶级分类 |

### 请求示例

```
GET /api/v1/categories/?page=1&page_size=20&keyword=电子
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
      "name": "电子产品",
      "parent_id": null,
      "tax_code": "TAX001",
      "sort_order": 1,
      "is_shop_display": true,
      "level": 1,
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
| items | array | 分类列表 |
| items[].id | string | 分类ID |
| items[].name | string | 分类名称 |
| items[].parent_id | string | 父分类ID |
| items[].tax_code | string | 税务编码 |
| items[].sort_order | integer | 排序权重 |
| items[].is_shop_display | boolean | 是否商城展示 |
| items[].level | integer | 分类层级（1/2/3） |
| items[].created_at | string | 创建时间 |
| items[].updated_at | string | 更新时间 |

---

### 6.X.3 获取分类树形结构

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/categories/tree` |
| **Method** | GET |
| **认证** | 需要认证 |

### 请求示例

```
GET /api/v1/categories/tree
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取分类树形结构成功",
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
          "children": [
            {
              "id": "507f1f77bcf86cd799439013",
              "name": "智能手机",
              "parent_id": "507f1f77bcf86cd799439012",
              "tax_code": "TAX003",
              "sort_order": 1,
              "is_shop_display": true,
              "level": 3,
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

**返回值字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 固定为 "success" |
| message | string | 操作结果描述 |
| result | array | 分类树形结构数组 |
| result[].id | string | 分类ID |
| result[].name | string | 分类名称 |
| result[].parent_id | string | 父分类ID |
| result[].tax_code | string | 税务编码 |
| result[].sort_order | integer | 排序权重 |
| result[].is_shop_display | boolean | 是否商城展示 |
| result[].level | integer | 分类层级（1/2/3） |
| result[].children | array | 子分类列表（递归结构） |

---

### 6.X.4 获取分类详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/categories/{category_id}` |
| **Method** | GET |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| category_id | string | 是 | 分类ID |

### 请求示例

```
GET /api/v1/categories/507f1f77bcf86cd799439011
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "获取分类详情成功",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "电子产品",
    "parent_id": null,
    "tax_code": "TAX001",
    "sort_order": 1,
    "is_shop_display": true,
    "level": 1,
    "created_at": "2026-05-01T10:00:00",
    "updated_at": "2026-05-01T10:00:00"
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

### 6.X.5 更新分类

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/categories/{category_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| category_id | string | 是 | 分类ID |

### 请求体

```json
{
  "name": "电子产品",
  "parent_id": "507f1f77bcf86cd799439010",
  "tax_code": "TAX001",
  "sort_order": 1,
  "is_shop_display": true
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 分类名称（1-100字符） |
| parent_id | string | 否 | 父分类ID，为空则为顶层分类 |
| tax_code | string | 否 | 税务编码（最大50字符） |
| sort_order | integer | 否 | 排序，数字越小越靠前 |
| is_shop_display | boolean | 否 | 是否商城展示 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "分类更新成功",
  "result": null
}
```

**错误响应**（不能将自己设为父分类）:
```json
{
  "status": "error",
  "message": "不能将自己设为父分类",
  "result": null
}
```

**错误响应**（会导致子分类超过三级）:
```json
{
  "status": "error",
  "message": "该操作会导致子分类超过三级限制",
  "result": null
}
```

**错误响应**（分类不存在）:
```json
{
  "status": "error",
  "message": "分类不存在或更新失败",
  "result": null
}
```

---

### 6.X.6 删除分类

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/categories/{category_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| category_id | string | 是 | 分类ID |

### 请求示例

```
DELETE /api/v1/categories/507f1f77bcf86cd799439011
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "分类删除成功",
  "result": null
}
```

**错误响应**（分类下存在子分类）:
```json
{
  "status": "error",
  "message": "该分类下存在子分类，无法删除",
  "result": null
}
```

**错误响应**（分类不存在）:
```json
{
  "status": "error",
  "message": "分类不存在或删除失败",
  "result": null
}
```

---

## 数据模型

### Category（分类）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 分类ID（MongoDB ObjectId） |
| name | string | 分类名称 |
| parent_id | string | 父分类ID，顶级分类为 null |
| tax_code | string | 税务编码 |
| sort_order | integer | 排序权重，数字越小越靠前 |
| is_shop_display | boolean | 是否在商城展示 |
| level | integer | 分类层级（1:一级, 2:二级, 3:三级） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### CategoryTreeNode（分类树节点）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 分类ID |
| name | string | 分类名称 |
| parent_id | string | 父分类ID |
| tax_code | string | 税务编码 |
| sort_order | integer | 排序权重 |
| is_shop_display | boolean | 是否商城展示 |
| level | integer | 分类层级 |
| children | array | 子分类列表（递归） |

### CategoryListResponse（分类列表响应）

| 字段 | 类型 | 描述 |
|------|------|------|
| total | integer | 总记录数 |
| page | integer | 当前页码 |
| page_size | integer | 每页记录数 |
| items | array | 分类列表 |

---

## 业务规则

1. **三级分类限制**: 系统最多支持三级分类（1级 → 2级 → 3级）
2. **父子关系约束**: 更新分类时不能将自己设为父分类
3. **层级联动**: 修改父分类时，系统会自动检查所有子分类是否超过三级限制
4. **删除约束**: 存在子分类的分类不允许删除
5. **排序规则**: 分类按 `sort_order` 字段升序排列，数字越小越靠前

---

## 权限说明

分类管理接口需要以下权限：

| 接口 | 所需权限 |
|------|----------|
| 创建分类 | `category.create` |
| 获取分类列表 | `category.view` |
| 获取分类树形结构 | `category.view` |
| 获取分类详情 | `category.view` |
| 更新分类 | `category.edit` |
| 删除分类 | `category.delete` |
