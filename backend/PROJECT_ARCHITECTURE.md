# AI MDR Platform Backend - 项目架构文档

## 项目概述

### 项目简介
AI MDR Platform Backend 是一个基于 FastAPI 的高性能异步 API 服务，为 AI MDR 平台提供后端支持。项目采用现代化的 Python 异步架构，支持 MongoDB 和 Redis 数据存储。

### 技术栈
- **Web 框架**: FastAPI 0.115.0 (异步、高性能)
- **数据库**: MongoDB (Motor 异步驱动)
- **缓存**: Redis (asyncio 版本)
- **数据验证**: Pydantic V2
- **配置管理**: Pydantic Settings
- **认证**: JWT (python-jose)
- **测试**: pytest + pytest-asyncio
- **代码质量**: Black, isort, flake8

## 目录结构

```
backend/
├── app/
│   ├── __init__.py          # 应用工厂，创建 FastAPI 实例
│   ├── database.py          # 数据库连接管理 (MongoDB + Redis)
│   ├── middleware.py        # 中间件 (日志记录)
│   └── routers/             # 路由模块
│       ├── __init__.py      # 路由聚合
│       └── health.py        # 健康检查路由
├── config/
│   ├── __init__.py          # 配置导出
│   └── settings.py          # 配置管理 (Pydantic Settings)
├── models/                  # 数据模型 (空目录，待扩展)
├── services/                # 业务逻辑服务 (空目录，待扩展)
├── utils/                   # 工具函数 (空目录，待扩展)
├── tests/                   # 测试目录 (空目录，待扩展)
├── main.py                  # 应用入口点
├── requirements.txt         # 项目依赖
├── .env.example             # 环境变量示例
├── .gitignore               # Git 忽略文件
└── README.md                # 项目说明文档
```

## 模块职责说明

### app/__init__.py
- **职责**: 应用工厂，创建 FastAPI 实例
- **功能**:
  - 创建 FastAPI 应用实例
  - 配置 CORS 中间件
  - 注册路由
  - 管理应用生命周期 (启动/关闭)

### app/database.py
- **职责**: 数据库连接管理
- **功能**:
  - MongoDB 连接管理 (Motor)
  - Redis 连接管理
  - 连接初始化和关闭
  - 提供数据库访问接口

### app/middleware.py
- **职责**: 中间件管理
- **功能**:
  - 请求日志记录
  - 响应时间统计
  - **认证中间件 (AuthMiddleware)**: 全局 JWT token 验证
  - **权限中间件 (PermissionMiddleware)**: 资源访问权限验证
- **重要**: 中间件必须在 `app/__init__.py` 中通过 `app.add_middleware()` 注册才会生效

### app/routers/
- **职责**: API 路由管理
- **子模块**:
  - `health.py`: 健康检查接口

### config/settings.py
- **职责**: 配置管理
- **功能**:
  - 环境变量读取
  - 配置验证
  - 配置访问接口

## 路由体系

### API 路由结构
```
/api/v1/
├── health/
│   ├── /          # 健康状态检查
│   └── /ping      # Ping 测试
```

### 统一响应格式
所有 API 响应遵循以下格式：
```json
{
  "status": "success|error",
  "message": "描述信息",
  "result": {},  // 数据结果
  "exc": null    // 异常信息
}
```

## 编码约定

### 命名规范
| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | 小写下划线 | `database.py`, `health.py` |
| 类 | 大驼峰 | `Database`, `LoggingMiddleware` |
| 函数 | 小写下划线 | `init_db`, `health_check` |
| 变量 | 小写下划线 | `mongo_client`, `redis_url` |
| 常量 | 全大写下划线 | `MONGODB_URL`, `SECRET_KEY` |

### 函数复杂度
- 单函数不超过 20 条语句
- 超过需拆分为子函数

### 注释要求
- 使用中文注释
- 复杂逻辑需解释原因

### 数据结构
- 使用 Pydantic 模型定义数据结构
- 所有 API 请求/响应使用 Pydantic 模型

### 异常处理
- 使用 FastAPI 的异常处理机制
- 统一异常响应格式

## 模块依赖关系

```
main.py
  ↓
app/__init__.py (创建应用)
  ↓
config/settings.py (配置)
  ↓
app/database.py (数据库连接)
  ↓
app/routers/ (路由)
  ↓
app/middleware.py (中间件)
```

## 技术债概览

### 高优先级
- [ ] 创建数据模型 (models/)
- [ ] 创建业务服务 (services/)
- [ ] 创建工具函数 (utils/)
- [ ] 编写单元测试 (tests/)

