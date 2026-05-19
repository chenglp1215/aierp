## 1. 后端 MySQL 模型

- [x] 1.1 创建 `models_mysql/ai.py`，定义 6 个 Tortoise ORM 模型（LlmModel、LlmConfig、KnowledgeBase、McpServer、Skill、Agent）
- [x] 1.2 更新 `models_mysql/__init__.py`，导出新模型
- [x] 1.3 验证模型定义正确，运行 `python -c "from models_mysql.ai import *"`

## 2. 后端 MySQL 服务层

- [x] 2.1 创建 `services/ai_service_mysql.py`，实现 LlmService（list_models、create_model、update_model）
- [x] 2.2 实现 LlmConfigService（get_config、update_config）
- [x] 2.3 实现 KnowledgeBaseService（list_knowledge_bases、create_knowledge_base、update_knowledge_base）
- [x] 2.4 实现 McpService（list_servers、create_server、update_server）
- [x] 2.5 实现 SkillService（list_skills、create_skill、update_skill、enable_skill、disable_skill、get_skills_by_ids）
- [x] 2.6 实现 AgentService（list_agents、create_agent、update_agent、get_agent、init_default_agents）
- [x] 2.7 创建全局服务实例导出

## 3. 后端路由更新

- [x] 3.1 更新 `app/routers/ai.py`，导入 MySQL 服务层替代 MongoDB 服务层
- [x] 3.2 修改路由参数类型：`model_id: str` → `model_id: int`（所有 6 个模块）
- [x] 3.3 验证 API 响应格式正确，ID 为整数类型

## 4. 数据迁移脚本

- [x] 4.1 创建 `scripts/migrate_ai_config_to_mysql.py`
- [x] 4.2 实现迁移逻辑：读取 MongoDB 数据 → 创建 MySQL 记录 → 映射 ObjectId 到整数 ID
- [x] 4.3 处理 Agent 的 skill_ids 和 mcp_server_ids 关联映射
- [x] 4.4 添加迁移统计和错误报告输出
- [x] 4.5 测试迁移脚本执行

## 5. 前端 API 类型更新

- [x] 5.1 更新 `web/src/services/api.ts` 中 llmApi、knowledgeBaseApi、mcpApi、skillApi、agentApi 的 ID 类型定义
- [x] 5.2 修改 getById 参数类型：`id: string` → `id: number`
- [x] 5.3 修改 update/delete 参数类型：`id: string` → `id: number`

## 6. 前端组件更新

- [x] 6.1 更新 `LlmSettings.vue`，适配整数 ID
- [x] 6.2 更新 `KnowledgeBaseSettings.vue`，适配整数 ID
- [x] 6.3 更新 `McpSettings.vue`，适配整数 ID
- [x] 6.4 更新 `SkillsSettings.vue`，适配整数 ID
- [x] 6.5 更新 `AgentSettings.vue`，适配整数 ID
- [x] 6.6 更新 `IntelligentSettings.vue`，适配整数 ID（无需修改，仅作为容器组件）

## 7. 验证与测试

- [ ] 7.1 启动后端服务，验证 API 接口正常响应
- [ ] 7.2 测试各模块 CRUD 操作
- [ ] 7.3 启动前端，验证智能设置页面功能正常
- [ ] 7.4 测试 Agent 创建/更新后 reload_agents 触发正常