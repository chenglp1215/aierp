# AI MDR Platform - 后端 API 接口文档

## 概述

本文档描述 AI MDR Platform 后端所有 REST API 接口，包括请求参数、响应结构和错误码。

**基础路径**: `/api/v1`

**认证方式**: Bearer Token (JWT)

**统一响应格式**:
```json
{
  "status": "success",
  "message": "操作描述",
  "result": {}
}
```

**分页响应格式**:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": []
}
```

---

## 目录

1. [认证模块](#1-认证模块-auth)
2. [用户管理](#2-用户管理)
3. [角色管理](#3-角色管理)
4. [权限管理](#4-权限管理)
5. [客户管理](#5-客户管理)
6. [商品管理](#6-商品管理)
7. [仓库管理](#7-仓库管理)
8. [库存管理](#8-库存管理)
9. [销售订单](#9-销售订单)
10. [采购单管理](#10-采购单管理)
11. [应收款管理](#11-应收款管理)
12. [LLM 设置](#12-llm-设置)
13. [知识库设置](#13-知识库设置)
14. [MCP 设置](#14-mcp-设置)
15. [Skills 设置](#15-skills-设置)
16. [Agent 设置](#16-agent-设置)
17. [AI 工具](#17-ai-工具)
18. [文件上传](#18-文件上传)
19. [WebSocket](#19-websocket)
20. [健康检查](#20-健康检查)

---

## 1. 认证模块 (auth)

### 1.1 用户登录

**接口**: `POST /auth/login`

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "status": "success",
  "result": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 1440,
    "user": {
      "id": "string",
      "username": "string",
      "full_name": "string",
      "email": "string",
      "status": "active",
      "roles": []
    }
  }
}
```

**错误码**: 401 - 用户名或密码错误

---

### 1.2 用户注册

**接口**: `POST /auth/register`

**请求体**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string",
  "phone": "string",
  "full_name": "string",
  "role_ids": ["string"]
}
```

**响应**:
```json
{
  "status": "success",
  "message": "注册成功",
  "result": { "id": "string" }
}
```

---

### 1.3 获取当前用户信息

**接口**: `GET /auth/me`

**响应**:
```json
{
  "id": "string",
  "username": "string",
  "full_name": "string",
  "email": "string",
  "phone": "string",
  "status": "active",
  "roles": [],
  "last_login": "datetime"
}
```

---

### 1.4 修改密码

**接口**: `PUT /auth/me/password`

**请求体**:
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**响应**:
```json
{
  "status": "success",
  "message": "密码修改成功"
}
```

---

## 2. 用户管理

### 2.1 获取用户列表

**接口**: `GET /auth/users`

**权限**: `user.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20，最大100 |
| status | string | 否 | 用户状态: active/inactive/locked |
| keyword | string | 否 | 搜索关键词 |

**响应**:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "string",
      "username": "string",
      "full_name": "string",
      "email": "string",
      "phone": "string",
      "status": "active",
      "roles": []
    }
  ]
}
```

---

### 2.2 获取用户详情

**接口**: `GET /auth/users/{user_id}`

**权限**: `user.view`

**响应**: 返回用户完整信息

---

### 2.3 创建用户

**接口**: `POST /auth/users`

**权限**: `user.create`

**请求体**:
```json
{
  "username": "string",
  "password": "string",
  "email": "string",
  "phone": "string",
  "full_name": "string",
  "role_ids": ["string"]
}
```

**响应**:
```json
{
  "status": "success",
  "message": "用户创建成功",
  "result": { "id": "string" }
}
```

---

### 2.4 更新用户

**接口**: `PUT /auth/users/{user_id}`

**权限**: `user.edit`

**请求体**:
```json
{
  "email": "string",
  "phone": "string",
  "full_name": "string",
  "role_ids": ["string"]
}
```

---

### 2.5 删除用户

**接口**: `DELETE /auth/users/{user_id}`

**权限**: `user.delete`

**响应**:
```json
{
  "status": "success",
  "message": "用户删除成功"
}
```

---

### 2.6 重置用户密码

**接口**: `PATCH /auth/users/{user_id}/password`

**权限**: `user.reset-password`

**请求体**:
```json
{
  "new_password": "string"
}
```

---

### 2.7 更新用户状态

**接口**: `PATCH /auth/users/{user_id}/status`

**权限**: `user.edit`

**查询参数**: `status` - 用户状态

---

## 3. 角色管理

### 3.1 获取角色列表

**接口**: `GET /roles`

**权限**: `role.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 角色状态 |
| keyword | string | 否 | 搜索关键词 |