### 中优先级
- [ ] 添加认证和授权
- [ ] 添加请求验证
- [ ] 添加错误处理
- [ ] 添加日志系统

### 低优先级
- [ ] 添加 API 文档自定义
- [ ] 添加性能监控
- [ ] 添加缓存策略

## 开发规范

### 代码风格
- 使用 Black 格式化代码
- 使用 isort 管理导入顺序
- 使用 flake8 检查代码质量

### 测试规范
- 所有新功能必须编写测试
- 测试文件放在 `tests/` 目录
- 使用 pytest 和 pytest-asyncio

### Git 提交规范
- 使用语义化提交信息
- 提交前运行代码检查

## 快速启动指南

### 本地开发
```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 5. 启动服务
python main.py

# 6. 访问 API 文档
# http://localhost:8000/docs
```

### 数据库准备
```bash
# 启动 MongoDB (Docker)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# 启动 Redis (Docker)
docker run -d -p 6379:6379 --name redis redis:latest
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行测试并显示覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/test_health.py
```

## 最近变更记录

| 日期 | 变更内容 | 原因 |
|------|----------|------|
| 2026-04-16 | 创建项目基础结构 | 初始化 FastAPI 项目 |
| 2026-04-16 | 配置 MongoDB 和 Redis | 支持数据存储 |
| 2026-04-16 | 创建健康检查路由 | 提供服务状态监控 |
| 2026-04-16 | 添加认证中间件 AuthMiddleware | 实现登录状态验证 |
| 2026-04-16 | 实现前端登录、登出、路由守卫 | 完成完整认证流程 |
| 2026-04-16 | **客户管理模块**：添加收货地址模型 | 支持多收货人/收货地址 |
| 2026-04-16 | **客户管理模块**：完善前后端CRUD | 实现新建、编辑、删除客户功能 |
| 2026-04-16 | **前端**：完善客户管理界面 | 支持收货地址管理 |
| 2026-04-20 | **前端权限控制系统**：新增 hooks/权限指令 | 实现基于后端权限树的动态菜单、页签、按钮显示控制 |
| 2026-04-21 | **Agent Tool Schema 格式修复** | BaseTool.get_schema() 返回格式不符合 OpenAI 规范导致 400 错误 |
| 2026-04-21 | **Agent Tools 业务模块封装**：新增销售订单、客户管理、库存管理三大模块的 Agent Tools | 支持 AI 通过 Function Calling 调用业务功能 |
| 2026-04-21 | **Agent 权限过滤机制**：实现基于用户权限的动态 Tools 加载 | 用户只能使用其权限范围内的 Tools，节省 Token |
| 2026-04-21 | **React 模式工具调用**：实现标准 React 循环的工具调用机制 | 支持流式输出、工具调用状态实时通知前端 |

## 权限系统设计

### 概述
系统采用 **后端驱动** 的前端权限控制方案：
- 后端维护完整的权限树（菜单、按钮、API 权限）
- 前端根据用户角色权限动态显示/隐藏菜单项、页签、操作按钮

### 权限类型
| 类型 | 说明 | 示例 |
|------|------|------|
| menu | 菜单权限，控制侧边栏和页签显示 | `sales.order.view`、`crm.view` |
| button | 按钮权限，控制操作按钮显示 | `user.create`、`user.edit`、`user.delete` |
| api | API权限，后端接口级权限控制 | 后端路由守卫使用 |

### 前端权限控制文件
```
web/src/
├── hooks/
│   ├── index.ts              # hooks 导出
│   ├── usePermission.ts       # 权限 hook（核心）
│   └── permissionPlugin.ts    # v-permission 指令插件
```

### 权限映射表

#### 菜单权限映射 (MENU_PERMISSION_MAP)
| 菜单ID | 权限代码 | 说明 |
|--------|----------|------|
| dashboard | dashboard.view | 工作台 |
| chat | chat.view | 智能助手 |
| sales-order | order.view | 销售订单 |
| sales-contract | order.view | 销售合同 |
| sales-return | order.view | 退货管理 |
| inventory-stock | inventory.stock.view | 库存管理 |
| inventory-check | inventory.check.view | 库存盘点 |
| inventory-transfer | inventory.transfer.view | 调拨管理 |
| finance-invoice | finance.invoice.view | 发票管理 |
| finance-payment | finance.payment.view | 付款管理 |
| finance-report | finance.report.view | 财务报表 |
| crm | customer.menu | 客户管理 |
| system-account | user.menu | 账号管理 |
| system-intelligent | intelligent.settings.view | 智能设置 |
| system-user | user.menu | 用户管理 |
| system-role | role.menu | 角色管理 |
| system-permission | permission.menu | 权限管理 |

