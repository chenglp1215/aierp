# 库存管理 API

> 管理仓库信息和库存数据，支持仓库CRUD、库存出入库、批次记录查询
> 
> 路由装饰器统一使用 `success_response`、`error_response`、`handle_result` 从 `app.decorators` 导入

## 基础信息

- **基础路径**: `/api/v1`
- **认证方式**: Bearer Token (JWT)
- **子模块路由**:
  - 仓库管理: `/api/v1/warehouses`
  - 库存管理: `/api/v1/stocks`
  - 入库批次: `/api/v1/inbound-batches`
  - 出库批次: `/api/v1/outbound-batches`

---

## HTTP 状态码规范

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 401 | 未认证或认证失效 |
| 5XX | 服务器内部错误 |

---

## 统一响应格式

### 成功响应格式

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {}
}
```

### 错误响应格式

```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

### 列表响应格式

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

## 一、仓库管理接口

### 1.1 创建仓库

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/warehouses/` |
| **Method** | POST |
| **认证** | 需要认证 |
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
| manager_id | string | 否 | 仓库管理员用户ID（关联users表） |
| manager_name | string | 否 | 仓库管理员姓名 |
| status | string | 否 | 仓库状态：`active`/`inactive`/`maintenance`（默认`active`） |
| description | string | 否 | 仓库描述 |

**成功响应**（201）:

```json
{
  "status": "success",
  "message": "仓库创建成功",
  "result": {
    "code": "WH20260501001"
  }
}
```

---

### 1.2 获取仓库列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/warehouses/` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `warehouse.view` |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |
| status | string | 否 | 仓库状态筛选：`active`/`inactive`/`maintenance` |
| keyword | string | 否 | 搜索关键词（仓库名称或地址模糊匹配） |

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
        "created_at": "2026-04-20T10:00:00",
        "updated_at": "2026-04-20T10:00:00"
      }
    ]
  }
}
```

---

### 1.3 搜索仓库（模糊匹配）

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/warehouses/search` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `warehouse.view` |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（至少1个字符） |
| limit | integer | 否 | 返回数量限制（默认10，最大50） |

**成功响应**:

```json
{
  "status": "success",
  "result": [
    {
      "id": "507f1f77bcf86cd799439020",
      "warehouse_code": "WH20260420001",
      "name": "深圳中心仓",
      "address": "深圳市宝安区福永街道128号",
      "status": "active"
    }
  ]
}
```

---

### 1.4 获取仓库管理员候选人

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/warehouses/manager-candidates` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `warehouse.view` |

**说明**: 返回具有 `warehouse_admin` 角色的活跃用户列表，用于仓库管理员选择。

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 否 | 搜索关键词（姓名或用户名模糊匹配） |

**成功响应**:

```json
{
  "status": "success",
  "result": [
    {
      "id": "507f1f77bcf86cd799439011",
      "username": "liming",
      "full_name": "李明"
    }
  ]
}
```

---

### 1.5 获取仓库详情

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/warehouses/{warehouse_code}` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `warehouse.view` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_code | string | 是 | 仓库编码 |

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
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-20T10:00:00"
  }
}
```

**错误响应**（仓库不存在）:

```json
{
  "status": "error",
  "message": "仓库不存在",
  "result": null
}
```

---

### 1.6 更新仓库

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/warehouses/{warehouse_code}` |
| **Method** | PUT |
| **认证** | 需要认证 |
| **权限** | `warehouse.edit` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_code | string | 是 | 仓库编码 |

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

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 仓库名称（1-100字符） |
| address | string | 否 | 仓库地址（1-500字符） |
| manager_id | string | 否 | 仓库管理员用户ID |
| manager_name | string | 否 | 仓库管理员姓名 |
| status | string | 否 | 仓库状态 |
| description | string | 否 | 仓库描述 |

**成功响应**:

```json
{
  "status": "success",
  "message": "仓库更新成功",
  "result": null
}
```

**错误响应**（仓库不存在）:

```json
{
  "status": "error",
  "message": "仓库不存在或更新失败",
  "result": null
}
```

---

