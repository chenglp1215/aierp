## ADDED Requirements

### Requirement: MySQL 版用户服务

系统 SHALL 使用 MySQL 数据库存储用户数据，通过 Tortoise ORM 进行数据访问。

#### Scenario: 用户认证
- **WHEN** 用户使用用户名和密码登录
- **THEN** 系统使用 `mysql_user_service.authenticate_user` 验证凭据并返回 JWT Token

#### Scenario: 获取用户信息
- **WHEN** 系统需要获取用户信息
- **THEN** 系统使用 `mysql_user_service.get_by_id` 或 `mysql_user_service.get_by_username` 从 MySQL 获取用户数据

### Requirement: MySQL 版角色服务

系统 SHALL 使用 MySQL 数据库存储角色数据，通过 Tortoise ORM 进行数据访问。

#### Scenario: 角色管理
- **WHEN** 管理员创建、更新或删除角色
- **THEN** 系统使用 `mysql_role_service` 进行 CRUD 操作

### Requirement: MySQL 版权限服务

系统 SHALL 使用 MySQL 数据库存储权限数据，通过 Tortoise ORM 进行数据访问。

#### Scenario: 权限树查询
- **WHEN** 系统需要展示权限树
- **THEN** 系统使用 `mysql_permission_service.get_permission_tree` 从 MySQL 获取权限数据并构建树形结构

## REMOVED Requirements

### Requirement: MongoDB 版用户服务

**Reason**: 项目已迁移到 MySQL，MongoDB 版用户服务不再使用

**Migration**: 使用 `mysql_user_service` 替代 `auth_service`

### Requirement: MongoDB 版角色服务

**Reason**: 项目已迁移到 MySQL，MongoDB 版角色服务不再使用

**Migration**: 使用 `mysql_role_service` 替代 `role_service`

### Requirement: MongoDB 版权限服务

**Reason**: 项目已迁移到 MySQL，MongoDB 版权限服务不再使用

**Migration**: 使用 `mysql_permission_service` 替代 `permission_service`

### Requirement: MongoDB 版商品服务

**Reason**: 项目已迁移到 MySQL，MongoDB 版商品服务不再使用

**Migration**: 使用 `product_service_mysql` 中的服务替代 `product_service.py` 中的服务
