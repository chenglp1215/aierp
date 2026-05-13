# 供应商管理 API

本文档描述供应商管理模块的所有 REST API 接口。

**模块路径**: `/api/v1/suppliers`

**权限要求**:
- `supplier.view`: 查看供应商
- `supplier.create`: 创建供应商
- `supplier.edit`: 编辑供应商
- `supplier.delete`: 删除供应商

---

## 数据模型

### 供应商供货品牌模型

```json
{
  "brand_id": "507f1f77bcf86cd799439011",
  "discount": 0.95,
  "is_priority": true
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| brand_id | string | 品牌ID（关联品牌表） |
| discount | float | 折扣率（0-1，默认1.0） |
| is_priority | boolean | 是否优先选择（默认false） |

### 银行账户模型

```json
{
  "bank_name": "中国工商银行",
  "account_name": "某某供应商有限公司",
  "account_no": "6222021234567890123"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| bank_name | string | 开户行 |
| account_name | string | 账户名 |
| account_no | string | 账号 |

### 供应商创建模型

```json
{
  "name": "某某供应商有限公司",
  "contact_person": "张三",
  "contact_phone": "13800138000",
  "contact_email": "zhangsan@example.com",
  "address": "北京市朝阳区某某街道123号",
  "bank_account": {
    "bank_name": "中国工商银行",
    "account_name": "某某供应商有限公司",
    "account_no": "6222021234567890123"
  },
  "supplied_brands": [
    {
      "brand_id": "507f1f77bcf86cd799439011",
      "discount": 0.95,
      "is_priority": true
    }
  ],
  "remark": "优质供应商",
  "is_active": true
}
```

#### 字段说明

##### 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 供应商名称 |

##### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| contact_person | string | 联系人 |
| contact_phone | string | 联系电话 |
| contact_email | string | 联系邮箱 |
| address | string | 地址 |
| bank_account | object | 银行账户信息 |
| supplied_brands | array | 供货品牌列表 |
| remark | string | 备注 |
| is_active | boolean | 是否激活（默认true） |

### 供应商完整模型

```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "某某供应商有限公司",
  "contact_person": "张三",
  "contact_phone": "13800138000",
  "contact_email": "zhangsan@example.com",
  "address": "北京市朝阳区某某街道123号",
  "bank_account": {
    "bank_name": "中国工商银行",
    "account_name": "某某供应商有限公司",
    "account_no": "6222021234567890123"
  },
  "supplied_brands": [
    {
      "brand_id": "507f1f77bcf86cd799439011",
      "discount": 0.95,
      "is_priority": true
    }
  ],
  "remark": "优质供应商",
  "is_active": true,
  "created_at": "2026-05-03T10:00:00",
  "updated_at": "2026-05-03T10:00:00"
}
```

---

## API 接口

### 1. 创建供应商

**POST** `/api/v1/suppliers/`

**权限**: `supplier.create`

#### 请求参数

```json
{
  "name": "某某供应商有限公司",
  "contact_person": "张三",
  "contact_phone": "13800138000",
  "contact_email": "zhangsan@example.com",
  "address": "北京市朝阳区某某街道123号",
  "bank_account": {
    "bank_name": "中国工商银行",
    "account_name": "某某供应商有限公司",
    "account_no": "6222021234567890123"
  },
  "supplied_brands": [
    {
      "brand_id": "507f1f77bcf86cd799439011",
      "discount": 0.95,
      "is_priority": true
    }
  ],
  "remark": "优质供应商",
  "is_active": true
}
```

#### 响应示例

```json
{
  "status": "success",
  "message": "供应商创建成功",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "某某供应商有限公司",
    "contact_person": "张三",
    "contact_phone": "13800138000",
    "contact_email": "zhangsan@example.com",
    "address": "北京市朝阳区某某街道123号",
    "bank_account": {
      "bank_name": "中国工商银行",
      "account_name": "某某供应商有限公司",
      "account_no": "6222021234567890123"
    },
    "supplied_brands": [
      {
        "brand_id": "507f1f77bcf86cd799439011",
        "discount": 0.95,
        "is_priority": true
      }
    ],
    "remark": "优质供应商",
    "is_active": true,
    "created_at": "2026-05-03T10:00:00",
    "updated_at": "2026-05-03T10:00:00"
  }
}
```

---

### 2. 获取供应商列表

**GET** `/api/v1/suppliers/`

**权限**: `supplier.view`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码（默认：1） |
| page_size | int | 否 | 每页数量（默认：20，最大：100） |
| keyword | string | 否 | 搜索关键词（供应商名称） |
| is_active | boolean | 否 | 是否激活 |
| brand_ids | string[] | 否 | 品牌ID列表（逗号分隔或多值形式） |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取供应商列表成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "507f1f77bcf86cd799439011",
        "name": "某某供应商有限公司",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "contact_email": "zhangsan@example.com",
        "address": "北京市朝阳区某某街道123号",
        "bank_account": {
          "bank_name": "中国工商银行",
          "account_name": "某某供应商有限公司",
          "account_no": "6222021234567890123"
        },
        "supplied_brands": [
          {
            "brand_id": "507f1f77bcf86cd799439011",
            "discount": 0.95,
            "is_priority": true
          }
        ],
        "remark": "优质供应商",
        "is_active": true,
        "created_at": "2026-05-03T10:00:00",
        "updated_at": "2026-05-03T10:00:00"
      }
    ]
  }
}
```

---

### 3. 获取供应商详情

**GET** `/api/v1/suppliers/{supplier_id}`

**权限**: `supplier.view`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | string | 是 | 供应商ID |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取供应商详情成功",
  "result": {
    "id": "507f1f77bcf86cd799439011",
    "name": "某某供应商有限公司",
    "contact_person": "张三",
    "contact_phone": "13800138000",
    "contact_email": "zhangsan@example.com",
    "address": "北京市朝阳区某某街道123号",
    "bank_account": {
      "bank_name": "中国工商银行",
      "account_name": "某某供应商有限公司",
      "account_no": "6222021234567890123"
    },
    "supplied_brands": [
      {
        "brand_id": "507f1f77bcf86cd799439011",
        "discount": 0.95,
        "is_priority": true
      }
    ],
    "remark": "优质供应商",
    "is_active": true,
    "created_at": "2026-05-03T10:00:00",
    "updated_at": "2026-05-03T10:00:00"
  }
}
```