**响应**:
```json
{
  "total": 10,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "string",
      "code": "string",
      "name": "string",
      "description": "string",
      "is_fixed": false,
      "permissions": [],
      "created_at": "datetime"
    }
  ]
}
```

---

### 3.2 获取角色详情

**接口**: `GET /roles/{role_id}`

**权限**: `role.view`

---

### 3.3 创建角色

**接口**: `POST /roles`

**权限**: `role.create`

**请求体**:
```json
{
  "code": "string",
  "name": "string",
  "description": "string",
  "permission_ids": ["string"]
}
```

---

### 3.4 更新角色

**接口**: `PUT /roles/{role_id}`

**权限**: `role.edit`

**请求体**:
```json
{
  "name": "string",
  "description": "string",
  "permission_ids": ["string"]
}
```

**注意**: 固化角色不允许修改

---

### 3.5 删除角色

**接口**: `DELETE /roles/{role_id}`

**权限**: `role.delete`

**注意**: 固化角色不允许删除

---

### 3.6 更新角色状态

**接口**: `PATCH /roles/{role_id}/status`

**权限**: `role.edit`

**查询参数**: `status` - 角色状态

---

## 4. 权限管理

### 4.1 获取权限列表

**接口**: `GET /permissions`

**权限**: `permission.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| keyword | string | 否 | 搜索关键词 |

---

### 4.2 获取权限树

**接口**: `GET /permissions/tree`

**权限**: `permission.view`

**响应**: 返回树形结构的权限列表

---

### 4.3 获取权限详情

**接口**: `GET /permissions/{permission_id}`

**权限**: `permission.view`

---

## 5. 客户管理

### 5.1 创建客户

**接口**: `POST /customers`

**权限**: `customer.create`

**请求体**:
```json
{
  "name": "string",
  "customer_type": "individual|company|government",
  "level": "vip|normal|potential",
  "contact_person": "string",
  "contact_phone": "string",
  "contact_email": "string",
  "address": "string",
  "city": "string",
  "province": "string",
  "industry": "string",
  "tax_number": "string",
  "bank_name": "string",
  "bank_account": "string",
  "credit_limit": 0,
  "remarks": "string",
  "shipping_addresses": [
    {
      "recipient_name": "string",
      "recipient_phone": "string",
      "province": "string",
      "city": "string",
      "district": "string",
      "address": "string",
      "is_default": false,
      "remarks": "string"
    }
  ]
}
```

---

### 5.2 获取客户列表

**接口**: `GET /customers`

**权限**: `customer.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 客户状态 |
| level | string | 否 | 客户级别 |
| keyword | string | 否 | 搜索关键词 |

---

### 5.3 获取客户统计

**接口**: `GET /customers/stats`

**权限**: `customer.view`

**响应**:
```json
{
  "status": "success",
  "result": {
    "total": 100,
    "by_level": {},
    "by_status": {}
  }
}
```

---

### 5.4 搜索客户

**接口**: `GET /customers/search`

**权限**: `customer.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| limit | int | 否 | 返回数量，默认10 |

---

### 5.5 获取客户详情

**接口**: `GET /customers/{customer_id}`

**权限**: `customer.view`

---

### 5.6 更新客户

**接口**: `PUT /customers/{customer_id}`

**权限**: `customer.edit`

**请求体**: 同创建，字段可选

---

### 5.7 删除客户

**接口**: `DELETE /customers/{customer_id}`

**权限**: `customer.delete`

---

### 5.8 更新客户状态

**接口**: `PATCH /customers/{customer_id}/status`

**权限**: `customer.edit`

**查询参数**: `status` - 客户状态

---

### 5.9 添加收货地址

**接口**: `POST /customers/{customer_id}/shipping-addresses`

**权限**: `customer.edit`

**请求体**:
```json
{
  "recipient_name": "string",
  "recipient_phone": "string",
  "province": "string",
  "city": "string",
  "district": "string",
  "address": "string",
  "is_default": false,
  "remarks": "string"
}
```

---

### 5.10 更新收货地址

**接口**: `PUT /customers/{customer_id}/shipping-addresses/{address_id}`

**权限**: `customer.edit`

---

### 5.11 删除收货地址

**接口**: `DELETE /customers/{customer_id}/shipping-addresses/{address_id}`

**权限**: `customer.edit`

---

### 5.12 设置默认收货地址

**接口**: `PATCH /customers/{customer_id}/shipping-addresses/{address_id}/default`

**权限**: `customer.edit`

---

## 6. 商品管理

### 6.1 创建商品

**接口**: `POST /products`

**权限**: `product.create`

**请求体**:
```json
{
  "product_code": "string",
  "name": "string",
  "image_url": "string",
  "brand": "string",
  "category": "string",
  "tax_code": "string"
}
```

---

### 6.2 获取商品列表

**接口**: `GET /products`

**权限**: `product.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| keyword | string | 否 | 搜索关键词 |

