## Why

当前供应商模块使用 MongoDB 存储，存在以下问题：
1. 与系统其他已迁移到 MySQL 的核心模块（客户、商品、采购单、销售订单等）数据源不一致
2. MongoDB 的嵌入式文档结构（如 `supplied_brands` 数组）难以通过外键约束保证数据完整性
3. 采购单中 `supplier_id` 字段无法建立外键关联，存在数据一致性风险
4. 需要统一数据层架构，便于后续维护和性能优化

## What Changes

- **数据模型迁移**: 将供应商从 MongoDB 集合迁移到 MySQL 表
  - 创建 `suppliers` 主表
  - 创建 `supplier_brands` 关联表（替代嵌入式数组，建立外键关联）
  - 创建 `supplier_bank_accounts` 表（银行账户信息独立存储）
- **外键约束**: 建立供应商与品牌、采购单之间的外键关联
- **API 接口调整**: 保持 RESTful API 路径不变，内部实现迁移到 Tortoise ORM
- **数据迁移脚本**: 提供从 MongoDB 到 MySQL 的数据迁移工具
- **前端适配**: 调整前端组件对接新的数据结构（ID 从字符串变为整数）

## Capabilities

### New Capabilities

- `supplier-mysql-model`: 供应商 MySQL 数据模型（Tortoise ORM），包含主表、品牌关联表、银行账户表
- `supplier-data-migration`: MongoDB 到 MySQL 的数据迁移脚本

### Modified Capabilities

- `supplier-api`: 供应商管理 API 接口实现从 MongoDB 迁移到 MySQL
- `supplier-frontend`: 前端供应商管理组件适配新的数据结构

## Impact

### 后端影响

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/models_mysql/supplier.py` | 新增 | 供应商 ORM 模型 |
| `backend/models_mysql/__init__.py` | 修改 | 导出新模型 |
| `backend/services/supplier_service.py` | 重写 | 迁移到 Tortoise ORM |
| `backend/validators/supplier_validator.py` | 保留 | 校验逻辑不变 |
| `backend/app/routers/supplier.py` | 微调 | 适配新服务层 |
| `backend/app/routers/api_docs/supplier.md` | 更新 | 更新 API 文档 |
| `backend/scripts/migrate_supplier_to_mysql.py` | 新增 | 数据迁移脚本 |
| `backend/tests/test_supplier_api.py` | 更新 | 适配新接口 |

### 前端影响

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `web/src/components/workspace/SupplierWorkspace.vue` | 修改 | 适配整数 ID |
| `web/src/services/api.ts` | 修改 | 更新类型定义 |

### 数据库影响

- 新增表: `suppliers`, `supplier_brands`, `supplier_bank_accounts`
- 修改表: `purchase_orders` 添加外键约束 `supplier_id`

### API 兼容性

- **路径不变**: `/api/v1/suppliers/*` 保持不变
- **响应格式变化**: `id` 从 MongoDB ObjectId 字符串变为 MySQL 整数
- **BREAKING**: 前端需要适配整数 ID
