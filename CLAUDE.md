# AIERP 项目文档

## 项目概述

AIERP 是一个企业资源计划（ERP）系统，包含后端（Python/FastAPI）和前端（Vue 3）。

### 技术栈

- **后端**: Python, FastAPI, SQLAlchemy
- **前端**: Vue 3, TypeScript, Vite, Vue Router, Pinia
- **数据库**: 需查看 requirements.txt 确认

## 可用的插件技能

以下技能安装在 `C:\Users\chenglp\.claude\plugins\`，当涉及对应场景时，应加载并参考对应的 `.md` 文件。

### Vue 前端开发（项目核心）

| 技能 | 路径 | 触发场景 |
|------|------|---------|
| **vue-best-practices** | `C:\Users\chenglp\.claude\plugins\vue-best-practices\agents\vue-best-practices.md` | 所有 Vue.js 任务，Composition API + `<script setup>` + TypeScript |
| **vue-router-best-practices** | `C:\Users\chenglp\.claude\plugins\vue-router-best-practices\agents\vue-router-best-practices.md` | Vue Router 导航守卫、路由参数、路由生命周期 |
| **vue-pinia-best-practices** | `C:\Users\chenglp\.claude\plugins\vue-pinia-best-practices\agents\vue-pinia-best-practices.md` | Pinia 状态管理、Store 设置、响应式 |
| **vue-debug-guides** | `C:\Users\chenglp\.claude\plugins\vue-debug-guides\agents\vue-debug-guides.md` | Vue 3 调试、运行时错误、响应式问题、SSR/hydration |
| **vue-testing-best-practices** | `C:\Users\chenglp\.claude\plugins\vue-testing-best-practices\agents\vue-testing-best-practices.md` | Vue.js 测试（Vitest, Vue Test Utils, Playwright E2E） |
| **vue-jsx-best-practices** | `C:\Users\chenglp\.claude\plugins\vue-jsx-best-practices\agents\vue-jsx-best-practices.md` | Vue JSX 语法、React JSX 迁移 |
| **vue-options-api-best-practices** | `C:\Users\chenglp\.claude\plugins\vue-options-api-best-practices\agents\vue-options-api-best-practices.md` | Vue 3 Options API 风格（当项目明确使用时） |

### 代码审查与架构

| 技能 | 路径 | 触发场景 |
|------|------|---------|
| **mdr-code-review** | `C:\Users\chenglp\.claude\plugins\mdr-code-review\agents\mdr-code-review.md` | 代码审查、Bug 修复、新功能开发、代码重构、架构文档维护 |
| **update-docs** | `C:\Users\chenglp\.claude\plugins\update-docs\agents\update-docs.md` | 更新文档、PR 文档检查 |
| **frontend-design** | `C:\Users\chenglp\.claude\plugins\frontend-design\agents\frontend-design.md` | 前端界面设计、组件构建、UI 美化 |

### 数据处理

| 技能 | 路径 | 触发场景 |
|------|------|---------|
| **excel-data-compare** | `C:\Users\chenglp\.claude\plugins\excel-data-compare\agents\excel-data-compare.md` | Excel 数据对比、数量核对、差异报告 |
| **minimax-xlsx** | `C:\Users\chenglp\.claude\plugins\minimax-xlsx\agents\minimax-xlsx.md` | Excel 文件创建、编辑、分析、格式化 |
| **minimax-docx** | `C:\Users\chenglp\.claude\plugins\minimax-docx\agents\minimax-docx.md` | Word 文档创建、编辑、格式化 |
| **minimax-pdf** | `C:\Users\chenglp\.claude\plugins\minimax-pdf\agents\minimax-pdf.md` | PDF 文档创建、填写、重新格式化 |

### 工具与其他

| 技能 | 路径 | 触发场景 |
|------|------|---------|
| **auto-timewise** | `C:\Users\chenglp\.claude\plugins\auto-timewise\agents\auto-timewise.md` | Jira Timewise 自动工时填报 |
| **skill-creator** | `C:\Users\chenglp\.claude\plugins\skill-creator\agents\skill-creator.md` | 创建/修改/优化技能 |
| **self-improving-agent** | `C:\Users\chenglp\.claude\plugins\self-improving-agent-3.0.6\agents\self-improving-agent-3.0.6.md` | 捕获学习内容、错误纠正、持续改进 |
| **工具生成技能** | `C:\Users\chenglp\.claude\plugins\工具生成技能-tools-build-skill\agents\工具生成技能-tools-build-skill.md` | 生成/修改内置工具 |

## 目录结构

```
aierp/
├── .project_docs/         # 项目文档目录（按需拆分前端/后端）
│   ├── backend/
│   │   ├── 项目基础规范.md    # 架构、代码风格、接口规范、视图实现、模块拆分
│   │   ├── 项目模块说明.md    # 各业务模块的功能说明
│   │   └── 项目业务说明.md    # 业务流转、业务注意事项
│   └── frontend/
│       ├── 项目基础规范.md    # 架构、组件规范、路由规范
│       ├── 项目模块说明.md    # 各业务模块的功能说明
│       └── 项目业务说明.md    # 业务流转、业务注意事项
├── backend/               # 后端服务
│   ├── app/               # FastAPI 应用
│   │   └── routers/       # API 路由
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   └── validators/        # 数据校验
├── web/                   # 前端项目
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   │   └── workspace/ # 工作区组件
│   │   ├── services/      # API 服务
│   │   └── ...
│   └── ...
└── CLAUDE.md              # 本文件
```

### 项目文档说明

项目文档统一存放在 `.project_docs/` 目录下，按前端和后端拆分：

| 文档 | 内容 | 更新规则 |
|------|------|---------|
| **项目基础规范** | 架构、代码风格、接口规范（含编写例子）、实现风格（含例子）、模块文件拆分和解耦定位 | 需用户同意后才可修改 |
| **项目模块说明** | 各业务模块的功能说明、API 列表、组件列表 | 随开发实时更新，可自动更新 |
| **项目业务说明** | 业务流转说明、业务注意事项、业务约束和规则 | 随业务调整实时更新，可自动更新 |

技能加载时，根据任务类型按需读取对应文档，不一次性读取所有文档。

插件技能安装在: `C:\Users\chenglp\.claude\plugins\`

## 如何使用插件技能

当需要使用某个技能时，读取对应的 `.md` 文件获取指导。所有插件均安装在 `C:\Users\chenglp\.claude\plugins\` 下。

部分插件还包含 `references/` 目录，提供更详细的参考文档，可根据需要加载。

## 编码规范

### 后端

- 文件名: 小写下划线 (`event_services.py`)
- 类名: 大驼峰 (`EventDocument`)
- 函数名: 小写下划线 (`get_block_log_list`)
- 常量: 全大写下划线 (`BLOCK_STATUS_CHOICES`)
- 单函数不超过 20 条语句
- 使用中文注释
- 统一响应格式: `{status, message, result, exc}`

### 前端

- 使用 Vue 3 Composition API + `<script setup lang="ts">`
- 组件按功能拆分，避免"超级组件"
- Props down, Events up
- 状态最小化，衍生数据用 computed
