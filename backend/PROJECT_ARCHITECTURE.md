# AI MDR Platform Backend - 项目架构文档

## 项目概述

### 项目简介
AI MDR Platform Backend 是一个基于 FastAPI 的高性能异步 API 服务，为 AI MDR 平台提供后端支持，支持 MongoDB 和 Redis 数据存储。

### 技术栈
- **框架**: FastAPI 0.115.0 (异步)
- **数据库**: MongoDB (Motor 异步驱动)
- **缓存**: Redis (asyncio 版本)
- **数据验证**: Pydantic V2
- **认证**: JWT (python-jose)

## 目录结构

```
backend/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── database.py          # MongoDB + Redis 连接
│   ├── middleware.py        # 中间件 (JWT认证)
│   └── routers/             # 路由模块
├── config/settings.py       # Pydantic Settings 配置
├── models/                  # Pydantic 数据模型
├── services/                # 业务逻辑服务
├── scripts/                 # 脚本文件
├── main.py                  # 入口点
├── API_DOCUMENTATION.md     # API 接口文档
└── requirements.txt         # 依赖
```

## API 接口文档

详细接口文档: [API_DOCUMENTATION.md](file:///e:/wechat-bot-dev/ai_mdr_platform/backend/API_DOCUMENTATION.md)

## 统一响应格式

```json
{
  "status": "success|error",
  "message": "描述信息",
  "result": {}
}
```

分页响应:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": []
}
```

## 编码约定

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件 | 小写下划线 | `database.py` |
| 类 | 大驼峰 | `Database` |
| 函数 | 小写下划线 | `get_user_by_id` |
| 常量 | 全大写下划线 | `SECRET_KEY` |

- 单函数不超过 20 条语句
- 使用中文注释
- 使用 Pydantic 模型定义数据结构

## 开发规范

### 代码风格
- Black 格式化代码
- isort 管理导入顺序
- flake8 检查代码质量

### 测试规范
- pytest + pytest-asyncio
- 测试文件放在 `tests/` 目录

### 文档同步规范
- **后续每次更新后端接口和数据结构，必须同步排查并调整 `API_DOCUMENTATION.md` 接口文档**
- 新增接口: 添加完整的请求/响应格式说明
- 修改接口: 同步更新参数、响应或权限说明
- 删除接口: 从文档中移除或标注废弃
- 变更数据结构: 检查并更新相关接口格式

## 快速启动

```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env

# 4. 启动服务
python main.py

