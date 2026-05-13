# 认证与权限管理 API

> 合并后的认证、用户、角色、权限管理接口

## 基础信息

- **认证基础路径**: `/api/v1/auth`
- **认证方式**: Bearer Token (JWT) 或 LOCAL_DEBUG 模式（跳过认证）
- **权限说明**: 需要携带有效 Token 访问（LOCAL_DEBUG 模式下跳过）

---

## 目录

### 认证

- [用户登录](#11-用户登录)
- [用户注册](#12-用户注册)
- [获取当前用户](#13-获取当前用户)
- [修改密码](#14-修改密码)

### 用户管理

- [获取用户列表](#21-获取用户列表)
- [获取用户详情](#22-获取用户详情)
- [创建用户](#23-创建用户)
- [更新用户](#24-更新用户)
- [删除用户](#25-删除用户)
- [重置用户密码](#26-重置用户密码)
- [更新用户状态](#27-更新用户状态)

### 角色管理

- [获取角色列表](#31-获取角色列表)
- [获取角色详情](#32-获取角色详情)
- [创建角色](#33-创建角色)
- [更新角色](#34-更新角色)
- [删除角色](#35-删除角色)
- [更新角色状态](#36-更新角色状态)

### 权限管理

- [获取权限列表](#41-获取权限列表)
- [获取权限树](#42-获取权限树)
- [获取权限详情](#43-获取权限详情)

---

## 1.1 用户登录

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/auth/login` |
| **Method** | POST |
| **权限** | 无需认证 |

### 请求体

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "69e0ae89f6c9e5eee0ba2320",
      "username": "admin",
      "full_name": "管理员",
      "email": "admin@example.com",
      "status": "active",
      "roles": [...],
      "permissions": [...]
    }
  }
}
```

**错误响应（认证失败）**:
```json
{
  "status": "error",
  "message": "用户名或密码错误",
  "result": null
}
```

---

## 1.2 用户注册

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/auth/register` |
| **Method** | POST |
| **权限** | 无需认证 |

### 请求体

```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "phone": "13800138000",
  "full_name": "新用户"
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名（3-50字符，只能包含字母、数字、下划线和连字符） |
| password | string | 是 | 密码（至少6位） |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 手机号 |
| full_name | string | 否 | 全名 |
| role_ids | array | 否 | 角色ID列表 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "69e0ae89f6c9e5eee0ba2321"
  }
}
```

**错误响应（用户名已存在）**:
```json
{
  "status": "error",
  "message": "用户名已存在",
  "result": null
}
```

---

## 1.3 获取当前用户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/me` |
| **Method** | GET |
| **权限** | 需要认证 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "69e0ae89f6c9e5eee0ba2320",
    "username": "admin",
    "full_name": "管理员",
    "email": "admin@example.com",
    "status": "active",
    "roles": [
      {
        "id": "...",
        "code": "super_admin",
        "name": "超级管理员",
        "permissions": [...]
      }
    ],
    "permissions": ["user.view", "user.create", ...]
  }
}
```

---

## 1.4 修改密码

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/auth/me/password` |
| **Method** | PUT |
| **权限** | 需要认证 |

### 请求体

```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码（至少6位） |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "密码修改成功",
  "result": null
}
```

**错误响应（旧密码错误）**:
```json
{
  "status": "error",
  "message": "旧密码错误",
  "result": null
}
```

---

## 2.1 获取用户列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/users/` |
| **Method** | GET |
| **权限** | `user.view` |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| status | string | 否 | - | 用户状态：`active` / `inactive` / `locked` |
| keyword | string | 否 | - | 搜索关键词（用户名、全名、邮箱） |
| role | string | 否 | - | 角色ID |

### 响应

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
        "id": "69e0ae89f6c9e5eee0ba2320",
        "username": "admin",
        "full_name": "管理员",
        "email": "admin@example.com",
        "status": "active",
        "roles": [...],
        "permissions": [...],
        "created_at": "2026-05-11T10:30:00Z"
      }
    ]
  }
}
```

---

## 2.2 获取用户详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/users/{user_id}/` |
| **Method** | GET |
| **权限** | `user.view` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "69e0ae89f6c9e5eee0ba2320",
    "username": "admin",
    "full_name": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "status": "active",
    "roles": [...],
    "permissions": [...],
    "created_at": "2026-05-11T10:30:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  }
}
```

**错误响应**:
```json
{
  "status": "error",
  "message": "用户不存在",
  "result": null
}
```

---

## 2.3 创建用户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/auth/users/` |
| **Method** | POST |
| **权限** | `user.create` |

### 请求体

```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "phone": "13800138000",
  "full_name": "新用户",
  "role_ids": ["role_id_1", "role_id_2"]
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | 是 | 用户名（3-50字符） |
| password | string | 是 | 密码（至少6位） |
| email | string | 否 | 邮箱 |
| phone | string | 否 | 手机号 |
| full_name | string | 否 | 全名 |
| role_ids | array | 否 | 角色ID列表 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "69e0ae89f6c9e5eee0ba2321"
  }
}
```

---

## 2.4 更新用户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/auth/users/{user_id}/` |
| **Method** | PUT |
| **权限** | `user.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

### 请求体

```json
{
  "email": "newemail@example.com",
  "phone": "13900139000",
  "full_name": "更新后的名字",
  "role_ids": ["role_id_1"],
  "new_password": "newpassword123"
}
```

**说明**: 支持部分更新，只发送需要更新的字段。如果需要修改密码，使用 `new_password` 字段。

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "用户更新成功",
  "result": null
}
```

---

## 2.5 删除用户

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/auth/users/{user_id}/` |
| **Method** | DELETE |
| **权限** | `user.delete` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "用户删除成功",
  "result": null
}
```

---

## 2.6 重置用户密码

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/auth/users/{user_id}/password` |
| **Method** | PATCH |
| **权限** | `user.reset-password` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

### 请求体

```json
{
  "new_password": "resetpassword123"
}
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "密码重置成功",
  "result": null
}
```

---

## 2.7 更新用户状态

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/auth/users/{user_id}/status` |
| **Method** | PATCH |
| **权限** | `user.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| status | string | 是 | 用户状态：`active` / `inactive` / `locked` |

### 请求示例

```
PATCH /api/v1/auth/users/69e0ae89f6c9e5eee0ba2320/status?status=inactive
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "用户状态更新成功",
  "result": null
}
```

---

## 3.1 获取角色列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/roles/` |
| **Method** | GET |
| **权限** | `role.view` |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| status | string | 否 | - | 角色状态：`active` / `inactive` |
| keyword | string | 否 | - | 搜索关键词（角色编码、名称） |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 5,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "69e0ae89f6c9e5eee0ba2320",
        "code": "super_admin",
        "name": "超级管理员",
        "description": "系统超级管理员，拥有所有权限",
        "is_fixed": true,
        "status": "active",
        "permissions": [...],
        "created_at": "2026-05-11T10:30:00Z"
      }
    ]
  }
}
```

---

## 3.2 获取角色详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/roles/{role_id}/` |
| **Method** | GET |
| **权限** | `role.view` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| role_id | string | 是 | 角色ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "69e0ae89f6c9e5eee0ba2320",
    "code": "admin",
    "name": "管理员",
    "description": "系统管理员",
    "is_fixed": false,
    "status": "active",
    "permission_ids": ["perm_id_1", "perm_id_2"],
    "permissions": [
      {
        "id": "perm_id_1",
        "code": "user.view",
        "name": "用户查看"
      }
    ],
    "created_at": "2026-05-11T10:30:00Z"
  }
}
```

---

## 3.3 创建角色

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/auth/roles/` |
| **Method** | POST |
| **权限** | `role.create` |

### 请求体

```json
{
  "code": "custom_role",
  "name": "自定义角色",
  "description": "这是一个自定义角色",
  "permission_ids": ["perm_id_1", "perm_id_2"]
}
```

**请求字段说明**:
| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| code | string | 是 | 角色编码（唯一） |
| name | string | 是 | 角色名称 |
| description | string | 否 | 描述 |
| permission_ids | array | 否 | 权限ID列表 |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "69e0ae89f6c9e5eee0ba2321"
  }
}
```

**错误响应（角色编码已存在）**:
```json
{
  "status": "error",
  "message": "角色编码已存在",
  "result": null
}
```

---

## 3.4 更新角色

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PUT /api/v1/auth/roles/{role_id}/` |
| **Method** | PUT |
| **权限** | `role.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| role_id | string | 是 | 角色ID |

### 请求体

```json
{
  "name": "更新后的角色名",
  "description": "更新后的描述",
  "permission_ids": ["perm_id_1", "perm_id_2", "perm_id_3"]
}
```

**说明**: 固化角色（is_fixed=true）不允许修改。

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "角色更新成功",
  "result": null
}
```

**错误响应（固化角色）**:
```json
{
  "status": "error",
  "message": "固化角色不允许修改",
  "result": null
}
```

---

## 3.5 删除角色

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `DELETE /api/v1/auth/roles/{role_id}/` |
| **Method** | DELETE |
| **权限** | `role.delete` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| role_id | string | 是 | 角色ID |

**说明**: 固化角色（is_fixed=true）不允许删除。

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "角色删除成功",
  "result": null
}
```

**错误响应（固化角色）**:
```json
{
  "status": "error",
  "message": "固化角色不允许删除",
  "result": null
}
```

---

## 3.6 更新角色状态

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `PATCH /api/v1/auth/roles/{role_id}/status` |
| **Method** | PATCH |
| **权限** | `role.edit` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| role_id | string | 是 | 角色ID |

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| status | string | 是 | 角色状态：`active` / `inactive` |

### 请求示例

```
PATCH /api/v1/auth/roles/69e0ae89f6c9e5eee0ba2320/status?status=inactive
```

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "角色状态更新成功",
  "result": null
}
```

