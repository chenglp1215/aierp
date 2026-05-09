# 库存管理 API

> 管理仓库、库存、出入库批次记录
>
> 路由装饰器统一使用 `@wrap_response` 从 `app.decorators` 导入

## 基础信息

- **基础路径**: `/api/v1`
- **认证方式**: Bearer Token (JWT)
- **子模块路由**:
  - 仓库管理: `/api/v1/warehouses`
  - 库存管理: `/api/v1/stocks`
  - 入库批次: `/api/v1/inbound-batches`
  - 出库批次: `/api/v1/outbound-batches`

---

## 统一响应格式

### 成功响应

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {}
}
```

### 错误响应

```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

### 列表响应

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": []
  }
}
```

---

## 一、仓库管理

### 1.1 获取仓库列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/warehouses/` |
| **权限** | `warehouse.view` |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| status | string | 否 | 仓库状态筛选：`active`/`inactive`/`maintenance` |
| keyword | string | 否 | 搜索关键词（仓库编码或名称模糊匹配） |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 10,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439020",
        "warehouse_code": "WH20260420001",
        "name": "深圳中心仓",
        "address": "深圳市宝安区福永街道128号",
        "manager_id": "507f1f77bcf86cd799439011",
        "manager_name": "李明",
        "status": "active",
        "description": "深圳地区主仓库",
        "created_at": "2026-04-28T10:00:00",
        "updated_at": "2026-04-28T10:00:00"
      }
    ]
  }
}
```

---

### 1.2 创建仓库

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/warehouses/` |
| **权限** | `warehouse.create` |

**请求体**:

```json
{
  "name": "深圳中心仓",
  "address": "深圳市宝安区福永街道128号",
  "manager_id": "507f1f77bcf86cd799439011",
  "manager_name": "李明",
  "status": "active",
  "description": "深圳地区主仓库"
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 是 | 仓库名称（1-100字符） |
| address | string | 是 | 仓库地址（1-500字符） |
| warehouse_code | string | 否 | 仓库编码（留空则自动生成，格式 `WH{日期}{6位随机数}`） |
| manager_id | string | 否 | 仓库管理员用户ID |
| manager_name | string | 否 | 仓库管理员姓名 |
| status | string | 否 | 仓库状态：`active`/`inactive`/`maintenance`（默认`active`） |
| description | string | 否 | 仓库描述（最多500字符） |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "507f1f77bcf86cd799439020",
    "warehouse_code": "WH20260501001",
    "name": "深圳中心仓",
    "address": "深圳市宝安区福永街道128号",
    "manager_id": "507f1f77bcf86cd799439011",
    "manager_name": "李明",
    "status": "active",
    "description": "深圳地区主仓库",
    "created_at": "2026-05-01T10:00:00",
    "updated_at": "2026-05-01T10:00:00"
  }
}
```

---

### 1.3 获取仓库详情

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/warehouses/{warehouse_id}` |
| **权限** | `warehouse.view` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_id | string | 是 | 仓库ID |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "507f1f77bcf86cd799439020",
    "warehouse_code": "WH20260420001",
    "name": "深圳中心仓",
    "address": "深圳市宝安区福永街道128号",
    "manager_id": "507f1f77bcf86cd799439011",
    "manager_name": "李明",
    "status": "active",
    "description": "深圳地区主仓库",
    "created_at": "2026-04-28T10:00:00",
    "updated_at": "2026-04-28T10:00:00"
  }
}
```

**错误响应**:

```json
{
  "status": "error",
  "message": "仓库不存在",
  "result": null
}
```

---