**响应**: 返回商品列表，每个商品包含其规格列表

---

### 6.3 获取商品统计

**接口**: `GET /products/stats`

**权限**: `product.view`

---

### 6.4 搜索商品

**接口**: `GET /products/search`

**权限**: `product.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| limit | int | 否 | 返回数量，默认10 |

---

### 6.5 获取商品详情

**接口**: `GET /products/{product_id}`

**权限**: `product.view`

**响应**: 返回商品详情，包含规格列表

---

### 6.6 更新商品

**接口**: `PUT /products/{product_id}`

**权限**: `product.edit`

---

### 6.7 删除商品

**接口**: `DELETE /products/{product_id}`

**权限**: `product.delete`

**注意**: 删除商品会同时删除关联的规格

---

### 6.8 获取商品规格列表

**接口**: `GET /products/{product_id}/specs`

**权限**: `product.view`

---

### 6.9 创建商品规格

**接口**: `POST /products/{product_id}/specs`

**权限**: `product.create`

**请求体**:
```json
{
  "spec_code": "string",
  "packaging": "string",
  "sales_spec": "string",
  "price": 0,
  "cas_number": "string",
  "is_active": true
}
```

---

### 6.10 获取规格详情

**接口**: `GET /products/specs/{spec_id}`

**权限**: `product.view`

---

### 6.11 更新规格

**接口**: `PUT /products/specs/{spec_id}`

**权限**: `product.edit`

---

### 6.12 删除规格

**接口**: `DELETE /products/specs/{spec_id}`

**权限**: `product.delete`

---

### 6.13 切换规格激活状态

**接口**: `PATCH /products/specs/{spec_id}/toggle-active`

**权限**: `product.edit`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_active | bool | 是 | 是否激活 |

---

### 6.14 获取规格库存明细

**接口**: `GET /products/specs/{spec_id}/stock-detail`

**权限**: `product.view`

**响应**:
```json
{
  "status": "success",
  "result": {
    "items": [
      {
        "warehouse_code": "string",
        "warehouse_name": "string",
        "quantity": 0
      }
    ],
    "total_quantity": 0
  }
}
```

---

### 6.15 获取所有规格列表

**接口**: `GET /products/all-specs/`

**权限**: `product.view`

---

## 7. 仓库管理

### 7.1 创建仓库

**接口**: `POST /warehouses`

**权限**: `warehouse.create`

**请求体**:
```json
{
  "name": "string",
  "address": "string",
  "manager_id": "string",
  "manager_name": "string",
  "status": "active",
  "description": "string"
}
```

---

### 7.2 获取仓库列表

**接口**: `GET /warehouses`

**权限**: `warehouse.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 仓库状态 |
| keyword | string | 否 | 搜索关键词 |

---

### 7.3 搜索仓库

**接口**: `GET /warehouses/search`

**权限**: `warehouse.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| limit | int | 否 | 返回数量，默认10 |

---

### 7.4 获取仓库管理员候选

**接口**: `GET /warehouses/manager-candidates`

**权限**: `warehouse.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 否 | 搜索关键词 |

---

### 7.5 获取仓库详情

**接口**: `GET /warehouses/{warehouse_code}`

**权限**: `warehouse.view`

---

### 7.6 更新仓库

**接口**: `PUT /warehouses/{warehouse_code}`

**权限**: `warehouse.edit`

---

### 7.7 删除仓库

**接口**: `DELETE /warehouses/{warehouse_code}`

**权限**: `warehouse.delete`

---

### 7.8 更新仓库状态

**接口**: `PATCH /warehouses/{warehouse_code}/status`

**权限**: `warehouse.edit`

**查询参数**: `status` - 仓库状态

