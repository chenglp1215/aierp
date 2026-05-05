# AI MDR Platform - 智能销售助手平台

<!-- 插入项目Logo或首页截图 -->
<!-- ![AI MDR Platform 首页](docs/images/homepage.png) -->

一个基于 AI Agent 的企业级智能销售助手平台，支持销售、采购、库存、财务、客户等核心业务模块的智能化管理。

---

## 目录

- [项目简介](#项目简介)
- [项目文档](#项目文档)
- [功能特点](#功能特点)
- [技术架构](#技术架构)
- [系统界面](#系统界面)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [API文档](#api文档)
- [部署指南](#部署指南)
- [开发指南](#开发指南)

---

## 项目简介

AI MDR Platform 是一款面向企业的智能化销售管理平台，融合了 AI Agent 技术与传统 ERP 功能。平台通过自然语言交互方式，简化业务流程，提升工作效率。

**核心定位**: 企业级 AI 驱动的销售管理解决方案

---

## 项目文档

项目开发文档统一存放在 `.project_docs/` 目录下：

```
.project_docs/
├── backend/
│   ├── 项目基础规范.md    # 架构、代码风格、接口规范、服务实现、模块拆分
│   ├── 项目模块说明.md    # 各业务模块的功能说明、API 列表
│   └── 项目业务说明.md    # 业务流转、业务注意事项、技术债
└── frontend/
    ├── 项目基础规范.md    # 架构、组件规范、路由规范、VxeTable 规范
    ├── 项目模块说明.md    # 各业务模块的功能说明、组件列表
    └── 项目业务说明.md    # 业务流转、业务注意事项
```

---

## 功能特点

### 1. AI 智能助手

- **自然语言交互**: 支持自然语言查询和操作业务数据
- **智能工具调用**: Agent 自动识别并调用所需工具
- **Skill 技能系统**: 可扩展的技能插件机制
- **多 Agent 支持**: 支持不同业务场景的专属 Agent

<!-- 插入AI助手界面截图 -->
<!-- ![AI 智能助手](docs/images/ai-chat.png) -->

### 2. 销售管理

- 销售订单创建、编辑、确认
- 订单状态跟踪
- 销售数据统计

### 3. 采购管理

- 采购订单全流程管理
- 供应商管理
- 采购报表统计

### 4. 财务管理

- 应收款管理
- 收款记录追踪
- 财务报表查看

<!-- 插入财务管理界面截图 -->
<!-- ![财务管理](docs/images/finance.png) -->

### 5. 库存管理

- 库��查看与管理
- 库存盘点
- 调拨管理
- 仓库管理

### 6. 客户关系管理 (CRM)

- 客户信息管理
- 客户跟进记录
- 客户分类管理

<!-- 插入CRM界面截图 -->
<!-- ![客户管理](docs/images/crm.png) -->

### 7. 商品管理

- 商品信息维护
- 商品分类
- 价格管理

### 8. 权限管理系统

- 基于 RBAC 的权限控制
- 角色管理
- 细粒度权限分配

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3)                          │
│                  Vue Router + TypeScript                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                     (FastAPI + CORS)                         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Agent 模块   │   │  业务服务模块  │   │  认证服务模块  │
│  (LangChain)  │   │               │   │   (JWT)       │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│              MongoDB (主数据库) + Redis (缓存)               │
└─────────────────────────────────────────────────────────────┘
```

### 后端技术栈

| 技术 | 说明 |
|------|------|
| FastAPI | 高性能 Python Web 框架 |
| Motor | MongoDB 异步驱动 |
| Redis | 缓存与会话存储 |
| Pydantic | 数据验证与序列化 |
| LangChain | AI Agent 开发框架 |
| python-jose | JWT 认证 |
| passlib | 密码加密 |

### 前端技术栈

| 技术 | 说明 |
|------|------|
| Vue 3 | 渐进式 JavaScript 框架 |
| Vue Router 5 | 官方路由管理器 |
| TypeScript | 类型安全 JavaScript |
| Vite | 下一代前端构建工具 |

---

## 系统界面

### 登录页面

<!-- 插入登录页面截图 -->
<!-- ![登录页面](docs/images/login.png) -->

### 工作台

<!-- 插入工作台截图 -->
<!-- ![工作台](docs/images/dashboard.png) -->

### 销售订单

<!-- 插入销售订单截图 -->
<!-- ![销售订单](docs/images/sales-order.png) -->

### AI 智能助手

<!-- 插入AI助手截图 -->
<!-- ![AI助手](docs/images/ai-chat.png) -->

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MongoDB 4.4+
- Redis 6+

### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制并配置环境变量
copy .env.example .env

# 启动服务
python main.py
```

### 前端启动

```bash
# 进入前端目录
cd web

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问系统

- 前端地址: http://localhost:5174
- 后端地址: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 默认账号

```
用户名: admin
密码: admin123
```

---

## 项目结构

```
ai_mdr_platform/
├── backend/
│   ├── app/
│   │   ├── agent/              # AI Agent 模块
│   │   │   ├── llm/            # LLM 客户端
│   │   │   ├── skills/         # 技能系统
│   │   │   ├── tools/          # 工具注册
│   │   │   ├── agent.py        # Agent 核心类
│   │   │   ├── config.py       # Agent 配置
│   │   │   └── manager.py      # Agent 管理器
│   │   ├── routers/            # API 路由
│   │   │   ├── ai.py           # AI 相关路由
│   │   │   ├── auth.py         # 认证路由
│   │   │   ├── customer.py     # 客户路由
│   │   │   ├── product.py      # 商品路由
│   │   │   ├── sales_order.py  # 销售路由
│   │   │   ├── procurement.py  # 采购路由
│   │   │   ├── inventory.py    # 库存路由
│   │   │   ├── accounts_receivable.py  # 应收款路由
│   │   │   └── ...
│   │   ├── services/           # 业务服务层
│   │   ├── models/             # 数据模型
│   │   ├── database.py         # 数据库连接
│   │   └── middleware.py       # 中间件
│   ├── config/
│   │   └── settings.py         # 配置管理
│   ├── main.py                 # 应用入口
│   └── requirements.txt        # Python 依赖
│
├── web/
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   │   ├── workspace/      # 业务工作区组件
│   │   │   ├── DashboardLayout.vue   # 布局组件
│   │   │   ├── LoginView.vue        # 登录页面
│   │   │   └── ...
│   │   ├── router/              # 路由配置
│   │   ├── services/           # API 服务
│   │   ├── hooks/              # 组合式函数
│   │   ├── styles/             # 全局样式
│   │   ├── App.vue             # 根组件
│   │   └── main.ts             # 入口文件
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

---

## API文档

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/register | 用户注册 |
| GET | /api/v1/auth/me | 获取当前用户 |

### AI 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/ai/chat | 发送聊天消息 |
| GET | /api/v1/ai/agents | 获取 Agent 列表 |
| GET | /api/v1/ai/tools | 获取工具列表 |
| GET | /api/v1/ai/skills | 获取技能列表 |

### 业务接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | /api/v1/customers | 客户管理 |
| GET/POST | /api/v1/products | 商品管理 |
| GET/POST | /api/v1/sales-orders | 销售订单 |
| GET/POST | /api/v1/procurement-orders | 采购订单 |
| GET/POST | /api/v1/inventory | 库存管理 |
| GET/POST | /api/v1/accounts-receivable | 应收款管理 |

详细 API 文档请访问: http://localhost:8000/docs

---

## 部署指南

### Docker 部署

```bash
# 构建后端镜像
docker build -t ai-mdr-backend ./backend

# 运行后端容器
docker run -p 8000:8000 --env-file ./backend/.env ai-mdr-backend

# 前端构建
cd web && npm run build
```

### Kubernetes 部署

项目支持在 Linux K8s 环境下部署，请参考 `deploy/k8s/` 目录下的配置文件。

### 生产环境配置

```bash
# 设置生产环境变量
APP_ENV=production
DEBUG=false
SECRET_KEY=your-production-secret-key
MONGODB_URL=mongodb://your-mongo-host:27017
REDIS_URL=redis://your-redis-host:6379/0
```

---

## 开发指南

### 代码规范

1. **Python 代码规范**
   - 使用 Black 格式化代码
   - 使用 isort 管理导入
   - 单函数不超过 20 条语句

2. **TypeScript 代码规范**
   - 使用 Vue 3 Composition API
   - 使用 TypeScript 严格模式
   - 组件文件使用 PascalCase

### 模块开发

#### 添加新的业务模块

1. **后端**
   - 在 `models/` 添加数据模型
   - 在 `services/` 添加业务服务
   - 在 `routers/` 添加 API 路由

2. **前端**
   - 在 `components/workspace/` 添加工作区组件
   - 在 `router/index.ts` 添加路由
   - 在 `services/api.ts` 添加 API 调用

#### 添加 Agent 工具

1. 在 `app/agent/tools/` 创建工具类
2. 继承 `BaseTool` 基类
3. 实现 `execute` 方法
4. 在 `tool_registry.py` 注册工具

#### 添加 Agent 技能

1. 在 `app/agent/skills/` 创建技能类
2. 继承 `BaseSkill` 基类
3. 实现技能逻辑
4. 在数据库中创建技能配置

---

## License

MIT License
