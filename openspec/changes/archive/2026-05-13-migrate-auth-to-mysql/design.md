## Context

当前用户权限模块使用 MongoDB + Motor 实现，存在以下问题：
1. 团队对 Django ORM 更熟悉，MongoDB 学习成本较高
2. 嵌套数组（role_ids、permission_ids）导致关联查询复杂
3. 无数据库 Schema，缺乏外键约束
4. 无迁移工具，数据库变更难以追踪

本次迁移采用渐进式策略，仅迁移用户权限模块，其他模块保持 MongoDB。

## Goals / Non-Goals

**Goals:**
- 使用 Tortoise ORM 实现 MySQL 版用户权限模块
- API 风格类似 Django ORM，降低学习成本
- 数据结构完全规范化（一对多关联表）
- 保持现有 API 接口不变（除 ID 类型外）
- 保留业务编码（role.code、permission.code）
- 提供数据库迁移工具（Aerich）

**Non-Goals:**
- 不迁移其他业务模块（商品、订单、库存等）
- 不实现双数据库同步写入
- 不保留 MongoDB ObjectId 映射（直接使用新 ID）

## Decisions

### 1. ORM 选型：Tortoise ORM

**选择 Tortoise ORM 的原因：**
- API 风格类似 Django ORM：`User.filter()`、`User.get()`、`prefetch_related()`
- 原生异步支持，专为 async/await 设计
- 内置 Pydantic 集成，模型可直接生成 schema
- 轻量级，与 FastAPI 集成简单

**备选方案：**
- SQLAlchemy ORM：功能强大但 API 风格差异大，学习成本高
- SQLModel：FastAPI 作者开发，但 Django 相似度不如 Tortoise

### 2. 数据结构设计：完全规范化

**表结构：**
```
users                 roles                  permissions
├── id (PK)           ├── id (PK)            ├── id (PK)
├── username          ├── code (业务编码)     ├── code (业务编码)
├── password          ├── name               ├── name
├── ...               ├── ...                ├── type
└── ...               └── ...                ├── parent_id (FK→permissions.id)
                                             └── ...

user_roles            role_permissions
├── id (PK)            ├── id (PK)
├── user_id (FK)       ├── role_id (FK)
└── role_id (FK)       └── permission_id (FK)
```

**设计决策：**
- 使用多对多关联表替代嵌套数组
- 业务编码（code）保留，用于权限判断
- 权限树通过 parent_id 自关联实现

### 3. ID 策略：MySQL 自增整数

**选择自增整数的原因：**
- 简单、高效、易读
- 前端适配成本低（类型改为 number）
- 无需维护 ObjectId 映射表

**前端适配：**
- TypeScript 类型定义：`id: number`
- 组件无需大改，仅类型声明调整

### 4. 初始化数据迁移

**策略：**
- 重写 init_db_mysql.py，直接在 MySQL 初始化数据
- 不从 MongoDB 迁移历史数据（开发阶段）
- 保留 init_db.py 作为 MongoDB 版本备份

**初始化数据：**
- 权限：约 60 条（菜单 + 按钮/工具）
- 角色：4 个固化角色（super_admin、warehouse_admin、purchaser_group、user）
- 用户：1 个默认管理员（admin / admin123）

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| 前端 ID 类型变更可能导致运行时错误 | 全面测试用户权限相关组件，类型检查 |
| 双数据库并存增加复杂度 | 明确模块边界，用户权限只用 MySQL |
| Tortoise ORM 生态不如 SQLAlchemy | 功能足够满足需求，社区活跃 |
| 迁移期间认证可能中断 | 先实现后切换，确保测试通过后再部署 |