---

## 4.1 获取权限列表

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/permissions/` |
| **Method** | GET |
| **权限** | `permission.view` |

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量（最大100） |
| keyword | string | 否 | - | 搜索关键词（权限编码、名称） |

### 响应

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
        "id": "69e0ae89f6c9e5eee0ba2320",
        "code": "user.view",
        "name": "用户查看",
        "type": "menu",
        "path": "/users",
        "parent_id": null,
        "sort_order": 95,
        "created_at": "2026-05-11T10:30:00Z"
      }
    ]
  }
}
```

---

## 4.2 获取权限树

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/permissions/tree` |
| **Method** | GET |
| **权限** | `permission.view` |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": [
    {
      "id": "69e0ae89f6c9e5eee0ba2320",
      "code": "user.menu",
      "name": "用户管理菜单",
      "type": "menu",
      "path": "/users",
      "parent_id": null,
      "sort_order": 90,
      "children": [
        {
          "id": "69e0ae89f6c9e5eee0ba2321",
          "code": "user.view",
          "name": "用户查看",
          "type": "menu",
          "path": "/users",
          "parent_id": "69e0ae89f6c9e5eee0ba2320",
          "sort_order": 95,
          "children": []
        }
      ]
    }
  ]
}
```

---

## 4.3 获取权限详情