---

### 4. 更新供应商

**PUT** `/api/v1/suppliers/{supplier_id}`

**权限**: `supplier.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | string | 是 | 供应商ID |

#### 请求参数

```json
{
  "name": "某某供应商有限公司（更新后）",
  "contact_person": "李四",
  "contact_phone": "13800138001",
  "remark": "更新后的备注"
}
```

#### 响应示例

```json
{
  "status": "success",
  "message": "供应商更新成功"
}
```

---

### 5. 删除供应商

**DELETE** `/api/v1/suppliers/{supplier_id}`

**权限**: `supplier.delete`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | string | 是 | 供应商ID |

#### 响应示例

```json
{
  "status": "success",
  "message": "供应商删除成功"
}
```

---

### 6. 切换供应商激活状态

**PATCH** `/api/v1/suppliers/{supplier_id}/toggle-active`

**权限**: `supplier.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | string | 是 | 供应商ID |

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 是 | 是否激活 |

#### 响应示例

```json
{
  "status": "success",
  "message": "供应商已激活"
}
```

---

### 7. 根据品牌ID获取供应商列表

**GET** `/api/v1/suppliers/by-brand/{brand_id}`

**权限**: `supplier.view`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| brand_id | string | 是 | 品牌ID |

#### 响应示例

```json
{
  "status": "success",
  "message": "获取供应商列表成功",
  "result": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "某某供应商有限公司",
      "contact_person": "张三",
      "contact_phone": "13800138000",
      "supplied_brands": [
        {
          "brand_id": "507f1f77bcf86cd799439011",
          "discount": 0.95,
          "is_priority": true
        }
      ],
      "is_active": true
    }
  ]
}
```

---

## 错误响应

### 供应商不存在

```json
{
  "status": "error",
  "message": "供应商不存在"
}
```

### 供应商名称已存在

```json
{
  "status": "error",
  "message": "供应商名称已存在"
}
```

### 供应商更新失败

```json
{
  "status": "error",
  "message": "供应商不存在或更新失败"
}
```

### 供应商删除失败

```json
{
  "status": "error",
  "message": "供应商不存在或删除失败"
}
```

### 供应商下有采购单无法删除

```json
{
  "status": "error",
  "message": "该供应商下存在 X 个采购单，无法删除"
}
```