### 1.7 删除仓库

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/warehouses/{warehouse_code}` |
| **Method** | DELETE |
| **认证** | 需要认证 |
| **权限** | `warehouse.delete` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_code | string | 是 | 仓库编码 |

**成功响应**:

```json
{
  "status": "success",
  "message": "仓库删除成功",
  "result": null
}
```

**错误响应**（仓库不存在）:

```json
{
  "status": "error",
  "message": "仓库不存在或删除失败",
  "result": null
}
```

---

### 1.8 更新仓库状态

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/warehouses/{warehouse_code}/status` |
| **Method** | PATCH |
| **认证** | 需要认证 |
| **权限** | `warehouse.edit` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| warehouse_code | string | 是 | 仓库编码 |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| status | string | 是 | 新状态：`active`/`inactive`/`maintenance` |

**成功响应**:

```json
{
  "status": "success",
  "message": "仓库状态更新成功",
  "result": null
}
```

**错误响应**（无效状态）:

```json
{
  "status": "error",
  "message": "无效的仓库状态",
  "result": null
}
```

---

## 二、库存管理接口

### 2.1 创建库存

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/stocks/` |
| **Method** | POST |
| **认证** | 需要认证 |
| **权限** | `stock.create` |

**请求体**:

```json
{
  "spec_id": "507f1f77bcf86cd799439030",
  "warehouse_id": "507f1f77bcf86cd799439020",
  "quantity": 100,
  "min_stock": 10,
  "max_stock": 500
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| spec_id | string | 是 | 商品规格ID |
| warehouse_id | string | 是 | 仓库ID |
| quantity | float | 否 | 初始库存数量（默认0） |
| min_stock | float | 否 | 最小库存警告阈值（默认0） |
| max_stock | float | 否 | 最大库存警告阈值（默认0） |

**成功响应**（201）:

```json
{
  "status": "success",
  "message": "库存创建成功",
  "result": {
    "id": "507f1f77bcf86cd799439040"
  }
}
```

**重复库存响应**:

```json
{
  "status": "duplicate",
  "message": "该仓库中已存在此规格的库存记录",
  "result": {
    "existing_id": "507f1f77bcf86cd799439040"
  }
}
```

---

### 2.2 获取库存列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/stocks/` |
| **Method** | GET |
| **认证** | 需要认证 |
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
| keyword | string | 否 | 关键词搜索（商品名称或编号模糊匹配） |

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
        "spec_id": "507f1f77bcf86cd799439030",
        "warehouse_id": "507f1f77bcf86cd799439020",
        "quantity": 100,
        "min_stock": 10,
        "max_stock": 500,
        "status": "normal",
        "spec": {
          "spec_id": "507f1f77bcf86cd799439030",
          "spec_code": "SP001-A",
          "packaging": "100片/盒",
          "sales_spec": "盒",
          "price": 25.5
        },
        "product": {
          "product_id": "507f1f77bcf86cd799439010",
          "product_code": "P2026010001",
          "product_name": "一次性医用口罩",
          "category": "医疗器械"
        },
        "warehouse": {
          "warehouse_id": "507f1f77bcf86cd799439020",
          "warehouse_code": "WH20260420001",
          "warehouse_name": "深圳中心仓"
        },
        "created_at": "2026-04-20T10:00:00",
        "updated_at": "2026-04-28T15:30:00"
      }
    ]
  }
}
```

---

### 2.3 获取库存统计

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/stocks/stats` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `stock.view` |

**成功响应**:

```json
{
  "status": "success",
  "result": {
    "total_count": 150,
    "normal_count": 120,
    "low_stock_count": 20,
    "out_of_stock_count": 5,
    "overstock_count": 5
  }
}
```

---