# 访问 API 文档: http://localhost:8000/docs
```

## 商品分类模块

### 数据结构
商品分类支持三级分类树，存储在 MongoDB `product_categories` 集合中。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str | 分类ID (自动生成) |
| name | str | 分类名称 |
| tax_code | str | 税务编码 |
| parent_id | str | 父分类ID (顶级分类为空) |
| level | int | 分类层级 (1/2/3) |
| sort_order | int | 排序权重 |
| is_active | bool | 是否有效 |

### API 端点
| 路径 | 方法 | 说明 |
|------|------|------|
| /product-categories/ | POST | 创建分类 |
| /product-categories/ | GET | 列表查询(平铺) |
| /product-categories/tree | GET | 树形结构 |
| /product-categories/parent-options | GET | 可选父分类 |
| /product-categories/children/{parent_id} | GET | 子分类列表 |
| /product-categories/{id} | GET | 分类详情 |
| /product-categories/{id} | PUT | 更新分类 |
| /product-categories/{id} | DELETE | 删除分类 |

### 前端页面
- ProductWorkspace.vue 改为包含子页签的容器组件
  - 子页签1: 商品分类 (ProductCategoryWorkspace.vue) - 三级树形视图+列表视图
  - 子页签2: 商品管理 (ProductManageContent.vue) - 原 ProductWorkspace 内容

### 核心文件
| 文件 | 说明 |
|------|------|
| backend/models/product_category.py | Pydantic 数据模型 |
| backend/services/product_category_service.py | 业务逻辑服务 |
| backend/app/routers/product.py | 分类路由 (category_router) |
| web/src/services/api.ts | productCategoryApi |
| web/src/components/workspace/ProductCategoryWorkspace.vue | 分类管理页面 |
| web/src/components/workspace/ProductManageContent.vue | 商品管理内容 |
| web/src/components/workspace/ProductWorkspace.vue | 页签容器 |

## 最近变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-04-29 | **商品分类模块**：新增三级分类管理(后端+前端) |
| 2026-04-28 | **API 接口文档**：整理所有后端接口为标准文档 |
| 2026-04-28 | **文档同步规范**：接口/数据结构变更需同步更新接口文档 |
| 2026-04-28 | **前端列表操作优化**：编辑/删除直接更新本地列表 |
| 2026-04-28 | **仓库编辑接口修复**：按 warehouse_code 而非 _id 更新 |
| 2026-04-21 | **Agent Tools 业务模块封装**：销售订单、客户、库存模块 |
| 2026-04-21 | **Agent 权限过滤机制**：基于用户权限动态加载 Tools |
| 2026-04-21 | **React 模式工具调用**：流式输出、工具调用状态通知 |

## 前端列表操作优化模式

### 核心原则
| 操作 | 处理方式 |
|------|----------|
| 编辑/更新 | 直接更新列表对应项 (findIndex + 直接赋值) |
| 删除 | 从列表 filter 移除 |
| 新建 | 调用 loadXxx() 刷新 (需获取后端 id) |
| 状态切换 | 直接更新本地项状态 |

### 关键教训
1. 编辑成功后不要重新加载整个列表
2. 删除成功后用 `filter` 移除
3. 新建操作仍需刷新获取后端生成的 id
4. 使用 Toast 替代 alert()

## 权限系统设计

### 权限类型
| 类型 | 说明 |
|------|------|
| menu | 菜单权限，控制侧边栏显示 |
| button | 按钮权限，控制操作按钮显示 |

### 核心文件
`web/src/hooks/usePermission.ts` - 权限 hook 和映射表

### 使用方式
```typescript
const { hasPermission } = usePermission()
if (hasPermission('user.create')) { /* ... */ }
```

```vue
<button v-permission="'user.create'">新建</button>
```

### 菜单权限映射
| 菜单ID | 权限代码 |
|--------|----------|
| sales-order | order.view |
| crm | customer.menu |
| system-user | user.menu |

### 按钮权限映射
| 操作ID | 权限代码 |
|--------|----------|
| create | create |
| edit | edit |
| delete | delete |

### 注意事项
1. admin 角色拥有所有权限
2. 权限代码命名: `模块.资源.操作` (如 `sales.order.create`)

## Agent Tools 设计

### 概述
系统将业务功能封装为 Agent 可调用的 Tools，支持基于用户权限的动态加载。

### Tool 模块
| 模块 | Tools |
|------|-------|
| 销售订单 | sales_order_search, sales_order_create, sales_order_update |
| 客户管理 | customer_search, customer_create, customer_update |
| 库存管理 | stock_search, stock_adjust, warehouse_search |

### 设计原则
1. 参数尽量使用可选参数，减少 prompt 长度
2. description 使用中文描述
3. 通过 `permission_code` 关联权限，无权限时 Tool 不暴露给 AI

## React 模式工具调用

### WebSocket 消息类型
| 类型 | 说明 |
|------|------|
| text | AI 文本回复 |
| tool_call_start | 工具开始调用 |
| tool_call_end | 工具调用结束 |
| error | 错误信息 |

### 核心流程
```
用户消息 → AI 生成文本(流式) → AI 决定调用工具 → 执行工具 → 返回结果 → 继续生成
```

### 前端集成
```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  switch (data.type) {
    case 'text': appendToChat(data.content); break;
    case 'tool_call_start': showToolCalling(data.tool); break;
    case 'tool_call_end': showToolResult(data.tool, data.success); break;
  }
};
```

## 开发经验总结

### 问题1: 登录/登出功能无法正常工作

#### 根因
1. Vue 路由缺少 `<router-view>` 导致路由切换无效
2. 退出登录只清除 `token`/`user`，没有清除 `token_expires_at`
3. AuthMiddleware 未注册

#### 正确做法
```typescript
// 退出登录必须清除所有认证数据
const keysToRemove = ['token', 'user', 'token_expires_at']
keysToRemove.forEach(key => localStorage.removeItem(key))
window.location.replace('/login')
```

### 问题2: Agent Tool Schema 格式错误

#### 根因
`BaseTool.get_schema()` 返回格式不符合 OpenAI Function Calling 规范

#### 正确格式
```python
{
    "type": "function",
    "function": {
        "name": self.name,
        "description": self.description,
        "parameters": self.parameters
    }
}
```

### 关键教训
1. Vue SPA 必须有 `<router-view>` 作为路由出口
2. localStorage 认证数据要全部清除
3. 后端中间件必须注册才会生效
4. 集成外部 API 时必须严格遵循其规范