### 1.4 更新仓库

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/warehouses/{warehouse_id}` |
| **权限** | `warehouse.edit` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_id | string | 是 | 仓库ID |

**请求体**:

```json
{
  "name": "深圳中心仓（更新）",
  "address": "深圳市宝安区新地址128号",
  "manager_id": "507f1f77bcf86cd799439011",
  "manager_name": "李明",
  "status": "active",
  "description": "更新后的描述"
}
```

**请求体字段说明**（均为选填，仅传需要修改的字段）:

| 字段 | 类型 | 描述 |
|------|------|------|
| name | string | 仓库名称（1-100字符） |
| address | string | 仓库地址（1-500字符） |
| manager_id | string | 仓库管理员用户ID |
| manager_name | string | 仓库管理员姓名 |
| status | string | 仓库状态 |
| description | string | 仓库描述 |

> 注意：`warehouse_code`、`created_at`、`updated_at`、`id` 不可修改。

**成功响应**:

```json
{
  "status": "success",
  "message": "仓库更新成功",
  "result": null
}
```

---

---

## 二、库存管理

### 2.1 获取库存列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/stocks/` |
| **权限** | `stock.view` |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| warehouse_id | string | 否 | 仓库ID筛选 |
| product_id | string | 否 | 商品ID筛选 |
| spec_id | string | 否 | 规格ID筛选 |
| status | string | 否 | 库存状态：`normal`/`low_stock`/`out_of_stock`/`overstock` |
| keyword | string | 否 | 关键词搜索（商品编号、商品名称或规格编号模糊匹配） |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439040",
        "warehouse_id": "507f1f77bcf86cd799439020",
        "product_id": "507f1f77bcf86cd799439010",
        "product_code": "P2026010001",
        "product_name": "一次性医用口罩",
        "spec_id": "507f1f77bcf86cd799439030",
        "spec_code": "SP001-A",
        "quantity": 100,
        "min_stock": 10,
        "max_stock": 500,
        "status": "normal",
        "product_info": {
          "id": "507f1f77bcf86cd799439010",
          "product_code": "P2026010001",
          "name": "一次性医用口罩",
          "brand_id": "507f1f77bcf86cd799439005",
          "category_id": "507f1f77bcf86cd799439008"
        },
        "spec_info": {
          "id": "507f1f77bcf86cd799439030",
          "spec_code": "SP001-A",
          "packaging": "100片/盒",
          "sales_spec": "盒",
          "price": 25.5
        },
        "warehouse_info": {
          "id": "507f1f77bcf86cd799439020",
          "warehouse_code": "WH20260420001",
          "name": "深圳中心仓"
        },
        "created_at": "2026-04-20T10:00:00",
        "updated_at": "2026-04-28T15:30:00"
      }
    ]
  }
}
```

---

### 2.2 获取库存详情

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/stocks/{stock_id}` |
| **权限** | `stock.view` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| stock_id | string | 是 | 库存ID |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "507f1f77bcf86cd799439040",
    "warehouse_id": "507f1f77bcf86cd799439020",
    "product_id": "507f1f77bcf86cd799439010",
    "product_code": "P2026010001",
    "product_name": "一次性医用口罩",
    "spec_id": "507f1f77bcf86cd799439030",
    "spec_code": "SP001-A",
    "quantity": 100,
    "min_stock": 10,
    "max_stock": 500,
    "status": "normal",
    "product_info": { "..." : "..." },
    "spec_info": { "..." : "..." },
    "warehouse_info": { "..." : "..." },
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-28T15:30:00"
  }
}
```

**错误响应**:

```json
{
  "status": "error",
  "message": "库存不存在",
  "result": null
}
```

---

### 2.3 更新库存（手动盘库）

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/stocks/{stock_id}` |
| **权限** | `stock.edit` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| stock_id | string | 是 | 库存ID |

**请求体**（仅支持以下字段，传入其他字段会被忽略）:

```json
{
  "quantity": 200,
  "min_stock": 20,
  "max_stock": 600
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| quantity | float | 否 | 当前库存数量（≥0） |
| min_stock | float | 否 | 最小库存警告阈值（≥0） |
| max_stock | float | 否 | 最大库存警告阈值（≥0） |

**成功响应**:

```json
{
  "status": "success",
  "message": "库存更新成功",
  "result": null
}
```

**错误响应**:

```json
{
  "status": "error",
  "message": "库存不存在",
  "result": null
}
```

---

## 三、入库批次管理

### 3.1 获取入库批次列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/inbound-batches/` |
| **权限** | `inbound.view` |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| stock_id | string | 否 | 库存ID筛选 |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 25,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439050",
        "warehouse_id": "507f1f77bcf86cd799439020",
        "product_id": "507f1f77bcf86cd799439010",
        "product_code": "P2026010001",
        "product_name": "一次性医用口罩",
        "spec_id": "507f1f77bcf86cd799439030",
        "spec_code": "SP001-A",
        "stock_id": "507f1f77bcf86cd799439040",
        "quantity": 200,
        "user_id": "507f1f77bcf86cd799439011",
        "user_name": "张三",
        "created_at": "2026-04-20T10:00:00",
        "updated_at": "2026-04-20T10:00:00"
      }
    ]
  }
}
```

---

### 3.2 创建入库批次

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/inbound-batches/` |
| **权限** | `inbound.create` |

**请求体**:

```json
{
  "warehouse_id": "507f1f77bcf86cd799439020",
  "product_id": "507f1f77bcf86cd799439010",
  "product_code": "P2026010001",
  "product_name": "一次性医用口罩",
  "spec_id": "507f1f77bcf86cd799439030",
  "spec_code": "SP001-A",
  "quantity": 200,
  "user_id": "507f1f77bcf86cd799439011",
  "user_name": "张三"
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_id | string | 是 | 仓库ID |
| product_id | string | 是 | 商品ID |
| product_code | string | 是 | 商品编号 |
| product_name | string | 是 | 商品名称 |
| spec_id | string | 是 | 规格ID |
| spec_code | string | 是 | 规格编号 |
| stock_id | string | 否 | 库存ID（为空时根据仓库+商品+规格自动创建或关联库存） |
| quantity | float | 是 | 入库数量（≥0） |
| user_id | string | 是 | 操作用户ID |
| user_name | string | 是 | 操作用户姓名 |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "507f1f77bcf86cd799439050",
    "warehouse_id": "507f1f77bcf86cd799439020",
    "product_id": "507f1f77bcf86cd799439010",
    "product_code": "P2026010001",
    "product_name": "一次性医用口罩",
    "spec_id": "507f1f77bcf86cd799439030",
    "spec_code": "SP001-A",
    "stock_id": "507f1f77bcf86cd799439040",
    "quantity": 200,
    "user_id": "507f1f77bcf86cd799439011",
    "user_name": "张三"
  }
}
```

---

### 3.3 获取入库批次详情

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/inbound-batches/{batch_id}` |
| **权限** | `inbound.view` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| batch_id | string | 是 | 入库批次ID |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "507f1f77bcf86cd799439050",
    "warehouse_id": "507f1f77bcf86cd799439020",
    "product_id": "507f1f77bcf86cd799439010",
    "product_code": "P2026010001",
    "product_name": "一次性医用口罩",
    "spec_id": "507f1f77bcf86cd799439030",
    "spec_code": "SP001-A",
    "stock_id": "507f1f77bcf86cd799439040",
    "quantity": 200,
    "user_id": "507f1f77bcf86cd799439011",
    "user_name": "张三",
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:00:00"
  }
}
```

**错误响应**:

```json
{
  "status": "error",
  "message": "入库批次不存在",
  "result": null
}
```

---

### 3.4 更新入库批次

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/inbound-batches/{batch_id}` |
| **权限** | `inbound.edit` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| batch_id | string | 是 | 入库批次ID |

**请求体**（均为选填）:

| 字段 | 类型 | 描述 |
|------|------|------|
| warehouse_id | string | 仓库ID |
| product_id | string | 商品ID |
| product_code | string | 商品编号 |
| product_name | string | 商品名称 |
| spec_id | string | 规格ID |
| spec_code | string | 规格编号 |
| stock_id | string | 库存ID |
| quantity | float | 入库数量（≥0） |
| user_id | string | 操作用户ID |
| user_name | string | 操作用户姓名 |

**成功响应**:

```json
{
  "status": "success",
  "message": "入库批次更新成功",
  "result": null
}
```

---

---

## 四、出库批次管理

### 4.1 获取出库批次列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/outbound-batches/` |
| **权限** | `outbound.view` |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| stock_id | string | 否 | 库存ID筛选 |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 15,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439060",
        "warehouse_id": "507f1f77bcf86cd799439020",
        "product_id": "507f1f77bcf86cd799439010",
        "product_code": "P2026010001",
        "product_name": "一次性医用口罩",
        "spec_id": "507f1f77bcf86cd799439030",
        "spec_code": "SP001-A",
        "stock_id": "507f1f77bcf86cd799439040",
        "quantity": 100,
        "user_id": "507f1f77bcf86cd799439012",
        "user_name": "李四",
        "created_at": "2026-04-28T14:00:00",
        "updated_at": "2026-04-28T14:00:00"
      }
    ]
  }
}
```

---

### 4.2 创建出库批次

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/outbound-batches/` |
| **权限** | `outbound.create` |

**请求体**:

```json
{
  "warehouse_id": "507f1f77bcf86cd799439020",
  "product_id": "507f1f77bcf86cd799439010",
  "product_code": "P2026010001",
  "product_name": "一次性医用口罩",
  "spec_id": "507f1f77bcf86cd799439030",
  "spec_code": "SP001-A",
  "stock_id": "507f1f77bcf86cd799439040",
  "quantity": 100,
  "user_id": "507f1f77bcf86cd799439012",
  "user_name": "李四"
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_id | string | 是 | 仓库ID |
| product_id | string | 是 | 商品ID |
| product_code | string | 是 | 商品编号 |
| product_name | string | 是 | 商品名称 |
| spec_id | string | 是 | 规格ID |
| spec_code | string | 是 | 规格编号 |
| stock_id | string | 是 | 库存ID |
| quantity | float | 是 | 出库数量（≥0） |
| user_id | string | 是 | 操作用户ID |
| user_name | string | 是 | 操作用户姓名 |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "507f1f77bcf86cd799439060",
    "warehouse_id": "507f1f77bcf86cd799439020",
    "product_id": "507f1f77bcf86cd799439010",
    "product_code": "P2026010001",
    "product_name": "一次性医用口罩",
    "spec_id": "507f1f77bcf86cd799439030",
    "spec_code": "SP001-A",
    "stock_id": "507f1f77bcf86cd799439040",
    "quantity": 100,
    "user_id": "507f1f77bcf86cd799439012",
    "user_name": "李四"
  }
}
```

