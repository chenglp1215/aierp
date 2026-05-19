## Context

供应商模块当前使用 MongoDB 存储，数据结构包含嵌入式数组（`supplied_brands`、`bank_account`）。系统其他核心模块（客户、商品、采购单、销售订单、库存等）已完成 MySQL 迁移，使用 Tortoise ORM。

当前 MongoDB 供应商数据结构：
```json
{
  "_id": ObjectId("..."),
  "name": "供应商名称",
  "contact_person": "联系人",
  "contact_phone": "联系电话",
  "contact_email": "邮箱",
  "address": "地址",
  "bank_account": {
    "bank_name": "开户行",
    "account_name": "账户名",
    "account_no": "账号"
  },
  "supplied_brands": [
    {
      "brand_id": "507f1f77bcf86cd799439011",
      "discount": 0.95,
      "is_priority": true
    }
  ],
  "remark": "备注",
  "is_active": true,
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

采购单表 `purchase_orders` 中 `supplier_id` 当前为普通整数字段，无外键约束。

## Goals / Non-Goals

**Goals:**
- 将供应商数据从 MongoDB 迁移到 MySQL
- 使用外键约束替代嵌入式数组，保证数据完整性
- 保持 API 路径和功能不变
- 提供数据迁移脚本，支持平滑迁移
- 更新采购单表，添加供应商外键约束

**Non-Goals:**
- 不改变供应商业务逻辑
- 不添加新功能（如供应商评级、多联系人等）
- 不修改前端 UI 设计

## Decisions

### 1. 数据模型设计

**决策**: 采用三表设计

| 表名 | 用途 |
|------|------|
| `suppliers` | 供应商主表 |
| `supplier_brands` | 供应商-品牌关联表（多对多） |
| `supplier_bank_accounts` | 银行账户表（一对多） |

**理由**:
- 符合 MySQL 关系型设计原则
- 便于建立外键约束
- 支持一个供应商多个银行账户（扩展性）
- 品牌关联独立表支持复杂查询

**替代方案**: 单表 + JSON 字段存储 `supplied_brands`
- 优点：简单，与 MongoDB 结构一致
- 缺点：无法建立外键约束，查询不便
- **不采用**

### 2. 表结构设计

```sql
-- 供应商主表
CREATE TABLE suppliers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    contact_person VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(200),
    address VARCHAR(500),
    remark TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 银行账户表
CREATE TABLE supplier_bank_accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    bank_name VARCHAR(200),
    account_name VARCHAR(200),
    account_no VARCHAR(50),
    is_default BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
);

-- 供应商-品牌关联表
CREATE TABLE supplier_brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    brand_id INT NOT NULL,
    discount DECIMAL(5,4) DEFAULT 1.0,
    is_priority BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
    UNIQUE KEY uk_supplier_brand (supplier_id, brand_id)
);
```

### 3. ID 类型变更

**决策**: ID 从 MongoDB ObjectId（24字符字符串）改为 MySQL INT

**理由**:
- 与其他已迁移模块保持一致
- INT 自增主键性能更好
- 前端需要适配类型变化

**影响**:
- 前端 TypeScript 类型需从 `string` 改为 `number`
- API 响应中 `id` 字段类型变化

### 4. 采购单外键约束

**决策**: 在 `purchase_orders` 表添加 `supplier_id` 外键

```sql
ALTER TABLE purchase_orders
ADD CONSTRAINT fk_purchase_order_supplier
FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL;
```

**理由**:
- 保证数据完整性
- 供应商删除时采购单保留（SET NULL）

## Risks / Trade-offs

### 风险1: 数据迁移失败
**[数据丢失风险]** → 迁移脚本使用事务，失败自动回滚；迁移前备份数据

### 风险2: 前端类型不兼容
**[运行时错误风险]** → 前端类型定义同步更新；API 文档明确标注类型变化

### 风险3: MongoDB ObjectId 无法直接映射
**[品牌关联断裂风险]** → 迁移脚本需要先查询品牌表，将 ObjectId 映射到 MySQL INT ID

### 风险4: 现有采购单数据
**[外键约束失败风险]** → 迁移时先迁移供应商，再更新采购单的 supplier_id

## Migration Plan

### 阶段1: 数据库准备
1. 创建 MySQL 表结构
2. 编写迁移脚本

### 阶段2: 数据迁移
1. 导出 MongoDB 供应商数据
2. 映射品牌 ObjectId 到 MySQL ID
3. 导入 MySQL 表
4. 验证数据完整性

### 阶段3: 代码切换
1. 更新后端服务层
2. 更新 API 路由
3. 更新前端组件
4. 更新 API 文档

### 阶段4: 清理
1. 删除 MongoDB 供应商集合（可选）
2. 删除旧模型文件

### 回滚策略
- 保留 MongoDB 数据不删除
- 代码可通过 Git 回滚
- MySQL 表可删除重建
