## 1. 数据模型创建

- [x] 1.1 创建 `backend/models_mysql/supplier.py`，定义 `Supplier`、`SupplierBankAccount`、`SupplierBrand` 模型
- [x] 1.2 更新 `backend/models_mysql/__init__.py`，导出新模型
- [x] 1.3 创建数据库迁移文件，生成表结构

## 2. 服务层迁移

- [x] 2.1 创建 `backend/services/supplier_service_mysql.py`，使用 Tortoise ORM 实现供应商服务
- [x] 2.2 实现供应商 CRUD 操作（创建、查询、更新、删除）
- [x] 2.3 实现银行账户管理功能
- [x] 2.4 实现品牌关联管理功能
- [x] 2.5 实现供应商列表查询（分页、搜索、筛选）
- [x] 2.6 实现按品牌查询供应商功能
- [x] 2.7 实现供应商激活状态切换功能

## 3. API 路由调整

- [x] 3.1 更新 `backend/app/routers/supplier.py`，使用新服务层
- [x] 3.2 调整路由参数类型（字符串 ID 改为整数 ID）
- [x] 3.3 更新响应格式，确保 ID 为整数类型

## 4. 数据迁移脚本

- [x] 4.1 创建 `backend/scripts/migrate_supplier_to_mysql.py`
- [x] 4.2 实现 MongoDB 数据读取逻辑
- [x] 4.3 实现品牌 ObjectId 到 MySQL ID 的映射逻辑
- [x] 4.4 实现数据插入逻辑（供应商、银行账户、品牌关联）
- [x] 4.5 添加事务支持和错误处理
- [x] 4.6 添加数据验证和统计输出

## 5. API 测试脚本

- [x] 5.1 更新 `backend/tests/test_supplier_api.py`，适配新接口
- [x] 5.2 编写创建供应商测试（包含银行账户和品牌关联）
- [x] 5.3 编写查询供应商列表测试
- [x] 5.4 编写获取供应商详情测试
- [x] 5.5 编写更新供应商测试
- [x] 5.6 编写删除供应商测试
- [x] 5.7 编写按品牌查询供应商测试
- [ ] 5.8 执行测试验证所有接口功能（需要启动后端服务）

## 6. API 文档更新

- [x] 6.1 更新 `backend/app/routers/api_docs/supplier.md`
- [x] 6.2 更新数据模型说明（ID 类型变更）
- [x] 6.3 更新请求/响应示例
- [x] 6.4 添加迁移注意事项说明

## 7. 前端适配

- [x] 7.1 更新 `web/src/services/api.ts`，调整供应商相关类型定义
- [x] 7.2 更新 `SupplierWorkspace.vue`，适配整数 ID
- [x] 7.3 调整表单数据处理逻辑
- [x] 7.4 调整列表显示逻辑
- [ ] 7.5 验证前端功能正常（需要启动前端服务）

## 8. 验证与清理

- [ ] 8.1 执行完整功能测试（前后端联调）
- [ ] 8.2 验证采购单关联供应商功能正常
- [x] 8.3 清理旧的 MongoDB 模型文件（可选保留）