---

## 8. 库存管理

### 8.1 创建库存记录

**接口**: `POST /stocks`

**权限**: `stock.create`

**请求体**:
```json
{
  "spec_id": "string",
  "warehouse_id": "string",
  "quantity": 0,
  "min_stock": 0,
  "max_stock": 0,
  "status": "normal"
}
```

---

### 8.2 获取库存列表

**接口**: `GET /stocks`

**权限**: `stock.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| warehouse_id | string | 否 | 仓库ID |
| product_id | string | 否 | 商品ID |
| status | string | 否 | 库存状态 |
| keyword | string | 否 | 搜索关键词 |

---

### 8.3 获取库存统计

**接口**: `GET /stocks/stats`

**权限**: `stock.view`

---

### 8.4 搜索库存

**接口**: `GET /stocks/search`

**权限**: `stock.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| limit | int | 否 | 返回数量，默认10 |

---

### 8.5 获取库存详情

**接口**: `GET /stocks/{stock_id}`

**权限**: `stock.view`

---

### 8.6 更新库存

**接口**: `PUT /stocks/{stock_id}`

**权限**: `stock.edit`

---

### 8.7 删除库存记录

**接口**: `DELETE /stocks/{stock_id}`

**权限**: `stock.delete`

---

### 8.8 调整库存

**接口**: `POST /stocks/{stock_id}/adjust`

**权限**: `stock.edit`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| quantity_change | float | 是 | 库存变化量 |
| is_add | bool | 否 | 是否为增加操作，默认true |

---

## 9. 销售订单

### 9.1 创建销售订单

**接口**: `POST /sales-orders`

**权限**: `order.create`

**请求体**:
```json
{
  "customer_id": "string",
  "customer_name": "string",
  "receiver_name": "string",
  "contact_phone": "string",
  "delivery_address": "string",
  "order_date": "datetime",
  "expected_delivery_date": "datetime",
  "remarks": "string",
  "delivery_type": "inventory|direct",
  "warehouse_id": "string",
  "warehouse_name": "string",
  "pickup_type": "self_pickup|express",
  "express_type": "sf|yto|zto|jd|ems|other",
  "express_no": "string",
  "express_fee": 0,
  "discount_ratio": 100,
  "items": [
    {
      "product_id": "string",
      "product_name": "string",
      "product_code": "string",
      "quantity": 0,
      "unit_price": 0,
      "subtotal": 0
    }
  ]
}
```

**注意**: 创建订单会自动创建对应的应收单

---

### 9.2 获取销售订单列表

**接口**: `GET /sales-orders`

**权限**: `order.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 订单状态 |
| customer_id | string | 否 | 客户ID |
| warehouse_id | string | 否 | 仓库ID |
| product_id | string | 否 | 商品ID |
| order_no | string | 否 | 订单号 |

---

### 9.3 获取销售订单详情

**接口**: `GET /sales-orders/{order_no}`

**权限**: `order.view`

---

### 9.4 更新销售订单

**接口**: `PUT /sales-orders/{order_no}`

**权限**: `order.edit`

---

### 9.5 删除销售订单

**接口**: `DELETE /sales-orders/{order_no}`

**权限**: `order.delete`

---

### 9.6 更新订单状态

**接口**: `PATCH /sales-orders/{order_no}/status`

**权限**: `order.edit`

**查询参数**: `status` - 订单状态

---

### 9.7 更新付款状态

**接口**: `PATCH /sales-orders/{order_no}/payment-status`

**权限**: `order.edit`

**查询参数**: `payment_status` - 付款状态

---

### 9.8 确认销售订单

**接口**: `POST /sales-orders/{order_no}/confirm`

**权限**: `order.edit`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| supplier_id | string | 否 | 供应商ID（采购直发时必填） |
| supplier_name | string | 否 | 供应商名称（采购直发时必填） |

---

## 10. 采购单管理

### 10.1 创建采购单

**接口**: `POST /procurement-orders`

**权限**: `procurement.create`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| sales_order_id | string | 否 | 关联销售订单ID |

**请求体**:
```json
{
  "supplier_id": "string",
  "supplier_name": "string",
  "contact_phone": "string",
  "delivery_address": "string",
  "expected_delivery_date": "datetime",
  "remarks": "string",
  "items": [
    {
      "product_id": "string",
      "product_name": "string",
      "product_code": "string",
      "quantity": 0,
      "unit_price": 0,
      "subtotal": 0
    }
  ]
}
```

---

### 10.2 获取采购单列表

**接口**: `GET /procurement-orders`

**权限**: `procurement.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 采购单状态 |
| supplier_id | string | 否 | 供应商ID |
| keyword | string | 否 | 搜索关键词 |

