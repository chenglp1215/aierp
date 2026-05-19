## ADDED Requirements

### Requirement: LLM 模型 CRUD 操作

系统 SHALL 提供 LLM 模型的创建、读取、更新、删除操作，数据存储在 MySQL。

#### Scenario: 创建 LLM 模型
- **WHEN** 用户提交 LLM 模型创建请求，包含 name、model_type、status
- **THEN** 系统创建 MySQL 记录，返回整数 ID

#### Scenario: 查询 LLM 模型列表
- **WHEN** 用户请求 LLM 模型列表，指定 page 和 page_size
- **THEN** 系统返回分页数据，每条记录包含整数 ID

#### Scenario: 更新 LLM 模型
- **WHEN** 用户提交更新请求，指定整数 model_id
- **THEN** 系统更新对应 MySQL 记录

#### Scenario: 删除 LLM 模型
- **WHEN** 用户提交删除请求，指定整数 model_id
- **THEN** 系统删除对应 MySQL 记录

### Requirement: LLM 全局配置管理

系统 SHALL 提供 LLM 全局配置的读取和更新操作，配置为单例模式。

#### Scenario: 获取 LLM 配置
- **WHEN** 用户请求获取 LLM 配置
- **THEN** 系统返回当前配置，如无配置则返回默认值

#### Scenario: 更新 LLM 配置
- **WHEN** 用户提交配置更新请求
- **THEN** 系统更新或创建配置记录（单例）

### Requirement: 知识库 CRUD 操作

系统 SHALL 提供知识库的创建、读取、更新、删除操作，数据存储在 MySQL。

#### Scenario: 创建知识库
- **WHEN** 用户提交知识库创建请求，包含 name、kb_type、description
- **THEN** 系统创建 MySQL 记录，返回整数 ID

#### Scenario: 查询知识库列表
- **WHEN** 用户请求知识库列表，可选按 kb_type 和 keyword 过滤
- **THEN** 系统返回分页数据，每条记录包含整数 ID

#### Scenario: 更新知识库
- **WHEN** 用户提交更新请求，指定整数 kb_id
- **THEN** 系统更新对应 MySQL 记录

#### Scenario: 删除知识库
- **WHEN** 用户提交删除请求，指定整数 kb_id
- **THEN** 系统删除对应 MySQL 记录

### Requirement: MCP 服务器 CRUD 操作

系统 SHALL 提供 MCP 服务器的创建、读取、更新、删除操作，数据存储在 MySQL。

#### Scenario: 创建 MCP 服务器
- **WHEN** 用户提交 MCP 服务器创建请求，包含 name、server_type、url、timeout
- **THEN** 系统创建 MySQL 记录，返回整数 ID

#### Scenario: 查询 MCP 服务器列表
- **WHEN** 用户请求 MCP 服务器列表，可选按 status 和 keyword 过滤
- **THEN** 系统返回分页数据，每条记录包含整数 ID

#### Scenario: 更新 MCP 服务器
- **WHEN** 用户提交更新请求，指定整数 server_id
- **THEN** 系统更新对应 MySQL 记录

#### Scenario: 删除 MCP 服务器
- **WHEN** 用户提交删除请求，指定整数 server_id
- **THEN** 系统删除对应 MySQL 记录

### Requirement: 技能 CRUD 操作

系统 SHALL 提供技能的创建、读取、更新、删除、启用/禁用操作，数据存储在 MySQL。

#### Scenario: 创建技能
- **WHEN** 用户提交技能创建请求，包含 name、category、description、content、parameters
- **THEN** 系统创建 MySQL 记录，返回整数 ID

#### Scenario: 查询技能列表
- **WHEN** 用户请求技能列表，可选按 category 和 keyword 过滤
- **THEN** 系统返回分页数据，每条记录包含整数 ID

#### Scenario: 更新技能
- **WHEN** 用户提交更新请求，指定整数 skill_id
- **THEN** 系统更新对应 MySQL 记录

#### Scenario: 删除技能
- **WHEN** 用户提交删除请求，指定整数 skill_id
- **THEN** 系统删除对应 MySQL 记录

#### Scenario: 启用技能
- **WHEN** 用户提交启用请求，指定整数 skill_id
- **THEN** 系统将 enabled 字段设为 True

#### Scenario: 禁用技能
- **WHEN** 用户提交禁用请求，指定整数 skill_id
- **THEN** 系统将 enabled 字段设为 False

### Requirement: Agent CRUD 操作

系统 SHALL 提供 Agent 的创建、读取、更新、删除操作，数据存储在 MySQL，支持关联技能和 MCP 服务器。

#### Scenario: 创建 Agent
- **WHEN** 用户提交 Agent 创建请求，包含 name、description、system_prompt、skill_ids、mcp_server_ids、tools_range
- **THEN** 系统创建 MySQL 记录，返回整数 ID，并触发 agent_manager.reload_agents()

#### Scenario: 查询 Agent 列表
- **WHEN** 用户请求 Agent 列表，可选按 keyword 过滤
- **THEN** 系统返回分页数据，每条记录包含整数 ID

#### Scenario: 更新 Agent
- **WHEN** 用户提交更新请求，指定整数 agent_id
- **THEN** 系统更新对应 MySQL 记录，并触发 agent_manager.reload_agents()

#### Scenario: 删除 Agent
- **WHEN** 用户提交删除请求，指定整数 agent_id
- **THEN** 系统删除对应 MySQL 记录，并触发 agent_manager.reload_agents()

### Requirement: API ID 类型为整数

系统 SHALL 在所有 AI 配置相关 API 中使用整数 ID，替代原有字符串 ObjectId。

#### Scenario: API 返回整数 ID
- **WHEN** 任何 AI 配置 API 返回数据
- **THEN** 所有 id 字段为整数类型（number）

#### Scenario: API 接收整数 ID 参数
- **WHEN** 用户调用需要 ID 参数的 API（如 GET /llm/models/{model_id}）
- **THEN** 系统接受整数类型 ID 参数

### Requirement: 数据迁移脚本

系统 SHALL 提供数据迁移脚本，将 MongoDB 数据迁移到 MySQL。

#### Scenario: 执行迁移脚本
- **WHEN** 迧行 `python scripts/migrate_ai_config_to_mysql.py`
- **THEN** 系统将 MongoDB 6 个集合数据迁移到 MySQL 对应表

#### Scenario: 迁移关联 ID 映射
- **WHEN** 迁移 Agent 数据时，包含 skill_ids 和 mcp_server_ids 字段
- **THEN** 系统正确映射 ObjectId 到新的整数 ID

#### Scenario: 迁移验证
- **WHEN** 迁移完成后
- **THEN** 系统输出迁移统计报告，包含成功/失败数量