## 1. 基础设施层

- [ ] 1.1 添加依赖到 requirements.txt：tortoise-orm[aiomysql]、aerich
- [ ] 1.2 更新 settings.py：添加 MySQL 连接配置（MYSQL_HOST、MYSQL_PORT、MYSQL_USER、MYSQL_PASSWORD、MYSQL_DATABASE）
- [ ] 1.3 更新 .env.example：添加 MySQL 连接示例
- [ ] 1.4 创建 models_mysql/__init__.py：导出所有 ORM 模型
- [ ] 1.5 更新 database.py：添加 Tortoise ORM 初始化函数
- [ ] 1.6 初始化 Aerich：运行 aerich init，配置迁移目录

## 2. ORM 模型定义

- [ ] 2.1 创建 models_mysql/auth.py：定义 UserStatus、RoleStatus、PermissionType 枚举
- [ ] 2.2 创建 Permission 模型：id、code、name、type、path、parent_id、description、sort_order、created_at、updated_at
- [ ] 2.3 创建 Role 模型：id、code、name、description、is_fixed、status、permissions（多对多）、created_at、updated_at
- [ ] 2.4 创建 User 模型：id、username、password、email、phone、full_name、avatar、status、roles（多对多）、last_login、created_at、updated_at
- [ ] 2.5 运行 aerich migrate --name "init_auth_tables"：生成初始迁移脚本
- [ ] 2.6 运行 aerich upgrade：执行数据库迁移

## 3. 服务层实现

- [ ] 3.1 创建 UserService 类：get_by_id、get_by_username、create_user、update_user、delete_user、list_users
- [ ] 3.2 实现 UserService.get_by_id：预加载 roles 和 roles__permissions
- [ ] 3.3 实现 UserService.create_user：校验唯一性、密码加密、角色关联
- [ ] 3.4 实现 UserService.list_users：支持分页、关键词搜索、状态筛选
- [ ] 3.5 创建 RoleService 类：get_by_id、get_by_code、create_role、update_role、delete_role、list_roles
- [ ] 3.6 实现 RoleService.create_role：校验编码唯一性、权限关联
- [ ] 3.7 创建 PermissionService 类：get_tree、list_permissions
- [ ] 3.8 实现 PermissionService.get_tree：构建树形结构、按 sort_order 排序
- [ ] 3.9 创建服务实例：user_service、role_service、permission_service

## 4. 路由层实现

- [ ] 4.1 创建 user_router：GET /users（列表）、GET /users/{user_id}（详情）、POST /users（创建）、PUT /users/{user_id}（更新）、DELETE /users/{user_id}（删除）
- [ ] 4.2 创建 role_router：GET /roles（列表）、GET /roles/{role_id}（详情）、POST /roles（创建）、PUT /roles/{role_id}（更新）、DELETE /roles/{role_id}（删除）
- [ ] 4.3 创建 permission_router：GET /permissions（列表）、GET /permissions/tree（权限树）
- [ ] 4.4 更新认证相关路由：POST /auth/login（登录）、GET /auth/me（当前用户）、POST /auth/change-password（修改密码）
- [ ] 4.5 更新 routers/__init__.py：注册新路由

## 5. 认证中间件适配

- [ ] 5.1 更新 middleware.py：适配 Tortoise ORM 用户查询
- [ ] 5.2 更新 require_permission：使用 Tortoise ORM 查询用户权限
- [ ] 5.3 更新 JWT Token 生成：sub 使用整数 ID

## 6. 初始化脚本

- [ ] 6.1 创建 scripts/init_db_mysql.py：MySQL 版初始化脚本
- [ ] 6.2 实现 init_default_permissions：创建约 60 条权限，建立父子关系
- [ ] 6.3 实现 init_super_admin_group：创建超级管理员角色，关联所有权限
- [ ] 6.4 实现 init_warehouse_admin_group：创建仓库管理员角色
- [ ] 6.5 实现 init_purchaser_group：创建采购组角色
- [ ] 6.6 实现 init_admin_user：创建默认管理员账号
- [ ] 6.7 实现 init_default_roles：创建普通用户角色
- [ ] 6.8 测试初始化脚本：运行 init_db_mysql.py，验证数据正确

## 7. 前端适配

- [ ] 7.1 更新 web/src/types/user.ts：id 字段改为 number 类型
- [ ] 7.2 更新 web/src/types/role.ts：id 字段改为 number 类型
- [ ] 7.3 更新 web/src/types/permission.ts：id、parent_id 字段改为 number 类型
- [ ] 7.4 检查 UserManagement.vue：适配整数 ID
- [ ] 7.5 检查 RoleManagement.vue：适配整数 ID
- [ ] 7.6 检查 PermissionManagement.vue：适配整数 ID

## 8. 测试与验证

- [ ] 8.1 更新 backend/tests/test_auth_api.py：适配 MySQL
- [ ] 8.2 测试用户登录：验证 JWT Token 生成正确
- [ ] 8.3 测试用户 CRUD：验证列表、详情、创建、更新、删除
- [ ] 8.4 测试角色 CRUD：验证列表、详情、创建、更新、删除
- [ ] 8.5 测试权限树：验证树形结构正确
- [ ] 8.6 测试权限校验：验证 require_permission 正常工作
- [ ] 8.7 前端集成测试：验证用户管理、角色管理、权限管理页面正常

## 9. 文档更新

- [ ] 9.1 更新 .project_docs/backend/项目基础规范.md：技术栈新增 MySQL + Tortoise ORM
- [ ] 9.2 更新 .project_docs/backend/项目模块说明.md：用户权限模块说明更新
- [ ] 9.3 更新 README.md：数据库配置说明
