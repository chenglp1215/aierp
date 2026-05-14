## 1. 删除无依赖的 MongoDB 模型文件

- [x] 1.1 删除 `backend/models/auth.py`（MongoDB 版 Pydantic 模型）
- [x] 1.2 删除 `backend/models/product.py`（MongoDB 版 Pydantic 模型）

## 2. 删除 MongoDB 版商品服务

- [x] 2.1 删除 `backend/services/product_service.py`（MongoDB 版服务层）

## 3. 重构 auth_service.py

- [x] 3.1 删除 `AuthService` 类（MongoDB 版用户服务）
- [x] 3.2 删除 `RoleService` 类（MongoDB 版角色服务）
- [x] 3.3 删除 `PermissionService` 类（MongoDB 版权限服务）
- [x] 3.4 删除 `auth_service`、`role_service`、`permission_service` 实例
- [x] 3.5 保留 MySQL 版服务类和实例

## 4. 更新服务导出

- [x] 4.1 更新 `backend/services/__init__.py`，移除 MongoDB 版服务导出

## 5. 迁移依赖模块

- [x] 5.1 更新 `backend/app/middleware.py`：将 `auth_service.get_user_by_id` 改为 `mysql_user_service.get_by_id`
- [x] 5.2 更新 `backend/app/routers/ws.py`：将 `auth_service.get_user_by_id` 改为 `mysql_user_service.get_by_id`
- [x] 5.3 更新 `backend/services/sales_order_service.py`：迁移到 MySQL 版 product_service
- [x] 5.4 更新 `backend/services/customer_service.py`：迁移到 MySQL 版服务
- [x] 5.5 更新 `backend/services/inventory_service.py`：迁移到 MySQL 版 product_service

## 6. 验证

- [x] 6.1 运行后端测试，确保无导入错误
- [x] 6.2 验证 API 响应格式正确
- [x] 6.3 验证用户认证流程正常

## 7. 待用户评估

以下文件需要用户确认处理方式：

- [x] 7.1 `backend/app/agent/tools/product.py` - Agent 工具是否仍在使用？如使用需迁移到 MySQL 版
- [x] 7.2 `backend/scripts/init_db.py` - 初始化脚本是否需要迁移到 MySQL？
- [x] 7.3 `backend/scripts/shell.py` - 调试脚本是否需要更新？