### 接口信息

| 属性 | 值 |
|------|-----|
| **URL** | `GET /api/v1/auth/permissions/{permission_id}/` |
| **Method** | GET |
| **权限** | `permission.view` |

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| permission_id | string | 是 | 权限ID |

### 响应

**成功响应**:
```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "69e0ae89f6c9e5eee0ba2320",
    "code": "user.view",
    "name": "用户查看",
    "type": "menu",
    "path": "/users",
    "parent_id": "69e0ae89f6c9e5eee0ba2321",
    "description": "查看用户列表和详情",
    "sort_order": 95,
    "created_at": "2026-05-11T10:30:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  }
}
```

---

## 数据结构

### 用户 (User)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 用户ID（系统自动生成） |
| username | string | 用户名 |
| password | string | 密码（加密存储） |
| email | string | 邮箱 |
| phone | string | 手机号 |
| full_name | string | 全名 |
| avatar | string | 头像URL |
| status | string | 用户状态：`active` / `inactive` / `locked` |
| role_ids | array | 角色ID列表 |
| roles | array | 用户角色列表（含权限详情） |
| permissions | array | 用户权限编码列表 |
| last_login | datetime | 最后登录时间 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 角色 (Role)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 角色ID（系统自动生成） |
| code | string | 角色编码（唯一） |
| name | string | 角色名称 |
| description | string | 描述 |
| is_fixed | boolean | 是否固化角色（固化角色不允许删除和修改） |
| status | string | 角色状态：`active` / `inactive` |
| permission_ids | array | 权限ID列表 |
| permissions | array | 角色权限列表 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 权限 (Permission)

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 权限ID（系统自动生成） |
| code | string | 权限编码（如 `user.view`） |
| name | string | 权限名称 |
| type | string | 权限类型：`menu` / `button` / `button,tools` / `tools` / `api` |
| path | string | 路径/路由 |
| parent_id | string | 父权限ID（用于构建权限树） |
| description | string | 描述 |
| sort_order | int | 排序 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 权限代码

| 权限 | 描述 |
|------|------|
| user.view | 查看用户 |
| user.create | 创建用户 |
| user.edit | 编辑用户 |
| user.delete | 删除用户 |
| user.reset-password | 重置用户密码 |
| role.view | 查看角色 |
| role.create | 创建角色 |
| role.edit | 编辑角色 |
| role.delete | 删除角色 |
| permission.view | 查看权限 |

---

## 变更记录

| 日期 | 变更内容 |
|------|---------|
| 2026-05-12 | 重构auth模块，将user、role、permission路由合并到统一的auth.py |
| 2026-05-12 | 路由前缀统一为 `/api/v1/auth` |
| 2026-05-12 | 服务层方法参数从Pydantic model改为Dict[str, Any] |
| 2026-05-12 | models/auth.py精简为只保留数据库集合相关的模型 |