---

### 10.3 获取采购单详情

**接口**: `GET /procurement-orders/{order_id}`

**权限**: `procurement.view`

---

### 10.4 更新采购单

**接口**: `PUT /procurement-orders/{order_id}`

**权限**: `procurement.edit`

---

### 10.5 删除采购单

**接口**: `DELETE /procurement-orders/{order_id}`

**权限**: `procurement.delete`

---

### 10.6 更新采购单状态

**接口**: `PATCH /procurement-orders/{order_id}/status`

**权限**: `procurement.edit`

**查询参数**: `status` - 采购单状态

---

## 11. 应收款管理

### 11.1 创建应收单

**接口**: `POST /accounts-receivable`

**权限**: `receivable.create`

**请求体**:
```json
{
  "customer_id": "string",
  "customer_name": "string",
  "sales_order_id": "string",
  "sales_order_no": "string",
  "total_amount": 0,
  "remarks": "string"
}
```

---

### 11.2 获取应收单列表

**接口**: `GET /accounts-receivable`

**权限**: `receivable.view`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 收款状态 |
| customer_id | string | 否 | 客户ID |
| keyword | string | 否 | 搜索关键词 |

---

### 11.3 获取应收单详情

**接口**: `GET /accounts-receivable/{receivable_id}`

**权限**: `receivable.view`

---

### 11.4 更新应收单

**接口**: `PUT /accounts-receivable/{receivable_id}`

**权限**: `receivable.edit`

---

### 11.5 删除应收单

**接口**: `DELETE /accounts-receivable/{receivable_id}`

**权限**: `receivable.delete`

---

### 11.6 记录收款

**接口**: `POST /accounts-receivable/{receivable_id}/record-payment`

**权限**: `receivable.edit`

**请求体**:
```json
{
  "amount": 0,
  "payment_method": "cash|bank_transfer|wechat|alipay|other",
  "remarks": "string"
}
```

---

### 11.7 更新应收单状态

**接口**: `PATCH /accounts-receivable/{receivable_id}/status`

**权限**: `receivable.edit`

**查询参数**: `status` - 收款状态

---

## 12. LLM 设置

### 12.1 获取 LLM 模型列表

**接口**: `GET /llm/models`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| keyword | string | 否 | 搜索关键词 |

---

### 12.2 获取 LLM 模型详情

**接口**: `GET /llm/models/{model_id}`

---

### 12.3 创建 LLM 模型

**接口**: `POST /llm/models`

**请求体**:
```json
{
  "name": "string",
  "provider": "string",
  "model_type": "string",
  "api_key": "string",
  "base_url": "string",
  "model_id": "string"
}
```

---

### 12.4 更新 LLM 模型

**接口**: `PUT /llm/models/{model_id}`

---

### 12.5 删除 LLM 模型

**接口**: `DELETE /llm/models/{model_id}`

---

### 12.6 测试 LLM 模型连接

**接口**: `POST /llm/models/{model_id}/test`

---

### 12.7 获取 LLM 配置

**接口**: `GET /llm/config`

---

### 12.8 更新 LLM 配置

**接口**: `PUT /llm/config`

**请求体**:
```json
{
  "default_model_id": "string",
  "temperature": 0,
  "max_tokens": 0
}
```

---

## 13. 知识库设置

### 13.1 获取知识库列表

**接口**: `GET /knowledge-base/collections`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| kb_type | string | 否 | 知识库类型 |
| keyword | string | 否 | 搜索关键词 |

---

### 13.2 获取知识库详情

**接口**: `GET /knowledge-base/collections/{kb_id}`

---

### 13.3 创建知识库

**接口**: `POST /knowledge-base/collections`

**请求体**:
```json
{
  "name": "string",
  "kb_type": "string",
  "description": "string"
}
```

---

### 13.4 更新知识库

**接口**: `PUT /knowledge-base/collections/{kb_id}`

---

### 13.5 删除知识库

**接口**: `DELETE /knowledge-base/collections/{kb_id}`

---

## 14. MCP 设置

### 14.1 获取 MCP 服务器列表