#### 按钮权限映射 (BUTTON_PERMISSION_MAP)
| 操作ID | 权限代码 |
|--------|----------|
| create | create |
| edit | edit |
| delete | delete |
| view | view |
| export | export |
| import | import |
| reset-password | reset-password |
| enable | enable |
| disable | disable |

### 使用方式

#### 1. 使用 usePermission Hook
```typescript
import { usePermission } from '@/hooks'

const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermission()

// 单个权限检查
if (hasPermission('user.create')) {
  // 有权限
}

// 任意一个权限检查
if (hasAnyPermission(['user.create', 'user.edit'])) {
  // 有任意一个权限
}

// 全部权限检查
if (hasAllPermissions(['user.create', 'user.edit'])) {
  // 有全部权限
}
```

#### 2. 使用 v-permission 指令
```vue
<template>
  <!-- 单个权限控制 -->
  <button v-permission="'user.create'">新建用户</button>

  <!-- 任意一个权限控制 -->
  <button v-has-any-permission="['user.edit', 'user.delete']">编辑/删除</button>

  <!-- 全部权限控制 -->
  <button v-has-all-permissions="['user.edit', 'user.reset-password']">编辑并重置密码</button>
</template>
```

#### 3. 菜单权限过滤（SidebarNav）
菜单ID与权限代码映射后自动过滤，无需额外代码

### 新增页面/功能时添加权限流程

#### Step 1: 后端添加权限数据
在 MongoDB 的 `permissions` 集合中添加权限文档：
```javascript
{
  "_id": ObjectId("..."),
  "code": "sales.order.create",      // 权限代码（唯一）
  "name": "创建销售订单",            // 权限名称
  "type": "button",                  // menu | button | api
  "path": "/sales-orders",           // 路由路径（可选）
  "parent_id": ObjectId("..."),      // 父权限ID（可选）
  "sort_order": 1,
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

#### Step 2: 前端添加权限映射
在 `web/src/hooks/usePermission.ts` 中的映射表添加：

**菜单权限**（如果新增页面）：
```typescript
export const MENU_PERMISSION_MAP: Record<string, string> = {
  // ... 现有映射
  'new-page': 'new.module.view',  // 新增
}
```

**按钮权限**（如果新增操作按钮）：
```typescript
export const BUTTON_PERMISSION_MAP: Record<string, string> = {
  // ... 现有映射
  'new-action': 'new.action',  // 新增
}
```

#### Step 3: 前端组件使用权限控制
**页面菜单**（SidebarNav.vue）：
- 菜单项已配置映射，自动过滤显示

**操作按钮**：
```vue
<button v-permission="'sales.order.create'">创建订单</button>
```

#### Step 4: 后端角色分配权限
在角色管理中，将新权限分配给相应角色

### 初始化权限数据脚本
可在系统初始化或部署时运行以下脚本添加默认权限：

```python
# 初始化销售模块权限
SALES_PERMISSIONS = [
    {"code": "sales.order.view", "name": "查看销售订单", "type": "menu", "path": "/sales/order"},
    {"code": "sales.order.create", "name": "创建销售订单", "type": "button"},
    {"code": "sales.order.edit", "name": "编辑销售订单", "type": "button"},
    {"code": "sales.order.delete", "name": "删除销售订单", "type": "button"},
    # ... 更多权限
]
```

### 注意事项
1. **admin 角色拥有所有权限**：代码中已处理 `role_codes.includes('admin')` 逻辑
2. **权限代码命名规范**：`模块.资源.操作`，如 `sales.order.create`
3. **菜单必须配置映射**：否则无法在 SidebarNav 中被正确过滤
4. **按钮权限需手动添加 v-permission 指令**：不会自动生效

## 开发经验总结

### 问题1: 登录/登出功能无法正常工作

#### 问题现象
1. 退出登录后页面没有跳转到登录页，仍然显示工作台
2. 直接访问 `/login` 也会跳转到工作台而不是登录页

#### 问题根因
1. **路由架构错误**：原有的 `App.vue` 直接挂载到 `#app`，没有 `<router-view>`，导致路由切换无效
2. **退出登录逻辑不完整**：只清除了 `token` 和 `user`，没有清除 `token_expires_at`
3. **路由守卫判断逻辑错误**：`/login` 路由的判断条件 `to.meta.requiresAuth === false` 无法正确区分登录页
4. **AuthMiddleware 未注册**：后端的认证中间件定义但没有在应用中注册使用

