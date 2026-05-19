## Why

AI 智能配置模块目前使用 MongoDB 存储，与项目其他已迁移到 MySQL 的核心业务模块（客户、产品、订单、采购、供应商等）数据存储方式不一致。统一到 MySQL 可以：

1. **数据一致性**：所有业务数据在同一数据库，便于跨模块查询和事务管理
2. **运维简化**：减少数据库维护成本，统一备份和监控策略
3. **ORM 统一**：使用 Tortoise ORM 提供更好的类型安全和关系管理

## What Changes

### 后端变更

- **新增 MySQL ORM 模型**：`models_mysql/ai.py`，包含 6 个模型
  - `LlmModel` - LLM 模型配置
  - `LlmConfig` - LLM 全局配置（单例）
  - `KnowledgeBase` - 知识库
  - `McpServer` - MCP 服务器
  - `Skill` - 技能配置
  - `Agent` - Agent 配置

- **新增 MySQL 服务层**：`services/ai_service_mysql.py`
  - 替换 MongoDB BaseService 继承为 Tortoise ORM 操作
  - ID 类型从字符串 ObjectId 改为整数

- **更新路由**：`app/routers/ai.py`
  - 适配整数 ID 参数
  - 调用 MySQL 服务层

- **新增数据迁移脚本**：`scripts/migrate_ai_config_to_mysql.py`
  - 迁移 MongoDB 数据到 MySQL
  - 处理 ObjectId 到整数 ID 的转换

### 前端变更

- **更新 API 类型定义**：`services/api.ts`
  - ID 类型从 `string` 改为 `number`

- **更新组件**：智能设置相关组件
  - `LlmSettings.vue`
  - `KnowledgeBaseSettings.vue`
  - `McpSettings.vue`
  - `SkillsSettings.vue`
  - `AgentSettings.vue`
  - `IntelligentSettings.vue`

### **BREAKING** 变更

- API 返回的 ID 从字符串（MongoDB ObjectId）变为整数
- 前端需要同步更新 ID 类型处理

## Capabilities

### New Capabilities

- `ai-config-mysql`: AI 智能配置模块 MySQL 存储能力，包含 LLM 模型、配置、知识库、MCP 服务器、技能、Agent 的 CRUD 操作

### Modified Capabilities

无（此迁移为实现层变更，不改变 API 行为规格）

## Impact

### 后端影响

| 文件 | 变更类型 |
|------|---------|
| `models_mysql/ai.py` | 新增 |
| `services/ai_service_mysql.py` | 新增 |
| `app/routers/ai.py` | 修改 |
| `scripts/migrate_ai_config_to_mysql.py` | 新增 |
| `models_mysql/__init__.py` | 修改（导出新模型） |

### 前端影响

| 文件 | 变更类型 |
|------|---------|
| `services/api.ts` | 修改（类型定义） |
| `components/workspace/LlmSettings.vue` | 修改 |
| `components/workspace/KnowledgeBaseSettings.vue` | 修改 |
| `components/workspace/McpSettings.vue` | 修改 |
| `components/workspace/SkillsSettings.vue` | 修改 |
| `components/workspace/AgentSettings.vue` | 修改 |
| `components/workspace/IntelligentSettings.vue` | 修改 |

### 数据库影响

- 新增 6 张 MySQL 表：`llm_models`, `llm_config`, `knowledge_bases`, `mcp_servers`, `skills`, `agents`
- 需执行数据迁移脚本迁移现有 MongoDB 数据