**接口**: `GET /mcp/servers`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 服务器状态 |
| keyword | string | 否 | 搜索关键词 |

---

### 14.2 获取 MCP 服务器详情

**接口**: `GET /mcp/servers/{server_id}`

---

### 14.3 创建 MCP 服务器

**接口**: `POST /mcp/servers`

**请求体**:
```json
{
  "name": "string",
  "server_type": "string",
  "command": "string",
  "args": ["string"],
  "env": {},
  "status": "active"
}
```

---

### 14.4 更新 MCP 服务器

**接口**: `PUT /mcp/servers/{server_id}`

---

### 14.5 删除 MCP 服务器

**接口**: `DELETE /mcp/servers/{server_id}`

---

### 14.6 测试 MCP 服务器连接

**接口**: `POST /mcp/servers/{server_id}/test`

---

### 14.7 获取 MCP 服务器工具列表

**接口**: `GET /mcp/servers/{server_id}/tools`

---

## 15. Skills 设置

### 15.1 获取技能列表

**接口**: `GET /skills`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| category | string | 否 | 技能分类 |
| keyword | string | 否 | 搜索关键词 |

---

### 15.2 获取技能详情

**接口**: `GET /skills/{skill_id}`

---

### 15.3 创建技能

**接口**: `POST /skills`

**请求体**:
```json
{
  "name": "string",
  "category": "string",
  "description": "string",
  "instruction": "string",
  "is_active": true
}
```

---

### 15.4 更新技能

**接口**: `PUT /skills/{skill_id}`

---

### 15.5 删除技能

**接口**: `DELETE /skills/{skill_id}`

---

### 15.6 启用技能

**接口**: `PATCH /skills/{skill_id}/enable`

---

### 15.7 禁用技能

**接口**: `PATCH /skills/{skill_id}/disable`

---

## 16. Agent 设置

### 16.1 获取 Agent 列表

**接口**: `GET /agents`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| keyword | string | 否 | 搜索关键词 |

---

### 16.2 获取 Agent 详情

**接口**: `GET /agents/{agent_id}`

---

### 16.3 创建 Agent

**接口**: `POST /agents`

**请求体**:
```json
{
  "name": "string",
  "description": "string",
  "model_id": "string",
  "skills": ["string"],
  "system_prompt": "string",
  "is_active": true
}
```

---

### 16.4 更新 Agent

**接口**: `PUT /agents/{agent_id}`

---

### 16.5 删除 Agent

**接口**: `DELETE /agents/{agent_id}`

---

## 17. AI 工具

### 17.1 获取所有 AI 工具

**接口**: `GET /ai/tools`

**响应**:
```json
{
  "items": [
    {
      "name": "string",
      "cn_name": "string",
      "description": "string",
      "permission_code": "string"
    }
  ],
  "total": 0
}
```

---

## 18. 文件上传

### 18.1 上传文件

**接口**: `POST /upload/file`

**权限**: 需登录

**请求体**: `multipart/form-data`
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| file | File | 是 | 上传的文件 |

**支持的类型**:
- 图片: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`
- 文档: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.txt`, `.csv`

**响应**:
```json
{
  "file_id": "string",
  "file_name": "string",
  "file_url": "string",
  "file_path": "string",
  "file_type": "image|document",
  "file_size": 0
}
```

---

### 18.2 删除文件

**接口**: `DELETE /upload/file/{file_id}`

**权限**: 需登录

---

## 19. WebSocket

### 19.1 WebSocket 聊天

**接口**: `WS /ws/chat/{agent_id}`

**认证**: 通过 query 参数传递 `user_id` 和 `token`

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |
| token | string | 是 | 认证Token |

**发送消息格式**:
```json
{
  "type": "text|image|voice|ping|clear_history",
  "content": "string",
  "files": []
}
```

**接收消息类型**:
| 类型 | 描述 |
|------|------|
| text | AI 文本回复 |
| tool_call_start | 工具开始调用 |
| tool_call_end | 工具调用结束 |
| form_result | 表单结果 |
| error | 错误信息 |
| system | 系统消息 |
| pong | ping 响应 |

---

### 19.2 WebSocket 状态

**接口**: `GET /ws/status`

**响应**:
```json
{
  "status": "running",
  "active_connections": 0
}
```

---

## 20. 健康检查

### 20.1 健康检查

**接口**: `GET /health/`

