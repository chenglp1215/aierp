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
│       ├── 各模块py文件
│       └── api_docs/        # API 文档
│           ├── README.md        # 项目总文档
│           ├── 各模块文档md文件
├── config/settings.py       # Pydantic Settings 配置
├── models/                  # Pydantic 数据模型
├── services/                # 业务逻辑服务
├── scripts/                 # 脚本文件
├── main.py                  # 入口点
└── requirements.txt         # 依赖
```

## API 接口文档

详细接口文档位于: [app/routers/api\_docs/README.md](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/README.md)

模块化文档:

- [客户管理 v2](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/customer_v2.md)
- [省份城市数据](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/province_city.md)
- [商品分类管理](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/category.md)
- [品牌管理](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/brand.md)
- [商品管理](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/product.md)

## 统一响应格式

### HTTP 状态码规范

| 状态码 | 说明       |
| --- | -------- |
| 200 | 请求成功     |
| 401 | 未认证或认证失效 |
| 5XX | 服务器内部错误  |

### 成功响应格式 (200)

#### list 列表响应

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": "64a1b2c3d4e5f6a7b8c9d0e1",
        "customer_code": "C2024010001",
        "name": "某医院检验科",
        "customer_type": "terminal",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "status": "normal",
        "sales_user_name": "李经理",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### detail 详情响应

```json
{
  "status": "success",
  "message": "操作成功",
  "result": {
    "id": "64a1b2c3d4e5f6a7b8c9d0e1",
    "customer_code": "C2024010001",
    "name": "某医院检验科",
    "customer_type": "terminal",
    "contact_person": "张三",
    "contact_phone": "13800138000",
    "status": "normal",
    "sales_user_name": "李经理",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 错误响应格式 (200)

#### 通用错误格式

```json
{
  "status": "error",
  "message": "错误描述信息",
  "result": null
}
```

#### 数据校验错误格式

当数据校验失败时（如参数验证），返回格式如下：

```json
{
  "status": "error",
  "message": "客户更新参数验证失败",
  "validation_errors": [
    {
      "field": "name",
      "message": "客户名称不能为空"
    },
    {
      "field": "contact_info.contact_phone",
      "message": "手机号格式不正确"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 固定为 `error` |
| message | string | 错误描述信息 |
| validation_errors | array | 校验错误列表 |
| validation_errors[].field | string | 错误字段路径 |
| validation_errors[].message | string | 字段错误描述 |

### 响应字段说明

| 字段                | 类型                | 说明                  |
| ----------------- | ----------------- | ------------------- |
| status            | string            | `success` 或 `error` |
| message           | string            | 操作结果的描述信息           |
| result            | object/array/null | 返回数据，失败时为 null      |
| result.total      | int               | 列表总记录数（仅列表接口）       |
| result.page       | int               | 当前页码（仅列表接口）         |
| result.page\_size | int               | 每页记录数（仅列表接口）        |
| result.items      | array             | 数据列表（仅列表接口）         |

### 无返回值的操作

对于删除等无返回值的操作：

```json
{
  "status": "success",
  "message": "删除成功",
  "result": null
}
```

## 编码约定

| 类型 | 规范     | 示例               |
| -- | ------ | ---------------- |
| 文件 | 小写下划线  | `database.py`    |
| 类  | 大驼峰    | `Database`       |
| 函数 | 小写下划线  | `get_user_by_id` |
| 常量 | 全大写下划线 | `SECRET_KEY`     |

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

- **后续每次更新后端接口和数据结构，必须同步排查并调整** **`API_DOCUMENTATION.md`** **接口文档**
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

| 字段          | 类型   | 说明             |
| ----------- | ---- | -------------- |
| id          | str  | 分类ID (自动生成)    |
| name        | str  | 分类名称           |
| tax\_code   | str  | 税务编码           |
| parent\_id  | str  | 父分类ID (顶级分类为空) |
| level       | int  | 分类层级 (1/2/3)   |
| sort\_order | int  | 排序权重           |
| is\_active  | bool | 是否有效           |

### API 端点

| 路径                                        | 方法     | 说明       |
| ----------------------------------------- | ------ | -------- |
| /product-categories/                      | POST   | 创建分类     |
| /product-categories/                      | GET    | 列表查询(平铺) |
| /product-categories/tree                  | GET    | 树形结构     |
| /product-categories/parent-options        | GET    | 可选父分类    |
| /product-categories/children/{parent\_id} | GET    | 子分类列表    |
| /product-categories/{id}                  | GET    | 分类详情     |
| /product-categories/{id}                  | PUT    | 更新分类     |
| /product-categories/{id}                  | DELETE | 删除分类     |

### 前端页面

- ProductWorkspace.vue 改为包含子页签的容器组件
  - 子页签1: 商品分类 (ProductCategoryWorkspace.vue) - 三级树形视图+列表视图
  - 子页签2: 商品管理 (ProductManageContent.vue) - 原 ProductWorkspace 内容

### 核心文件

| 文件                                                        | 说明                      |
| --------------------------------------------------------- | ----------------------- |
| backend/models/product\_category.py                       | Pydantic 数据模型           |
| backend/services/product\_category\_service.py            | 业务逻辑服务                  |
| backend/app/routers/product.py                            | 分类路由 (category\_router) |
| web/src/services/api.ts                                   | productCategoryApi      |
| web/src/components/workspace/ProductCategoryWorkspace.vue | 分类管理页面                  |
| web/src/components/workspace/ProductManageContent.vue     | 商品管理内容                  |
| web/src/components/workspace/ProductWorkspace.vue         | 页签容器                    |

## 最近变更记录

| 日期         | 变更内容                                                                        |
| ---------- | --------------------------------------------------------------------------- |
| 2026-05-01 | **客户折扣管理模块**：新增客户折扣设置功能，包含客户折扣表（客户ID、品牌ID、折扣值、是否生效）及完整CRUD接口 |
| 2026-05-01 | **客户管理API规范化**：移除HTTPException、统一错误响应格式、新增handle_result装饰器 |
| 2026-05-01 | **客户管理销售人调整**：新建/编辑客户时自动设置为当前鉴权人，前端移除销售人选择框                   |
| 2026-05-01 | **商品管理API文档**：新增完整商品管理接口文档 [product.md](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/product.md)，包含商品和规格的16个接口 |
| 2026-05-01 | **商品分类API规范化**：统一响应格式(status/message/result)、移除HTTPException、改用错误响应字典 |
| 2026-05-01 | **商品分类API文档**：新增完整商品分类管理接口文档 [category.md](file:///d:/project/aierp/aierp/backend/app/routers/api_docs/category.md) |
| 2026-05-01 | **API 接口规范更新**：统一响应格式(status/message/result)、HTTP状态码规范(200/401/5XX)、模块化文档拆分 |
| 2026-04-29 | **商品分类模块**：新增三级分类管理(后端+前端)                                                  |
| 2026-04-28 | **API 接口文档**：整理所有后端接口为标准文档                                                  |
| 2026-04-28 | **文档同步规范**：接口/数据结构变更需同步更新接口文档                                               |
| 2026-04-28 | **前端列表操作优化**：编辑/删除直接更新本地列表                                                  |
| 2026-04-28 | **仓库编辑接口修复**：按 warehouse\_code 而非 \_id 更新                                   |
| 2026-04-21 | **Agent Tools 业务模块封装**：销售订单、客户、库存模块                                         |
| 2026-04-21 | **Agent 权限过滤机制**：基于用户权限动态加载 Tools                                           |
| 2026-04-21 | **React 模式工具调用**：流式输出、工具调用状态通知                                              |

## 前端列表操作优化模式

### 核心原则

| 操作    | 处理方式                         |
| ----- | ---------------------------- |
| 编辑/更新 | 直接更新列表对应项 (findIndex + 直接赋值) |
| 删除    | 从列表 filter 移除                |
| 新建    | 调用 loadXxx() 刷新 (需获取后端 id)   |
| 状态切换  | 直接更新本地项状态                    |

### 关键教训

1. 编辑成功后不要重新加载整个列表
2. 删除成功后用 `filter` 移除
3. 新建操作仍需刷新获取后端生成的 id
4. 使用 Toast 替代 alert()

## 权限系统设计

### 权限类型

| 类型     | 说明            |
| ------ | ------------- |
| menu   | 菜单权限，控制侧边栏显示  |
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

| 菜单ID        | 权限代码          |
| ----------- | ------------- |
| sales-order | order.view    |
| crm         | customer.menu |
| system-user | user.menu     |

### 按钮权限映射

| 操作ID   | 权限代码   |
| ------ | ------ |
| create | create |
| edit   | edit   |
| delete | delete |

### 注意事项

1. admin 角色拥有所有权限
2. 权限代码命名: `模块.资源.操作` (如 `sales.order.create`)

## Agent Tools 设计

### 概述

系统将业务功能封装为 Agent 可调用的 Tools，支持基于用户权限的动态加载。

### Tool 模块

| 模块   | Tools                                                            |
| ---- | ---------------------------------------------------------------- |
| 销售订单 | sales\_order\_search, sales\_order\_create, sales\_order\_update |
| 客户管理 | customer\_search, customer\_create, customer\_update             |
| 库存管理 | stock\_search, stock\_adjust, warehouse\_search                  |

### 设计原则

1. 参数尽量使用可选参数，减少 prompt 长度
2. description 使用中文描述
3. 通过 `permission_code` 关联权限，无权限时 Tool 不暴露给 AI

## React 模式工具调用

### WebSocket 消息类型

| 类型                | 说明      |
| ----------------- | ------- |
| text              | AI 文本回复 |
| tool\_call\_start | 工具开始调用  |
| tool\_call\_end   | 工具调用结束  |
| error             | 错误信息    |

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

## VxeTable4 前端表格实现规范

### 概述

项目前端使用 VxeTable4 作为通用表格组件，适用于产品管理、客户管理、订单管理等列表页面。

### 核心文件

| 文件                                                  | 说明           |
| --------------------------------------------------- | ------------ |
| web/src/components/workspace/ProductWorkspace.vue   | 产品管理页面（完整示例） |
| web/src/components/workspace/SalesOrderList.vue     | 销售订单列表       |
| web/src/components/workspace/InventoryWorkspace.vue | 库存管理页面       |

### 垂直表格数据构建（产品-规格展开模式）

当一个产品有多个规格时，需要将数据转换为垂直展开格式：

```typescript
interface ProductGroup {
  product: Product
  rowspan: number
}

const buildVerticalTableData = () => {
  const data: any[] = []
  for (const group of productGroups.value) {
    const specs = group.product.specs || []
    for (let i = 0; i < specs.length; i++) {
      const spec = specs[i]
      data.push({
        _id: `${group.product.id}_${spec.id}`,
        product_id: group.product.id,
        product_code: group.product.product_code,
        product_name: group.product.name,
        isFirst: i === 0,
        rowspan: i === 0 ? specs.length : 0,
        product_rowspan: i === 0 ? specs.length : 0,
        specs_length: specs.length
      })
    }
  }
  verticalTableData.value = data
}
```

### 合并单元格规则 (span-method)

```typescript
type SpanMethod = (params: { row: any; columnIndex: number }) => { rowspan: number; colspan: number } | void

const verticalSpanMethod: SpanMethod = ({ row, columnIndex }) => {
  const productCols = [0, 1, 2, 3, 4, 5]  // 需要合并的产品列
  const actionCol = 12  // 操作列索引
  
  if (productCols.includes(columnIndex) && row.isFirst) {
    return { rowspan: row.rowspan, colspan: 1 }
  }
  if (productCols.includes(columnIndex) || (columnIndex === actionCol && !row.isFirst)) {
    return { rowspan: 0, colspan: 0 }
  }
  if (columnIndex === actionCol && row.isFirst) {
    return { rowspan: row.rowspan, colspan: 1 }
  }
}
```

### 序号方法 (seq-method)

处理分页时序号连续性：

```typescript
const seqMethod = ({ row }: { row: any }) => {
  if (!row.isFirst) return 0
  const firstRows = verticalTableData.value.filter(r => r.isFirst)
  return firstRows.findIndex(r => r._id === row._id) + 1 + (page.value - 1) * pageSize.value
}
```

### 基础模板结构

```vue
<vxe-table
  :data="verticalTableData"
  :column-config="{ resizable: true }"
  :span-method="verticalSpanMethod"
  :seq-config="{ seqMethod: seqMethod }"
>
  <vxe-column type="seq" title="序号" width="60" fixed="left" class-name="col--center" />
  <vxe-column field="product_code" title="产品编号" width="130" class-name="col--center" />
  <!-- 更多列 -->
  <vxe-column title="操作" width="220" fixed="right" class-name="col--center">
    <template #default="{ row }">
      <span class="action-btns">
        <button class="btn-link" @click="openEditProduct(row)">编辑</button>
        <button class="btn-link danger" @click="confirmDeleteProduct(row)">删除</button>
      </span>
    </template>
  </vxe-column>
</vxe-table>

<vxe-pager
  v-model:current-page="page"
  v-model:page-size="pageSize"
  :total="total"
  :layouts="['PrevPage', 'JumpNumber', 'NextPage', 'FullJump', 'Sizes', 'Total']"
  @page-change="handlePageChange"
/>
```

### 分页处理

```typescript
const handlePageChange = ({ currentPage, pageSize: newPageSize }: { currentPage: number; pageSize: number }) => {
  page.value = currentPage
  pageSize.value = newPageSize
  loadProducts()
}
```

### 样式定制

全局样式（在组件 `<style>` 标签外）：

```css
.vxe-table {
  font-size: 13px;
  color: var(--text-primary);
}

.vxe-table .vxe-body--row {
  height: 48px;
}

.vxe-table .vxe-body--column.col--center {
  text-align: center;
  justify-content: center;
}

.vxe-pager {
  margin-top: 16px;
  background-color: var(--bg-card) !important;
  border-top: 1px solid var(--border-color);
}

.vxe-pager .vxe-pager--num-btn.is--active {
  background-color: var(--accent-blue) !important;
  color: white !important;
}
```

### 主题适配

```css
[data-theme="light"] .vxe-pager {
  background-color: #ffffff !important;
  border-top: 1px solid #e5e7eb;
}

[data-theme="light"] .vxe-pager .vxe-pager--num-btn.is--active {
  color: #ffffff !important;
}
```

### 操作列按钮样式

```css
.action-btns {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-link {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn-link:hover {
  background-color: rgba(0, 120, 212, 0.1);
}

.btn-link.danger {
  color: var(--accent-red);
}

.btn-link.danger:hover {
  background-color: rgba(239, 68, 68, 0.1);
}
```

### 状态标签

```vue
<vxe-column field="spec_is_active" title="规格有效" width="80" class-name="col--center">
  <template #default="{ row }">
    <span :class="['active-tag', row.spec_is_active ? 'active' : '']">
      {{ row.spec_is_active ? '在售' : '停用' }}
    </span>
  </template>
</vxe-column>
```

```css
.active-tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
}

.active-tag.active {
  background-color: rgba(16, 185, 129, 0.1);
  color: var(--accent-green);
}
```

### 加载状态覆盖层

```vue
<div class="table-section" style="position: relative;">
  <div v-if="loading" class="table-loading-overlay">
    <div class="table-loading-content">加载中...</div>
  </div>
  <vxe-table :data="verticalTableData" ...>
    <!-- ... -->
  </vxe-table>
</div>
```

```css
.table-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

[data-theme="dark"] .table-loading-overlay {
  background-color: rgba(0, 0, 0, 0.8);
}
```