#### 正确做法
1. **正确的 Vue 路由架构**：
   - 创建 `App.vue` 作为根组件，只包含 `<router-view />`
   - 创建独立的布局组件（如 `DashboardLayout.vue`）用于认证后的页面
   - 在路由配置中正确指定组件
   
2. **退出登录必须清除所有认证数据**：
   ```typescript
   const keysToRemove = ['token', 'user', 'token_expires_at', 'remembered_username', 'remembered_password']
   keysToRemove.forEach(key => localStorage.removeItem(key))
   window.location.replace('/login')  // 使用 replace 而不是 href
   ```

3. **路由守卫正确判断逻辑**：
   ```typescript
   router.beforeEach((to, _from, next) => {
     // 访问登录页
     if (to.path === '/login') {
       const token = localStorage.getItem('token')
       if (token && !isTokenExpired()) {
         next('/dashboard')  // 已登录用户访问登录页，跳转到主页
         return
       }
       next()  // 未登录用户停留在登录页
       return
     }
     
     // 访问需要认证的页面
     if (to.meta.requiresAuth && isTokenExpired()) {
       clearAuthData()
       next('/login')  // token过期，跳转登录页
       return
     }
     
     next()
   })
   ```

4. **后端中间件必须注册**：
   ```python
   # 在 app/__init__.py 中
   app.add_middleware(AuthMiddleware)
   ```

#### 关键教训
- **Vue 单页应用架构基础**：SPA 应用必须有 `<router-view>` 作为路由出口
- **组件拆分原则**：布局组件和页面组件要分离
- **localStorage 要清除干净**：认证相关数据要全部清除，否则 `isTokenExpired()` 会返回错误结果
- **后端中间件必须注册**：仅仅定义中间件类而不注册是不会生效的
- **路由判断用具体路径**：`to.path === '/login'` 比 `to.meta.requiresAuth === false` 更可靠

### 问题2: 前端 401 响应没有触发自动登出

#### 问题根因
API 拦截器中虽然检测到 401 状态码，但后续处理逻辑可能因为某些原因没有正确执行

#### 正确做法
```typescript
if (response.status === 401) {
  clearAuthData()
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
  throw new Error('登录已过期')
}
```

### Vue Router 最佳实践
1. **根组件应该只包含路由出口**，不要包含业务布局
2. **布局组件单独创建**，按需加载
3. **路由守卫要处理所有边界情况**：登录页、主页、未认证、已认证
4. **退出登录使用 `window.location.replace()`** 避免浏览器历史记录问题

### 问题3: Agent Tool Schema 格式错误导致 API 调用失败

#### 问题现象
调用 Agent 服务时报错：
```
ERROR:app.agent.agent:Agent chat error: Error code: 400 - {'error': {'code': '400', 'message': 'Param Incorrect', 'param': '`function` is not set', 'type': ''}}
```