**响应**:
```json
{
  "status": "healthy",
  "service": "ai_mdr_platform_api",
  "version": "1.0.0",
  "database": {
    "mongodb": "connected",
    "redis": "connected"
  }
}
```

---

### 20.2 Ping

**接口**: `GET /health/ping`

**响应**:
```json
{
  "message": "pong"
}
```

---

## 附录

### 枚举值说明

**用户状态 (UserStatus)**:
- `active` - 正常
- `inactive` - 未激活
- `locked` - 锁定

**客户类型 (CustomerType)**:
- `individual` - 个人
- `company` - 企业
- `government` - 政府

**客户级别 (CustomerLevel)**:
- `vip` - VIP
- `normal` - 普通
- `potential` - 潜在

**客户状态 (CustomerStatus)**:
- `normal` - 正常
- `inactive` - 未激活
- `blacklisted` - 黑名单

**仓库状态 (WarehouseStatus)**:
- `active` - 正常
- `inactive` - 停用
- `maintenance` - 维护中

**库存状态 (StockStatus)**:
- `normal` - 正常
- `low_stock` - 低库存
- `out_of_stock` - 缺货
- `overstock` - 超库存

**订单状态 (OrderStatus)**:
- `draft` - 草稿
- `pending` - 待处理
- `confirmed` - 已确认
- `processing` - 处理中
- `shipped` - 已发货
- `completed` - 已完成
- `cancelled` - 已取消

**付款状态 (PaymentStatus)**:
- `unpaid` - 未付款
- `partial` - 部分付款
- `paid` - 已付清

**采购单状态 (ProcurementOrderStatus)**:
- `draft` - 草稿
- `pending` - 待处理
- `confirmed` - 已确认
- `purchased` - 已采购
- `received` - 已收货
- `cancelled` - 已取消

**应收单状态 (ReceivableStatus)**:
- `unpaid` - 未收款
- `partial` - 部分收款
- `paid` - 已收清
- `overdue` - 逾期
- `cancelled` - 已取消

**发货方式 (DeliveryType)**:
- `inventory` - 库存发货
- `direct` - 采购直发

**提货方式 (PickupType)**:
- `self_pickup` - 自取
- `express` - 快递

**快递类型 (ExpressType)**:
- `sf` - 顺丰
- `yto` - 圆通
- `zto` - 中通
- `jd` - 京东
- `ems` - EMS
- `other` - 其他

---

## 权限代码参考

| 模块 | 权限代码 | 描述 |
|------|----------|------|
| 用户 | user.view | 查看用户 |
| 用户 | user.create | 创建用户 |
| 用户 | user.edit | 编辑用户 |
| 用户 | user.delete | 删除用户 |
| 用户 | user.reset-password | 重置密码 |
| 角色 | role.view | 查看角色 |
| 角色 | role.create | 创建角色 |
| 角色 | role.edit | 编辑角色 |
| 角色 | role.delete | 删除角色 |
| 权限 | permission.view | 查看权限 |
| 客户 | customer.view | 查看客户 |
| 客户 | customer.create | 创建客户 |
| 客户 | customer.edit | 编辑客户 |
| 客户 | customer.delete | 删除客户 |
| 商品 | product.view | 查看商品 |
| 商品 | product.create | 创建商品 |
| 商品 | product.edit | 编辑商品 |
| 商品 | product.delete | 删除商品 |
| 仓库 | warehouse.view | 查看仓库 |
| 仓库 | warehouse.create | 创建仓库 |
| 仓库 | warehouse.edit | 编辑仓库 |
| 仓库 | warehouse.delete | 删除仓库 |
| 库存 | stock.view | 查看库存 |
| 库存 | stock.create | 创建库存 |
| 库存 | stock.edit | 编辑库存 |
| 库存 | stock.delete | 删除库存 |
| 订单 | order.view | 查看订单 |
| 订单 | order.create | 创建订单 |
| 订单 | order.edit | 编辑订单 |
| 订单 | order.delete | 删除订单 |
| 采购 | procurement.view | 查看采购单 |
| 采购 | procurement.create | 创建采购单 |
| 采购 | procurement.edit | 编辑采购单 |
| 采购 | procurement.delete | 删除采购单 |
| 应收 | receivable.view | 查看应收单 |
| 应收 | receivable.create | 创建应收单 |
| 应收 | receivable.edit | 编辑应收单 |
| 应收 | receivable.delete | 删除应收单 |
