## ADDED Requirements

### Requirement: MySQL 数据库连接

系统 SHALL 支持 MySQL 数据库连接，使用 Tortoise ORM 作为异步 ORM 层。

#### Scenario: 数据库初始化
- **WHEN** 应用启动时
- **THEN** 系统 SHALL 初始化 Tortoise ORM 连接 MySQL 数据库
- **AND** 系统 SHALL 同时保持 MongoDB 连接（其他模块使用）

#### Scenario: 数据库配置
- **WHEN** 配置数据库连接时
- **THEN** 系统 SHALL 从 settings.py 读取 MySQL 连接参数（host、port、user、password、database）

---

### Requirement: 用户模型（MySQL）

系统 SHALL 使用 Tortoise ORM 定义 User 模型，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntField (PK) | 自增主键 |
| username | CharField(50, unique) | 用户名 |
| password | CharField(255) | 密码（bcrypt hash） |
| email | CharField(100, unique, null) | 邮箱 |
| phone | CharField(20, unique, null) | 手机号 |
| full_name | CharField(100, null) | 全名 |
| avatar | CharField(500, null) | 头像 URL |
| status | CharEnumField | 状态（active/inactive/locked） |
| roles | ManyToManyField | 关联角色 |
| last_login | DatetimeField(null) | 最后登录时间 |
| created_at | DatetimeField(auto_now_add) | 创建时间 |
| updated_at | DatetimeField(auto_now) | 更新时间 |

#### Scenario: 用户创建
- **WHEN** 创建新用户时
- **THEN** 系统 SHALL 校验用户名唯一性
- **AND** 系统 SHALL 对密码进行 bcrypt 加密
- **AND** 系统 SHALL 返回用户 ID 为整数类型

#### Scenario: 用户角色关联
- **WHEN** 为用户分配角色时
- **THEN** 系统 SHALL 通过 user_roles 关联表建立关系
- **AND** 系统 SHALL 支持批量分配多个角色

---

### Requirement: 角色模型（MySQL）

系统 SHALL 使用 Tortoise ORM 定义 Role 模型，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntField (PK) | 自增主键 |
| code | CharField(50, unique) | 角色编码（业务保留） |
| name | CharField(100) | 角色名称 |
| description | CharField(500, null) | 描述 |
| is_fixed | BooleanField | 是否固化角色 |
| status | CharEnumField | 状态（active/inactive） |
| permissions | ManyToManyField | 关联权限 |
| created_at | DatetimeField(auto_now_add) | 创建时间 |
| updated_at | DatetimeField(auto_now) | 更新时间 |

#### Scenario: 角色编码保留
- **WHEN** 创建或查询角色时
- **THEN** 系统 SHALL 保留角色编码（code）用于业务逻辑判断
- **AND** code 值 SHALL 为：super_admin、warehouse_admin、purchaser_group、user

#### Scenario: 固化角色保护
- **WHEN** 尝试删除固化角色（is_fixed=True）时
- **THEN** 系统 SHALL 拒绝删除操作
- **AND** 系统 SHALL 返回错误信息"固化角色不允许删除"

---

### Requirement: 权限模型（MySQL）

系统 SHALL 使用 Tortoise ORM 定义 Permission 模型，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | IntField (PK) | 自增主键 |
| code | CharField(100, unique) | 权限编码（业务保留） |
| name | CharField(100) | 权限名称 |
| type | CharEnumField | 类型（menu/button/button,tools/tools/api） |
| path | CharField(200, null) | 路径/路由 |
| parent_id | IntField (FK, null) | 父权限 ID |
| description | CharField(500, null) | 描述 |
| sort_order | IntField | 排序 |
| created_at | DatetimeField(auto_now_add) | 创建时间 |
| updated_at | DatetimeField(auto_now) | 更新时间 |

#### Scenario: 权限树结构
- **WHEN** 查询权限树时
- **THEN** 系统 SHALL 通过 parent_id 自关联构建树形结构
- **AND** 子权限 SHALL 挂载到对应父权限下

#### Scenario: 权限编码保留
- **WHEN** 进行权限判断时
- **THEN** 系统 SHALL 使用权限编码（code）进行匹配
- **AND** code 格式 SHALL 为：`<模块>.<操作>`（如 user.view、product.create）

---

### Requirement: 用户服务层

系统 SHALL 提供 UserService，使用 Tortoise ORM 实现用户 CRUD 操作。

#### Scenario: 用户列表查询
- **WHEN** 查询用户列表时
- **THEN** 系统 SHALL 支持分页（page、page_size）
- **AND** 系统 SHALL 支持关键词搜索（username、full_name、email）
- **AND** 系统 SHALL 支持状态筛选
- **AND** 系统 SHALL 预加载角色信息（prefetch_related）