### 2.4 搜索库存（模糊匹配）

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/stocks/search` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `stock.view` |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词（至少1个字符） |
| limit | integer | 否 | 返回数量限制（默认10，最大50） |

**成功响应**:

```json
{
  "status": "success",
  "result": [
    {
      "id": "507f1f77bcf86cd799439040",
      "spec_id": "507f1f77bcf86cd799439030",
      "warehouse_id": "507f1f77bcf86cd799439020",
      "quantity": 100,
      "status": "normal",
      "spec": { "spec_code": "SP001-A", "packaging": "100片/盒" },
      "product": { "product_code": "P2026010001", "product_name": "一次性医用口罩" },
      "warehouse": { "warehouse_name": "深圳中心仓" }
    }
  ]
}
```

---

### 2.5 获取库存详情

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/stocks/{stock_id}` |
| **Method** | GET |
| **认证** | 需要认证 |
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
    "spec_id": "507f1f77bcf86cd799439030",
    "warehouse_id": "507f1f77bcf86cd799439020",
    "quantity": 100,
    "min_stock": 10,
    "max_stock": 500,
    "status": "normal",
    "spec": { "...": "..." },
    "product": { "...": "..." },
    "warehouse": { "...": "..." },
    "created_at": "2026-04-20T10:00:00",
    "updated_at": "2026-04-28T15:30:00"
  }
}
```

**错误响应**（库存不存在）:

```json
{
  "status": "error",
  "message": "库存不存在",
  "result": null
}
```

---

### 2.6 获取库存详细信息（含出入库记录）

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/stocks/{stock_id}/detail` |
| **Method** | GET |
| **认证** | 需要认证 |
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
    "stock": {
      "id": "507f1f77bcf86cd799439040",
      "spec_id": "507f1f77bcf86cd799439030",
      "warehouse_id": "507f1f77bcf86cd799439020",
      "quantity": 100,
      "min_stock": 10,
      "max_stock": 500,
      "status": "normal"
    },
    "inbound_batches": [
      {
        "id": "507f1f77bcf86cd799439030",
        "inventory_id": "507f1f77bcf86cd799439040",
        "quantity": 200,
        "operator_name": "张三",
        "remarks": "采购入库",
        "created_at": "2026-04-20T10:00:00"
      }
    ],
    "outbound_batches": [
      {
        "id": "507f1f77bcf86cd799439031",
        "inventory_id": "507f1f77bcf86cd799439040",
        "quantity": 100,
        "operator_name": "李四",
        "remarks": "销售出库",
        "created_at": "2026-04-28T14:00:00"
      }
    ]
  }
}
```

---

### 2.7 更新库存

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/stocks/{stock_id}` |
| **Method** | PUT |
| **认证** | 需要认证 |
| **权限** | `stock.edit` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| stock_id | string | 是 | 库存ID |

**请求体**:

```json
{
  "quantity": 200,
  "min_stock": 20,
  "max_stock": 600,
  "status": "normal"
}
```

**请求体字段说明**:

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| quantity | float | 否 | 当前库存数量 |
| min_stock | float | 否 | 最小库存警告阈值 |
| max_stock | float | 否 | 最大库存警告阈值 |
| status | string | 否 | 库存状态：`normal`/`low_stock`/`out_of_stock`/`overstock` |

**成功响应**:

```json
{
  "status": "success",
  "message": "库存更新成功",
  "result": null
}
```

---

### 2.8 删除库存

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/stocks/{stock_id}` |
| **Method** | DELETE |
| **认证** | 需要认证 |
| **权限** | `stock.delete` |

**成功响应**:

```json
{
  "status": "success",
  "message": "库存删除成功",
  "result": null
}
```

---

### 2.9 入库操作

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/stocks/{stock_id}/inbound` |
| **Method** | POST |
| **认证** | 需要认证 |
| **说明** | 操作人信息自动从当前登录用户获取 |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| stock_id | string | 是 | 库存ID |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| quantity | float | 是 | 入库数量（必须大于0） |
| remarks | string | 否 | 备注信息 |

**成功响应**:

```json
{
  "status": "success",
  "message": "入库成功",
  "result": {
    "new_quantity": 300,
    "batch_id": "507f1f77bcf86cd799439050"
  }
}
```

**错误响应**（库存不存在）:

```json
{
  "status": "error",
  "message": "库存不存在",
  "result": null
}
```

---