#### 问题根因
[app/agent/tools/base.py](file:///e:/wechat-bot-dev/sale_assistant/vibecoding/ai_mdr_platform/backend/app/agent/tools/base.py) 中 `BaseTool.get_schema()` 方法返回的格式不符合 OpenAI Function Calling 规范。

**错误格式**（修复前）：
```python
def get_schema(self) -> Dict[str, Any]:
    return {
        "name": self.name,
        "description": self.description,
        "parameters": self.parameters
    }
```

**正确格式**（修复后）：
```python
def get_schema(self) -> Dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    }
```

#### OpenAI Function Calling 规范
Tool schema 必须包含外层 `type` 和 `function` 包装：
```json
{
  "type": "function",
  "function": {
    "name": "tool_name",
    "description": "tool description",
    "parameters": { ... }
  }
}
```

#### 关键教训
- **集成外部 API 时必须严格遵循其规范**：OpenAI 的 function calling 格式是标准化的
- **LangChain 等封装库会自动处理格式转换**：但如果自己实现 schema，必须遵循官方格式
- **不同模型提供商的 API 格式可能不同**：mimo-v2-flash 遵循 OpenAI 标准

## Agent Tools 设计

### 概述
系统将业务功能封装为 Agent 可调用的 Tools，支持基于用户权限的动态加载。

### Tool 文件结构
```
app/agent/tools/
├── __init__.py
├── base.py              # BaseTool 基类
├── registry.py          # ToolRegistry 注册表
├── builtin.py           # 内置工具（知识库等）
├── sales_order.py       # 销售订单模块 Tools
├── customer.py          # 客户管理模块 Tools
└── inventory.py         # 库存管理模块 Tools
```

### Tool 权限映射

#### 销售订单模块 (Sales Order)
| Tool Name | Permission Code | 说明 |
|-----------|----------------|------|
| sales_order_search | order.view | 搜索/查看订单 |
| sales_order_create | order.create | 创建订单 |
| sales_order_update | order.edit | 更新订单 |
| sales_order_status | order.edit | 更新订单状态 |
| sales_order_payment | order.edit | 更新付款状态 |

#### 客户管理模块 (Customer)
| Tool Name | Permission Code | 说明 |
|-----------|----------------|------|
| customer_search | customer.view | 搜索/查看客户 |
| customer_create | customer.create | 创建客户 |
| customer_update | customer.edit | 更新客户信息 |
| customer_address | customer.edit | 管理收货地址 |
| customer_stats | customer.view | 客户统计 |

#### 库存管理模块 (Inventory)
| Tool Name | Permission Code | 说明 |
|-----------|----------------|------|
| stock_search | inventory.stock.view | 搜索库存 |
| stock_adjust | inventory.stock.edit | 调整库存 |
| stock_stats | inventory.stock.view | 库存统计 |
| warehouse_search | inventory.warehouse.view | 搜索仓库 |
| transfer_create | inventory.transfer.edit | 创建调拨单 |
| transfer_search | inventory.transfer.view | 搜索调拨单 |
| transfer_status | inventory.transfer.edit | 更新调拨状态 |

### Tool 设计原则
1. **Token 节省**：每个 Tool 参数尽量使用可选参数，默认值，减少 prompt 长度
2. **便捷性**：description 使用中文描述，AI 能准确判断何时调用
3. **权限控制**：通过 `permission_code` 字段关联权限，用户无权限时 Tool 不会暴露给 AI
4. **单一职责**：每个 Tool 只做一件事，避免复杂组合

### 权限过滤机制
1. **BaseTool** 新增 `permission_code` 字段
2. **ToolRegistry** 新增 `get_schemas(user_permissions)` 方法，支持按权限过滤
3. **Agent.chat()** 接收 `user_permissions` 参数，传递给 `_get_tools()`
4. **WebSocket** 聊天时从用户信息中提取 `permissions` 列表

### Tool 调用示例
```python
# Agent 根据用户权限自动过滤可用的 Tools
# 无 order.view 权限的用户，AI 不会看到 sales_order_search 等工具
response = await agent.chat(
    user_message="帮我查一下最近的订单",
    user_id=user_id,
    user_permissions=user_permissions  # 自动过滤无权限的 Tools
)
```

## React 模式工具调用实现

### 概述
系统实现了标准的 React (Reasoning + Action) 模式的 AI 工具调用，支持流式输出和实时工具调用状态通知。

### 核心机制
1. **流式输出**：AI 生成的文本内容实时流式返回给前端
2. **工具调用中断**：当 AI 需要调用工具时，文本输出暂停
3. **状态通知**：通过 WebSocket 向前端发送工具调用开始/结束消息
4. **多轮对话**：工具执行结果会作为上下文继续给 AI，进行多轮交互

### WebSocket 消息类型
| 消息类型 | 说明 | 包含字段 |
|---------|------|---------|
| `stream_start` | AI 开始生成回复 | agent_id |
| `stream` | AI 文本内容片段 | content, agent_id |
| `tool_call_start` | 工具开始调用 | tool, args, agent_id |
| `tool_call_end` | 工具调用结束 | tool, success, content, error, agent_id |
| `stream_end` | AI 回复生成完成 | content, agent_id |
| `error` | 错误信息 | content, agent_id |

### 实现类和方法
- **Agent.chat_with_tools_stream()**：核心方法，实现 React 循环
- **LLMClient.chat_with_tools_stream()**：LLM 流式接口
- **WebSocket 回调**：
  - `tool_call_callback`：工具开始调用时触发
  - `tool_result_callback`：工具执行完成时触发

### React 循环流程
```
用户消息
    ↓
AI 生成文本 (流式输出 content)
    ↓
AI 决定调用工具
    ↓
发送 tool_call_start 通知
    ↓
执行工具
    ↓
发送 tool_call_end 通知 (包含结果)
    ↓
工具结果加入上下文
    ↓
继续 AI 生成 (可能再次调用工具)
    ↓
...
直到 AI 不再调用工具
    ↓
发送 stream_end 通知
```

### 前端集成示例
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'stream':
      // 实时显示 AI 回复
      appendToChat(data.content);
      break;
    case 'tool_call_start':
      // 显示工具调用状态
      showToolCalling(data.tool, data.args);
      break;
    case 'tool_call_end':
      // 显示工具执行结果
      showToolResult(data.tool, data.success, data.content);
      break;
    case 'stream_end':
      // 回复完成
      finalizeChat(data.content);
      break;
  }
};
```
