## Context

AI 智能配置模块当前使用 MongoDB 存储 6 个集合的数据：`llm_models`、`llm_config`、`knowledge_bases`、`mcp_servers`、`skills`、`agents`。项目其他核心业务模块已迁移到 MySQL（使用 Tortoise ORM），需要统一数据存储方案。

当前架构：
- MongoDB 集合使用 `BaseService` 基类，通过 `motor.motor_asyncio` 异步驱动
- ID 为字符串类型（MongoDB ObjectId）
- 无外键约束，数据关系通过应用层维护

目标架构：
- MySQL 表使用 Tortoise ORM 模型
- ID 为自增整数类型
- 保持现有 API 接口不变（除 ID 类型外）

## Goals / Non-Goals

**Goals:**
- 将 6 个 MongoDB 集合迁移到 MySQL 表
- 保持 API 接口兼容（响应格式不变）
- 提供数据迁移脚本，支持平滑迁移
- 前端适配整数 ID 类型

**Non-Goals:**
- 不改变 API 业务逻辑
- 不新增功能特性
- 不修改 Agent 运行时逻辑（`app/agent/` 目录）

## Decisions

### 1. ORM 模型设计

**决定**：使用 Tortoise ORM，遵循现有 `models_mysql/` 目录规范

**理由**：
- 与项目其他模块保持一致
- Tortoise ORM 支持异步操作，与 FastAPI 配合良好
- 提供类型安全和关系管理

**替代方案**：
- SQLAlchemy：项目未使用，引入成本高
- 继续使用 MongoDB：与项目统一存储策略冲突

### 2. ID 类型处理

**决定**：使用自增整数 ID，API 返回整数

**理由**：
- MySQL 自增主键性能好
- 整数 ID 更易读、易调试
- 与其他已迁移模块保持一致

**迁移策略**：
- 数据迁移时，ObjectId 映射到新整数 ID
- 关联字段（如 `skill_ids`、`mcp_server_ids`）需要重新映射

### 3. LlmConfig 单例处理

**决定**：`llm_config` 表只存储一条记录，服务层保证单例

**理由**：
- 原 MongoDB 设计就是单文档存储
- 简化配置管理，避免多配置冲突

**实现**：
- 表结构允许存储多条，但服务层 `get_config()` 只返回第一条
- `update_config()` 使用 `get_or_create` 模式

### 4. JSON 字段处理

**决定**：复杂字段使用 `JSONField` 存储

**涉及字段**：
- `Skill.parameters` - 技能参数配置
- `Skill.config` - 技能配置
- `Agent.skill_ids` - 关联技能 ID 列表（改为 JSON 数组）
- `Agent.mcp_server_ids` - 关联 MCP 服务器 ID 列表
- `Agent.tools_range` - 工具范围列表

**理由**：
- 这些字段结构灵活，不需要强类型约束
- 避免创建多对多关联表增加复杂度

### 5. 服务层设计

**决定**：创建新的 `ai_service_mysql.py`，不修改原 `ai_service.py`

**理由**：
- 保留原文件作为备份参考
- 便于回滚（只需切换路由导入）
- 符合项目迁移惯例（如 `supplier_service_mysql.py`）

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 数据迁移过程中服务不可用 | 迁移脚本支持断点续传，记录已迁移 ID |
| ID 类型变更导致前端兼容问题 | 前端同步更新，统一使用 `number` 类型 |
| Agent 关联 ID 列表迁移失败 | 迁移脚本验证关联完整性，输出错误报告 |
| 迁移后 Agent 运行异常 | 保留 `agent_manager.reload_agents()` 逻辑，支持热重载 |

## Migration Plan

### 阶段 1：后端开发（无数据迁移）

1. 创建 MySQL ORM 模型 `models_mysql/ai.py`
2. 创建 MySQL 服务层 `services/ai_service_mysql.py`
3. 更新路由导入，使用 MySQL 服务层
4. 本地测试 API 功能

### 阶段 2：数据迁移

1. 部署后端代码（此时 MongoDB 数据仍在）
2. 执行迁移脚本 `python scripts/migrate_ai_config_to_mysql.py`
3. 验证数据完整性

### 阶段 3：前端适配

1. 更新 API 类型定义
2. 更新组件 ID 类型处理
3. 端到端测试

### 回滚策略

如需回滚：
1. 恢复路由导入为 MongoDB 服务层
2. 重新部署后端
3. 前端回退 ID 类型为 `string`

## Open Questions

无待解决问题，设计已明确。