---

### 4.3 获取出库批次详情

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/outbound-batches/{batch_id}` |
| **权限** | `outbound.view` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| batch_id | string | 是 | 出库批次ID |

**成功响应**:

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "507f1f77bcf86cd799439060",
    "warehouse_id": "507f1f77bcf86cd799439020",
    "product_id": "507f1f77bcf86cd799439010",
    "product_code": "P2026010001",
    "product_name": "一次性医用口罩",
    "spec_id": "507f1f77bcf86cd799439030",
    "spec_code": "SP001-A",
    "stock_id": "507f1f77bcf86cd799439040",
    "quantity": 100,
    "user_id": "507f1f77bcf86cd799439012",
    "user_name": "李四",
    "created_at": "2026-04-28T14:00:00",
    "updated_at": "2026-04-28T14:00:00"
  }
}
```

**错误响应**:

```json
{
  "status": "error",
  "message": "出库批次不存在",
  "result": null
}
```

---

### 4.4 更新出库批次

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/outbound-batches/{batch_id}` |
| **权限** | `outbound.edit` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| batch_id | string | 是 | 出库批次ID |

**请求体**（均为选填）:

| 字段 | 类型 | 描述 |
|------|------|------|
| warehouse_id | string | 仓库ID |
| product_id | string | 商品ID |
| product_code | string | 商品编号 |
| product_name | string | 商品名称 |
| spec_id | string | 规格ID |
| spec_code | string | 规格编号 |
| stock_id | string | 库存ID |
| quantity | float | 出库数量（≥0） |
| user_id | string | 操作用户ID |
| user_name | string | 操作用户姓名 |

**成功响应**:

```json
{
  "status": "success",
  "message": "出库批次更新成功",
  "result": null
}
```

---

---

## 数据模型

### Warehouse（仓库）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 仓库ID |
| warehouse_code | string | 仓库编码（系统自动生成，格式 `WH{日期}{6位随机数}`） |
| name | string | 仓库名称 |
| address | string | 仓库地址 |
| manager_id | string | 仓库管理员用户ID（关联users表） |
| manager_name | string | 管理员姓名（冗余字段，便于显示） |
| status | string | 仓库状态：`active`/`inactive`/`maintenance` |
| description | string | 仓库描述 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Stock（库存）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 库存ID |
| warehouse_id | string | 仓库ID |
| product_id | string | 商品ID |
| product_code | string | 商品编号 |
| product_name | string | 商品名称 |
| spec_id | string | 规格ID |
| spec_code | string | 规格编号 |
| quantity | float | 当前库存数量 |
| min_stock | float | 最小库存警告阈值 |
| max_stock | float | 最大库存警告阈值 |
| status | string | 库存状态：`normal`/`low_stock`/`out_of_stock`/`overstock` |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

格式化后额外字段：

| 字段 | 类型 | 描述 |
|------|------|------|
| product_info | object | 关联商品信息 |
| spec_info | object | 关联规格信息 |
| warehouse_info | object | 关联仓库信息 |

### InboundBatch（入库批次）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 入库批次ID |
| warehouse_id | string | 仓库ID |
| product_id | string | 商品ID |
| product_code | string | 商品编号 |
| product_name | string | 商品名称 |
| spec_id | string | 规格ID |
| spec_code | string | 规格编号 |
| stock_id | string | 库存ID |
| quantity | float | 入库数量 |
| user_id | string | 操作用户ID |
| user_name | string | 操作用户姓名 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### OutboundBatch（出库批次）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 出库批次ID |
| warehouse_id | string | 仓库ID |
| product_id | string | 商品ID |
| product_code | string | 商品编号 |
| product_name | string | 商品名称 |
| spec_id | string | 规格ID |
| spec_code | string | 规格编号 |
| stock_id | string | 库存ID |
| quantity | float | 出库数量 |
| user_id | string | 操作用户ID |
| user_name | string | 操作用户姓名 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 权限说明

| 接口 | 所需权限 |
|------|----------|
| 获取仓库列表 | `warehouse.view` |
| 创建仓库 | `warehouse.create` |
| 获取仓库详情 | `warehouse.view` |
| 更新仓库 | `warehouse.edit` |
| 获取库存列表 | `stock.view` |
| 获取库存详情 | `stock.view` |
| 更新库存（盘库） | `stock.edit` |
| 获取入库批次列表 | `inbound.view` |
| 创建入库批次 | `inbound.create` |
| 获取入库批次详情 | `inbound.view` |
| 更新入库批次 | `inbound.edit` |
| 获取出库批次列表 | `outbound.view` |
| 创建出库批次 | `outbound.create` |
| 获取出库批次详情 | `outbound.view` |
| 更新出库批次 | `outbound.edit` |