### 2.10 出库操作

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/stocks/{stock_id}/outbound` |
| **Method** | POST |
| **认证** | 需要认证 |
| **说明** | 操作人信息自动从当前登录用户获取 |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| stock_id | string | 是 | 库存ID |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| quantity | float | 是 | 出库数量（必须大于0） |
| remarks | string | 否 | 备注信息 |

**成功响应**:

```json
{
  "status": "success",
  "message": "出库成功",
  "result": {
    "new_quantity": 200,
    "batch_id": "507f1f77bcf86cd799439051"
  }
}
```

**错误响应**（库存不足）:

```json
{
  "status": "error",
  "message": "库存不足，当前库存: 100，出库数量: 200",
  "result": null
}
```

---

## 三、出入库批次查询接口

### 3.1 获取入库批次列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/inbound-batches/by-stock/{stock_id}` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `stock.view` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| stock_id | string | 是 | 库存ID |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |

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
        "id": "507f1f77bcf86cd799439030",
        "inventory_id": "507f1f77bcf86cd799439040",
        "quantity": 200,
        "operator_id": "507f1f77bcf86cd799439011",
        "operator_name": "张三",
        "remarks": "采购入库",
        "created_at": "2026-04-20T10:00:00"
      }
    ]
  }
}
```

---

### 3.2 获取出库批次列表

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/outbound-batches/by-stock/{stock_id}` |
| **Method** | GET |
| **认证** | 需要认证 |
| **权限** | `stock.view` |

**路径参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| stock_id | string | 是 | 库存ID |

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认20，最大100） |

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
        "id": "507f1f77bcf86cd799439031",
        "inventory_id": "507f1f77bcf86cd799439040",
        "quantity": 100,
        "operator_id": "507f1f77bcf86cd799439012",
        "operator_name": "李四",
        "remarks": "销售出库",
        "created_at": "2026-04-28T14:00:00"
      }
    ]
  }
}
```

---

## 数据模型

### Warehouse（仓库）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 仓库ID（MongoDB ObjectId） |
| warehouse_code | string | 仓库编码（系统自动生成，如 WH20260420001） |
| name | string | 仓库名称 |
| address | string | 仓库地址 |
| manager_id | string | 仓库管理员用户ID |
| manager_name | string | 仓库管理员姓名 |
| status | string | 仓库状态：`active`/`inactive`/`maintenance` |
| description | string | 仓库描述 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### Stock（库存）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 库存ID |
| spec_id | string | 商品规格ID |
| warehouse_id | string | 仓库ID |
| quantity | float | 当前库存数量 |
| min_stock | float | 最小库存警告阈值 |
| max_stock | float | 最大库存警告阈值 |
| status | string | 库存状态：`normal`/`low_stock`/`out_of_stock`/`overstock` |
| spec | object | 规格信息（关联查询） |
| product | object | 商品信息（关联查询） |
| warehouse | object | 仓库信息（关联查询） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### InboundBatch（入库批次）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 入库批次ID |
| inventory_id | string | 关联库存ID |
| quantity | float | 入库数量 |
| operator_id | string | 操作人ID |
| operator_name | string | 操作人姓名 |
| remarks | string | 备注 |
| created_at | datetime | 入库时间 |

### OutboundBatch（出库批次）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 出库批次ID |
| inventory_id | string | 关联库存ID |
| quantity | float | 出库数量 |
| operator_id | string | 操作人ID |
| operator_name | string | 操作人姓名 |
| remarks | string | 备注 |
| created_at | datetime | 出库时间 |

---

## 权限说明

| 接口 | 所需权限 |
|------|----------|
| 创建仓库 | `warehouse.create` |
| 获取仓库列表 | `warehouse.view` |
| 搜索仓库 | `warehouse.view` |
| 获取仓库管理员候选人 | `warehouse.view` |
| 获取仓库详情 | `warehouse.view` |
| 更新仓库 | `warehouse.edit` |
| 删除仓库 | `warehouse.delete` |
| 更新仓库状态 | `warehouse.edit` |
| 创建库存 | `stock.create` |
| 获取库存列表 | `stock.view` |
| 获取库存统计 | `stock.view` |
| 搜索库存 | `stock.view` |
| 获取库存详情 | `stock.view` |
| 获取库存详细信息 | `stock.view` |
| 更新库存 | `stock.edit` |
| 删除库存 | `stock.delete` |
| 入库操作 | 需要登录（自动记录操作人） |
| 出库操作 | 需要登录（自动记录操作人） |
| 查询入库批次 | `stock.view` |
| 查询出库批次 | `stock.view` |