#### Scenario: 用户详情查询
- **WHEN** 查询用户详情时
- **THEN** 系统 SHALL 返回用户基本信息
- **AND** 系统 SHALL 返回关联角色列表
- **AND** 系统 SHALL 返回用户权限编码列表（聚合所有角色的权限）

#### Scenario: 用户认证
- **WHEN** 用户登录时
- **THEN** 系统 SHALL 校验用户名和密码
- **AND** 系统 SHALL 生成 JWT Token（包含用户 ID、角色、权限）

---

### Requirement: 角色服务层

系统 SHALL 提供 RoleService，使用 Tortoise ORM 实现角色 CRUD 操作。

#### Scenario: 角色创建
- **WHEN** 创建角色时
- **THEN** 系统 SHALL 校验角色编码唯一性
- **AND** 系统 SHALL 关联指定权限

#### Scenario: 角色列表查询
- **WHEN** 查询角色列表时
- **THEN** 系统 SHALL 支持分页
- **AND** 系统 SHALL 支持关键词搜索
- **AND** 系统 SHALL 预加载权限信息

---

### Requirement: 权限服务层

系统 SHALL 提供 PermissionService，使用 Tortoise ORM 实现权限操作。

#### Scenario: 权限树查询
- **WHEN** 查询权限树时
- **THEN** 系统 SHALL 返回树形结构（父权限包含子权限列表）
- **AND** 系统 SHALL 按 sort_order 排序

#### Scenario: 权限列表查询
- **WHEN** 查询权限列表时
- **THEN** 系统 SHALL 支持关键词搜索
- **AND** 系统 SHALL 支持分页

---

### Requirement: 用户权限 API 路由

系统 SHALL 提供用户、角色、权限的 API 路由，遵循项目规范（product.py 模式）。

#### Scenario: 路由结构
- **WHEN** 定义 API 路由时
- **THEN** 系统 SHALL 使用独立 APIRouter：
  - user_router: `/users`
  - role_router: `/roles`
  - permission_router: `/permissions`

#### Scenario: 路由编写规范
- **WHEN** 编写路由函数时
- **THEN** 系统 SHALL 使用 `@wrap_response` 装饰器
- **AND** 系统 SHALL 使用 `require_permission` 进行权限校验
- **AND** 系统 SHALL 使用 `Dict[str, Any]` 接收请求体

#### Scenario: API 响应格式
- **WHEN** 返回 API 响应时
- **THEN** 系统 SHALL 返回标准格式：
  ```json
  {
    "status": "success",
    "message": "操作成功",
    "result": { "id": 1, ... }
  }
  ```
- **AND** id 字段 SHALL 为整数类型

---

### Requirement: 数据库初始化脚本

系统 SHALL 提供 MySQL 版本的数据库初始化脚本（init_db_mysql.py）。

#### Scenario: 初始化权限
- **WHEN** 运行初始化脚本时
- **THEN** 系统 SHALL 创建约 60 条权限记录
- **AND** 系统 SHALL 建立父子权限关系

#### Scenario: 初始化角色
- **WHEN** 运行初始化脚本时
- **THEN** 系统 SHALL 创建 4 个固化角色：
  - super_admin：拥有所有权限
  - warehouse_admin：仓库+库存权限
  - purchaser_group：采购+订单查看权限
  - user：基础业务权限

#### Scenario: 初始化管理员
- **WHEN** 运行初始化脚本时
- **THEN** 系统 SHALL 创建默认管理员账号（admin / admin123）
- **AND** 系统 SHALL 绑定 super_admin 角色

#### Scenario: 幂等性
- **WHEN** 多次运行初始化脚本时
- **THEN** 系统 SHALL 跳过已存在的数据
- **AND** 系统 SHALL 不重复创建

---

### Requirement: 前端 ID 类型适配

系统 SHALL 更新前端用户权限相关组件的 ID 类型定义。

#### Scenario: TypeScript 类型更新
- **WHEN** 定义用户、角色、权限类型时
- **THEN** 系统 SHALL 将 id 字段定义为 `number` 类型

#### Scenario: API 调用适配
- **WHEN** 调用用户权限 API 时
- **THEN** 前端 SHALL 正确处理整数类型 ID
- **AND** 路径参数 SHALL 为数字类型

---

### Requirement: 数据库迁移工具

系统 SHALL 使用 Aerich 作为数据库迁移工具。

#### Scenario: 迁移初始化
- **WHEN** 初始化 Aerich 时
- **THEN** 系统 SHALL 创建 migrations 目录
- **AND** 系统 SHALL 生成初始迁移脚本

#### Scenario: 迁移执行
- **WHEN** 执行迁移时
- **THEN** 系统 SHALL 创建所有定义的表
- **AND** 系统 SHALL 创建外键约束和索引