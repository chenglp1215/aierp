## Why

当前项目使用 MongoDB 作为主数据库，但团队对 Django ORM 更熟悉。为了降低学习成本、提高开发效率，决定将用户权限模块从 MongoDB 迁移到 MySQL，使用 Tortoise ORM（API 风格类似 Django ORM，原生支持异步）。

这是渐进式迁移的第一步，后续其他模块将逐步迁移。

## What Changes

- **新增 MySQL 数据库支持**：添加 Tortoise ORM 作为 MySQL 异步 ORM 层
- **重写用户权限模块**：使用 Tortoise ORM 重构 User、Role、Permission 模型和服务
- **数据结构规范化**：将 MongoDB 嵌套数组（role_ids、permission_ids）拆分为关联表
- **ID 类型变更**：从 MongoDB ObjectId（字符串）改为 MySQL 自增整数
- **前端适配**：用户、角色、权限相关组件的 ID 类型改为 number
- **初始化脚本迁移**：init_db.py 迁移到 MySQL 版本
- **BREAKING**: 用户权限相关 API 响应中 id 字段从字符串变为整数

## Capabilities

### New Capabilities

- `mysql-auth-module`: 用户权限模块的 MySQL 实现，包含 User、Role、Permission 的 ORM 模型、服务层和 API 路由

### Modified Capabilities

- `backend-base-spec`: 技术栈新增 MySQL + Tortoise ORM，数据库连接层支持双数据库
- `backend-modules-spec`: 用户权限模块从 MongoDB 切换到 MySQL，ID 类型变更
- `frontend-base-spec`: 用户权限相关 TypeScript 类型定义更新（id: string → id: number）

## Impact

**后端影响**：
- `backend/requirements.txt`: 新增 tortoise-orm[aiomysql]、aerich
- `backend/config/settings.py`: 新增 MySQL 连接配置
- `backend/app/database.py`: 新增 Tortoise 初始化
- `backend/models_mysql/`: 新增 Tortoise ORM 模型目录
- `backend/services/auth_service.py`: 重写为 Tortoise 版本
- `backend/app/routers/auth.py`: 重写路由（遵循 product.py 模式）
- `backend/scripts/init_db.py`: 迁移到 MySQL 版本

**前端影响**：
- `web/src/types/`: 用户权限相关类型定义更新
- `web/src/components/workspace/`: UserManagement、RoleManagement、PermissionManagement 组件适配

**数据库影响**：
- 新增 MySQL 数据库，包含 users、roles、permissions、user_roles、role_permissions 表
- MongoDB 用户权限相关集合保留（只读备份）
