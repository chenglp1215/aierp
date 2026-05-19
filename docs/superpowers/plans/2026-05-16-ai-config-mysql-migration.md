# AI 智能配置模块 MySQL 迁移实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 AI 智能配置模块从 MongoDB 迁移到 MySQL，包含 6 个数据模型（LLM 模型、LLM 配置、知识库、MCP 服务器、技能、Agent）。

**Architecture:** 使用 Tortoise ORM 创建 MySQL 模型，新建 MySQL 服务层替代 MongoDB 服务层，更新路由使用整数 ID，提供数据迁移脚本处理 ObjectId 到整数 ID 的映射。

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL, Vue 3, TypeScript

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/models_mysql/ai.py` | 6 个 Tortoise ORM 模型定义 |
| `backend/services/ai_service_mysql.py` | MySQL 服务层，CRUD 操作 |
| `backend/app/routers/ai.py` | 路由更新，整数 ID 参数 |
| `backend/scripts/migrate_ai_config_to_mysql.py` | 数据迁移脚本 |
| `web/src/services/api.ts` | 前端 API 类型更新 |
| `web/src/components/workspace/*.vue` | 前端组件 ID 类型适配 |

---

## Task 1: 创建 MySQL ORM 模型

**Files:**
- Create: `backend/models_mysql/ai.py`
- Modify: `backend/models_mysql/__init__.py`

- [ ] **Step 1: 创建 models_mysql/ai.py 文件**

创建包含 6 个模型的文件：

```python
"""
AI 智能配置 - Tortoise ORM 模型
"""
from enum import Enum
from tortoise import fields
from tortoise.models import Model


class LlmModelType(str, Enum):
    """LLM 模型类型枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    CUSTOM = "custom"


class LlmModelStatus(str, Enum):
    """LLM 模型状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class KnowledgeBaseType(str, Enum):
    """知识库类型枚举"""
    DOCUMENT = "document"
    QA = "qa"
    WEB = "web"


class McpServerType(str, Enum):
    """MCP 服务器类型枚举"""
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class McpServerStatus(str, Enum):
    """MCP 服务器状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class SkillCategory(str, Enum):
    """技能分类枚举"""
    CONVERSATION = "conversation"
    TOOL = "tool"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"


class LlmModel(Model):
    """LLM 模型配置"""
    id = fields.IntField(pk=True, description="模型ID")
    name = fields.CharField(max_length=100, description="模型名称")
    model_type = fields.CharEnumField(LlmModelType, description="模型类型")
    status = fields.CharEnumField(LlmModelStatus, default=LlmModelStatus.ACTIVE, description="状态")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "llm_models"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "model_type": self.model_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LlmConfig(Model):
    """LLM 全局配置（单例）"""
    id = fields.IntField(pk=True, description="配置ID")
    default_model = fields.CharField(max_length=100, default="", description="默认模型")
    api_base_url = fields.CharField(max_length=500, default="", description="API Base URL")
    api_key = fields.CharField(max_length=500, default="", description="API Key")
    streaming = fields.BooleanField(default=True, description="是否启用流式输出")
    timeout = fields.IntField(default=60, description="超时时间(秒)")
    retry_count = fields.IntField(default=3, description="重试次数")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "llm_config"

    def to_dict(self):
        return {
            "id": self.id,
            "default_model": self.default_model,
            "api_base_url": self.api_base_url,
            "api_key": self.api_key,
            "streaming": self.streaming,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class KnowledgeBase(Model):
    """知识库"""
    id = fields.IntField(pk=True, description="知识库ID")
    name = fields.CharField(max_length=100, description="知识库名称")
    kb_type = fields.CharEnumField(KnowledgeBaseType, description="知识库类型")
    description = fields.CharField(max_length=500, null=True, description="描述")
    status = fields.CharField(max_length=20, default="active", description="状态")
    document_count = fields.IntField(default=0, description="文档数量")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "knowledge_bases"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "kb_type": self.kb_type.value,
            "description": self.description,
            "status": self.status,
            "document_count": self.document_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class McpServer(Model):
    """MCP 服务器"""
    id = fields.IntField(pk=True, description="服务器ID")
    name = fields.CharField(max_length=100, description="服务器名称")
    server_type = fields.CharEnumField(McpServerType, description="服务器类型")
    url = fields.CharField(max_length=500, null=True, description="服务器URL")
    status = fields.CharEnumField(McpServerStatus, default=McpServerStatus.ACTIVE, description="状态")
    description = fields.CharField(max_length=500, null=True, description="描述")
    timeout = fields.IntField(default=30, description="超时时间")
    tool_count = fields.IntField(default=0, description="工具数量")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "mcp_servers"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "server_type": self.server_type.value,
            "url": self.url,
            "status": self.status.value,
            "description": self.description,
            "timeout": self.timeout,
            "tool_count": self.tool_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Skill(Model):
    """技能"""
    id = fields.IntField(pk=True, description="技能ID")
    name = fields.CharField(max_length=100, description="技能名称")
    description = fields.CharField(max_length=500, null=True, description="描述")
    category = fields.CharEnumField(SkillCategory, description="分类")
    enabled = fields.BooleanField(default=True, description="是否启用")
    priority = fields.IntField(default=5, description="优先级(1-10)")
    permission_code = fields.CharField(max_length=100, default="", description="权限码")
    parameters = fields.JSONField(default=dict, description="技能参数")
    content = fields.TextField(null=True, description="技能内容(Markdown)")
    config = fields.JSONField(default=dict, null=True, description="技能配置")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "skills"
        ordering = ["-priority", "-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "enabled": self.enabled,
            "priority": self.priority,
            "permission_code": self.permission_code,
            "parameters": self.parameters or {},
            "content": self.content,
            "config": self.config or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Agent(Model):
    """Agent"""
    id = fields.IntField(pk=True, description="Agent ID")
    name = fields.CharField(max_length=100, description="Agent名称")
    description = fields.CharField(max_length=500, null=True, description="描述")
    system_prompt = fields.TextField(default="", description="系统提示词")
    skill_ids = fields.JSONField(default=list, description="关联技能ID列表")
    mcp_server_ids = fields.JSONField(default=list, description="关联MCP服务器ID列表")
    tools_range = fields.JSONField(default=list, description="工具范围")
    enabled = fields.BooleanField(default=True, description="是否启用")
    sort_order = fields.IntField(default=0, description="排序权重")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "agents"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "skill_ids": self.skill_ids or [],
            "mcp_server_ids": self.mcp_server_ids or [],
            "tools_range": self.tools_range or [],
            "enabled": self.enabled,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 更新 models_mysql/__init__.py 导出新模型**

在 `backend/models_mysql/__init__.py` 末尾添加：

```python
from .ai import (
    LlmModel, LlmConfig, LlmModelType, LlmModelStatus,
    KnowledgeBase, KnowledgeBaseType,
    McpServer, McpServerType, McpServerStatus,
    Skill, SkillCategory,
    Agent
)

# 在 __all__ 列表中添加：
    # AI 智能配置
    "LlmModel",
    "LlmConfig",
    "LlmModelType",
    "LlmModelStatus",
    "KnowledgeBase",
    "KnowledgeBaseType",
    "McpServer",
    "McpServerType",
    "McpServerStatus",
    "Skill",
    "SkillCategory",
    "Agent",
```

- [ ] **Step 3: 验证模型定义正确**

Run: `cd E:/ai_erp/aierp/backend && venv/Scripts/python -c "from models_mysql.ai import *; print('模型导入成功')"`

Expected: 输出 "模型导入成功"

- [ ] **Step 4: Commit**

```bash
cd E:/ai_erp/aierp && git add backend/models_mysql/ai.py backend/models_mysql/__init__.py
git commit -m "feat: 添加 AI 智能配置 MySQL ORM 模型

- 添加 LlmModel、LlmConfig、KnowledgeBase、McpServer、Skill、Agent 模型
- 使用 Tortoise ORM 定义
- ID 类型为整数自增

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 2: 创建 MySQL 服务层

**Files:**
- Create: `backend/services/ai_service_mysql.py`

- [ ] **Step 1: 创建 ai_service_mysql.py 文件**

```python
"""
AI 智能配置 - 服务层 (MySQL 版本)
"""
import logging
from typing import Optional, Dict, Any, List

from tortoise.expressions import Q

from models_mysql.ai import (
    LlmModel, LlmConfig, LlmModelType, LlmModelStatus,
    KnowledgeBase, KnowledgeBaseType,
    McpServer, McpServerType, McpServerStatus,
    Skill, SkillCategory,
    Agent
)

logger = logging.getLogger(__name__)


class LlmService:
    """LLM 模型服务"""

    async def create_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建模型"""
        model = await LlmModel.create(
            name=model_data.get("name"),
            model_type=model_data.get("model_type", LlmModelType.OPENAI),
            status=model_data.get("status", LlmModelStatus.ACTIVE),
        )
        return model.to_dict()

    async def update_model(self, model_id: int, model_data: Dict[str, Any]) -> bool:
        """更新模型"""
        model = await LlmModel.get_or_none(id=model_id)
        if not model:
            return False

        if "name" in model_data:
            model.name = model_data["name"]
        if "model_type" in model_data:
            model.model_type = model_data["model_type"]
        if "status" in model_data:
            model.status = model_data["status"]

        await model.save()
        return True

    async def list_models(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询模型列表"""
        query = LlmModel.all()

        if keyword:
            query = query.filter(
                Q(name__contains=keyword) | Q(model_type__contains=keyword)
            )

        total = await query.count()
        models = await query.offset((page - 1) * page_size).limit(page_size)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [m.to_dict() for m in models],
        }

    async def get_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取模型"""
        model = await LlmModel.get_or_none(id=model_id)
        return model.to_dict() if model else None

    async def delete(self, model_id: int) -> bool:
        """删除模型"""
        model = await LlmModel.get_or_none(id=model_id)
        if not model:
            return False
        await model.delete()
        return True


class LlmConfigService:
    """LLM 配置服务"""

    async def get_config(self) -> Optional[Dict[str, Any]]:
        """获取配置（单例）"""
        config = await LlmConfig.first()
        if config:
            return config.to_dict()
        return None

    async def update_config(self, config_data: Dict[str, Any]) -> bool:
        """更新配置（单例）"""
        config = await LlmConfig.first()

        if config:
            # 更新现有配置
            for field in ["default_model", "api_base_url", "api_key", "streaming", "timeout", "retry_count"]:
                if field in config_data:
                    setattr(config, field, config_data[field])
            await config.save()
        else:
            # 创建新配置
            await LlmConfig.create(
                default_model=config_data.get("default_model", ""),
                api_base_url=config_data.get("api_base_url", ""),
                api_key=config_data.get("api_key", ""),
                streaming=config_data.get("streaming", True),
                timeout=config_data.get("timeout", 60),
                retry_count=config_data.get("retry_count", 3),
            )
        return True


class KnowledgeBaseService:
    """知识库服务"""

    async def create_knowledge_base(self, kb_data: Dict[str, Any]) -> str:
        """创建知识库"""
        kb = await KnowledgeBase.create(
            name=kb_data.get("name"),
            kb_type=kb_data.get("kb_type"),
            description=kb_data.get("description"),
        )
        return str(kb.id)

    async def update_knowledge_base(self, kb_id: int, kb_data: Dict[str, Any]) -> bool:
        """更新知识库"""
        kb = await KnowledgeBase.get_or_none(id=kb_id)
        if not kb:
            return False

        for field in ["name", "kb_type", "description", "status", "document_count"]:
            if field in kb_data:
                setattr(kb, field, kb_data[field])

        await kb.save()
        return True

    async def list_knowledge_bases(
        self,
        page: int = 1,
        page_size: int = 20,
        kb_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询知识库列表"""
        query = KnowledgeBase.all()

        if kb_type:
            query = query.filter(kb_type=kb_type)
        if keyword:
            query = query.filter(
                Q(name__contains=keyword) | Q(description__contains=keyword)
            )

        total = await query.count()
        kbs = await query.offset((page - 1) * page_size).limit(page_size)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [kb.to_dict() for kb in kbs],
        }

    async def get_by_id(self, kb_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取知识库"""
        kb = await KnowledgeBase.get_or_none(id=kb_id)
        return kb.to_dict() if kb else None

    async def delete(self, kb_id: int) -> bool:
        """删除知识库"""
        kb = await KnowledgeBase.get_or_none(id=kb_id)
        if not kb:
            return False
        await kb.delete()
        return True


class McpService:
    """MCP 服务器服务"""

    async def create_server(self, server_data: Dict[str, Any]) -> str:
        """创建 MCP 服务器"""
        server = await McpServer.create(
            name=server_data.get("name"),
            server_type=server_data.get("server_type"),
            url=server_data.get("url"),
            description=server_data.get("description"),
            timeout=server_data.get("timeout", 30),
        )
        return str(server.id)

    async def update_server(self, server_id: int, server_data: Dict[str, Any]) -> bool:
        """更新 MCP 服务器"""
        server = await McpServer.get_or_none(id=server_id)
        if not server:
            return False

        for field in ["name", "server_type", "url", "description", "timeout", "status", "tool_count"]:
            if field in server_data:
                setattr(server, field, server_data[field])

        await server.save()
        return True

    async def list_servers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询服务器列表"""
        query = McpServer.all()

        if status:
            query = query.filter(status=status)
        if keyword:
            query = query.filter(
                Q(name__contains=keyword) | Q(description__contains=keyword)
            )

        total = await query.count()
        servers = await query.offset((page - 1) * page_size).limit(page_size)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [s.to_dict() for s in servers],
        }

    async def get_by_id(self, server_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取服务器"""
        server = await McpServer.get_or_none(id=server_id)
        return server.to_dict() if server else None

    async def delete(self, server_id: int) -> bool:
        """删除服务器"""
        server = await McpServer.get_or_none(id=server_id)
        if not server:
            return False
        await server.delete()
        return True


class SkillService:
    """技能服务"""

    async def create_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建技能"""
        from app.agent.skills.loader import load_skill_from_db
        skill_data = load_skill_from_db(skill_data)

        skill = await Skill.create(
            name=skill_data.get("name"),
            description=skill_data.get("description"),
            category=skill_data.get("category"),
            enabled=skill_data.get("enabled", True),
            priority=skill_data.get("priority", 5),
            permission_code=skill_data.get("permission_code", ""),
            parameters=skill_data.get("parameters", {}),
            content=skill_data.get("content"),
            config=skill_data.get("config"),
        )
        result = skill.to_dict()
        result["id"] = str(skill.id)
        return result

    async def update_skill(self, skill_id: int, skill_data: Dict[str, Any]) -> bool:
        """更新技能"""
        from app.agent.skills.loader import load_skill_from_db
        skill_data = load_skill_from_db(skill_data)

        skill = await Skill.get_or_none(id=skill_id)
        if not skill:
            return False

        for field in ["name", "description", "category", "enabled", "priority", "permission_code", "parameters", "content", "config"]:
            if field in skill_data:
                setattr(skill, field, skill_data[field])

        await skill.save()
        return True

    async def enable_skill(self, skill_id: int) -> bool:
        """启用技能"""
        skill = await Skill.get_or_none(id=skill_id)
        if not skill:
            return False
        skill.enabled = True
        await skill.save()
        return True

    async def disable_skill(self, skill_id: int) -> bool:
        """禁用技能"""
        skill = await Skill.get_or_none(id=skill_id)
        if not skill:
            return False
        skill.enabled = False
        await skill.save()
        return True

    async def list_skills(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询技能列表"""
        query = Skill.all()

        if category:
            query = query.filter(category=category)
        if keyword:
            query = query.filter(
                Q(name__contains=keyword) | Q(description__contains=keyword)
            )

        total = await query.count()
        skills = await query.offset((page - 1) * page_size).limit(page_size)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [s.to_dict() for s in skills],
        }

    async def get_by_id(self, skill_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取技能"""
        skill = await Skill.get_or_none(id=skill_id)
        return skill.to_dict() if skill else None

    async def delete(self, skill_id: int) -> bool:
        """删除技能"""
        skill = await Skill.get_or_none(id=skill_id)
        if not skill:
            return False
        await skill.delete()
        return True

    async def get_skills_by_ids(self, skill_ids: List[int]) -> List[Dict[str, Any]]:
        """根据 ID 列表获取技能"""
        from app.agent.skills.loader import load_skill_from_db

        if not skill_ids:
            return []

        skills = await Skill.filter(id__in=skill_ids, enabled=True).all()
        result = []
        for skill in skills:
            skill_dict = skill.to_dict()
            skill_dict = load_skill_from_db(skill_dict)
            result.append(skill_dict)
        return result


class AgentService:
    """Agent 服务"""

    async def create_agent(self, agent_data: Dict[str, Any]) -> str:
        """创建 Agent"""
        agent = await Agent.create(
            name=agent_data.get("name"),
            description=agent_data.get("description"),
            system_prompt=agent_data.get("system_prompt", ""),
            skill_ids=agent_data.get("skill_ids", []),
            mcp_server_ids=agent_data.get("mcp_server_ids", []),
            tools_range=agent_data.get("tools_range", []),
            enabled=agent_data.get("enabled", True),
            sort_order=agent_data.get("sort_order", 0),
        )
        return str(agent.id)

    async def update_agent(self, agent_id: int, agent_data: Dict[str, Any]) -> bool:
        """更新 Agent"""
        agent = await Agent.get_or_none(id=agent_id)
        if not agent:
            return False

        for field in ["name", "description", "system_prompt", "skill_ids", "mcp_server_ids", "tools_range", "enabled", "sort_order"]:
            if field in agent_data:
                setattr(agent, field, agent_data[field])

        await agent.save()
        return True

    async def get_agent(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """获取单个 Agent"""
        agent = await Agent.get_or_none(id=agent_id)
        return agent.to_dict() if agent else None

    async def list_agents(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询 Agent 列表"""
        query = Agent.all()

        if keyword:
            query = query.filter(
                Q(name__contains=keyword) | Q(description__contains=keyword)
            )

        total = await query.count()
        agents = await query.offset((page - 1) * page_size).limit(page_size)

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [a.to_dict() for a in agents],
        }

    async def get_by_id(self, agent_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取 Agent"""
        agent = await Agent.get_or_none(id=agent_id)
        return agent.to_dict() if agent else None

    async def delete(self, agent_id: int) -> bool:
        """删除 Agent"""
        agent = await Agent.get_or_none(id=agent_id)
        if not agent:
            return False
        await agent.delete()
        return True

    async def init_default_agents(self) -> None:
        """初始化默认 Agent"""
        existing = await Agent.all().count()
        if existing > 0:
            return

        default_agents = [
            {
                "name": "智能问答",
                "description": "回答用户关于产品和服务的问题",
                "system_prompt": "你是一个智能客服助手，擅长回答用户关于产品功能、服务流程等问题。",
                "skill_ids": [],
                "mcp_server_ids": [],
                "tools_range": [],
                "enabled": True,
                "sort_order": 1
            },
            {
                "name": "新建订单",
                "description": "帮助用户创建销售订单",
                "system_prompt": "你是一个订单助手，擅长帮助用户创建和管理销售订单。",
                "skill_ids": [],
                "mcp_server_ids": [],
                "tools_range": [],
                "enabled": True,
                "sort_order": 2
            },
            {
                "name": "导出报表",
                "description": "帮助用户导出各类业务报表",
                "system_prompt": "你是一个报表助手，擅长帮助用户导出销售、客户等各类业务报表。",
                "skill_ids": [],
                "mcp_server_ids": [],
                "tools_range": [],
                "enabled": True,
                "sort_order": 3
            }
        ]

        for agent_data in default_agents:
            await Agent.create(**agent_data)
        logger.info("默认 Agent 初始化完成")


# 全局实例
llm_service = LlmService()
llm_config_service = LlmConfigService()
knowledge_base_service = KnowledgeBaseService()
mcp_service = McpService()
skill_service = SkillService()
agent_service = AgentService()
```

- [ ] **Step 2: 验证服务层导入正确**

Run: `cd E:/ai_erp/aierp/backend && venv/Scripts/python -c "from services.ai_service_mysql import *; print('服务层导入成功')"`

Expected: 输出 "服务层导入成功"

- [ ] **Step 3: Commit**

```bash
cd E:/ai_erp/aierp && git add backend/services/ai_service_mysql.py
git commit -m "feat: 添加 AI 智能配置 MySQL 服务层

- 实现 LlmService、LlmConfigService、KnowledgeBaseService
- 实现 McpService、SkillService、AgentService
- 支持整数 ID 操作

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 3: 更新路由使用 MySQL 服务层

**Files:**
- Modify: `backend/app/routers/ai.py`

- [ ] **Step 1: 更新路由导入和服务层引用**

修改 `backend/app/routers/ai.py` 文件头部导入：

```python
# 将原来的导入：
# from services.ai_service import (
#     llm_service, llm_config_service,
#     knowledge_base_service, mcp_service,
#     skill_service, agent_service
# )

# 改为：
from services.ai_service_mysql import (
    llm_service, llm_config_service,
    knowledge_base_service, mcp_service,
    skill_service, agent_service
)
```

- [ ] **Step 2: 修改所有路由参数类型从 str 改为 int**

需要修改的参数：
- `model_id: str` → `model_id: int`
- `kb_id: str` → `kb_id: int`
- `server_id: str` → `server_id: int`
- `skill_id: str` → `skill_id: int`
- `agent_id: str` → `agent_id: int`

具体修改位置：
- Line 40: `async def get_llm_model(model_id: int):`
- Line 56: `async def update_llm_model(model_id: int, model_data: LlmModelUpdate):`
- Line 65: `async def delete_llm_model(model_id: int):`
- Line 74: `async def test_llm_model(model_id: int):`
- Line 114: `async def get_knowledge_base(kb_id: int):`
- Line 130: `async def update_knowledge_base(kb_id: int, kb_data: KnowledgeBaseUpdate):`
- Line 139: `async def delete_knowledge_base(kb_id: int):`
- Line 161: `async def get_mcp_server(server_id: int):`
- Line 177: `async def update_mcp_server(server_id: int, server_data: McpServerUpdate):`
- Line 186: `async def delete_mcp_server(server_id: int):`
- Line 195: `async def test_mcp_server(server_id: int):`
- Line 204: `async def get_mcp_server_tools(server_id: int):`
- Line 226: `async def get_skill(skill_id: int):`
- Line 242: `async def update_skill(skill_id: int, skill_data: SkillUpdate):`
- Line 251: `async def delete_skill(skill_id: int):`
- Line 260: `async def enable_skill(skill_id: int):`
- Line 269: `async def disable_skill(skill_id: int):`
- Line 290: `async def get_agent(agent_id: int):`
- Line 307: `async def update_agent(agent_id: int, agent_data: AgentUpdate):`
- Line 317: `async def delete_agent(agent_id: int):`

- [ ] **Step 3: Commit**

```bash
cd E:/ai_erp/aierp && git add backend/app/routers/ai.py
git commit -m "feat: 更新 AI 配置路由使用 MySQL 服务层

- 切换到 ai_service_mysql 服务层
- 所有 ID 参数从 str 改为 int

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 4: 创建数据迁移脚本

**Files:**
- Create: `backend/scripts/migrate_ai_config_to_mysql.py`

- [ ] **Step 1: 创建迁移脚本**

```python
"""
AI 智能配置数据迁移脚本 - MongoDB 到 MySQL
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from tortoise import Tortoise
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.settings import settings
from models_mysql.ai import (
    LlmModel, LlmConfig, LlmModelType, LlmModelStatus,
    KnowledgeBase, KnowledgeBaseType,
    McpServer, McpServerType, McpServerStatus,
    Skill, SkillCategory,
    Agent
)


async def get_mongo_client():
    """获取 MongoDB 客户端"""
    mongo_url = settings.MONGO_URL
    client = AsyncIOMotorClient(mongo_url)
    return client


async def init_tortoise():
    """初始化 Tortoise ORM"""
    await Tortoise.init(
        db_url=f"mysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
        modules={"models": ["models_mysql.ai"]},
    )
    await Tortoise.generate_schemas()


async def migrate_llm_models(db) -> Dict[str, int]:
    """迁移 LLM 模型"""
    print("\n--- 迁移 LLM 模型 ---")
    collection = db["llm_models"]
    total = await collection.count_documents({})
    print(f"MongoDB 记录数: {total}")

    id_mapping = {}
    success = 0

    async for doc in collection.find({}):
        try:
            model = await LlmModel.create(
                name=doc.get("name", ""),
                model_type=doc.get("model_type", "openai"),
                status=doc.get("status", "active"),
            )
            id_mapping[str(doc["_id"])] = model.id
            success += 1
        except Exception as e:
            print(f"迁移失败: {doc.get('name')}, 错误: {e}")

    print(f"成功迁移: {success}")
    return id_mapping


async def migrate_llm_config(db) -> bool:
    """迁移 LLM 配置"""
    print("\n--- 迁移 LLM 配置 ---")
    collection = db["llm_config"]

    doc = await collection.find_one({})
    if not doc:
        print("无配置数据")
        return True

    # 检查是否已存在
    existing = await LlmConfig.first()
    if existing:
        print("配置已存在，跳过")
        return True

    await LlmConfig.create(
        default_model=doc.get("default_model", ""),
        api_base_url=doc.get("api_base_url", ""),
        api_key=doc.get("api_key", ""),
        streaming=doc.get("streaming", True),
        timeout=doc.get("timeout", 60),
        retry_count=doc.get("retry_count", 3),
    )
    print("配置迁移成功")
    return True


async def migrate_knowledge_bases(db) -> Dict[str, int]:
    """迁移知识库"""
    print("\n--- 迁移知识库 ---")
    collection = db["knowledge_bases"]
    total = await collection.count_documents({})
    print(f"MongoDB 记录数: {total}")

    id_mapping = {}
    success = 0

    async for doc in collection.find({}):
        try:
            kb = await KnowledgeBase.create(
                name=doc.get("name", ""),
                kb_type=doc.get("kb_type", "document"),
                description=doc.get("description"),
                status=doc.get("status", "active"),
                document_count=doc.get("document_count", 0),
            )
            id_mapping[str(doc["_id"])] = kb.id
            success += 1
        except Exception as e:
            print(f"迁移失败: {doc.get('name')}, 错误: {e}")

    print(f"成功迁移: {success}")
    return id_mapping


async def migrate_mcp_servers(db) -> Dict[str, int]:
    """迁移 MCP 服务器"""
    print("\n--- 迁移 MCP 服务器 ---")
    collection = db["mcp_servers"]
    total = await collection.count_documents({})
    print(f"MongoDB 记录数: {total}")

    id_mapping = {}
    success = 0

    async for doc in collection.find({}):
        try:
            server = await McpServer.create(
                name=doc.get("name", ""),
                server_type=doc.get("server_type", "stdio"),
                url=doc.get("url"),
                status=doc.get("status", "active"),
                description=doc.get("description"),
                timeout=doc.get("timeout", 30),
                tool_count=doc.get("tool_count", 0),
            )
            id_mapping[str(doc["_id"])] = server.id
            success += 1
        except Exception as e:
            print(f"迁移失败: {doc.get('name')}, 错误: {e}")

    print(f"成功迁移: {success}")
    return id_mapping


async def migrate_skills(db) -> Dict[str, int]:
    """迁移技能"""
    print("\n--- 迁移技能 ---")
    collection = db["skills"]
    total = await collection.count_documents({})
    print(f"MongoDB 记录数: {total}")

    id_mapping = {}
    success = 0

    async for doc in collection.find({}):
        try:
            skill = await Skill.create(
                name=doc.get("name", ""),
                description=doc.get("description"),
                category=doc.get("category", "tool"),
                enabled=doc.get("enabled", True),
                priority=doc.get("priority", 5),
                permission_code=doc.get("permission_code", ""),
                parameters=doc.get("parameters", {}),
                content=doc.get("content"),
                config=doc.get("config"),
            )
            id_mapping[str(doc["_id"])] = skill.id
            success += 1
        except Exception as e:
            print(f"迁移失败: {doc.get('name')}, 错误: {e}")

    print(f"成功迁移: {success}")
    return id_mapping


async def migrate_agents(db, skill_mapping: Dict[str, int], mcp_mapping: Dict[str, int]) -> Dict[str, int]:
    """迁移 Agent"""
    print("\n--- 迁移 Agent ---")
    collection = db["agents"]
    total = await collection.count_documents({})
    print(f"MongoDB 记录数: {total}")

    id_mapping = {}
    success = 0

    async for doc in collection.find({}):
        try:
            # 映射 skill_ids
            old_skill_ids = doc.get("skill_ids", [])
            new_skill_ids = []
            for old_id in old_skill_ids:
                new_id = skill_mapping.get(str(old_id))
                if new_id:
                    new_skill_ids.append(new_id)

            # 映射 mcp_server_ids
            old_mcp_ids = doc.get("mcp_server_ids", [])
            new_mcp_ids = []
            for old_id in old_mcp_ids:
                new_id = mcp_mapping.get(str(old_id))
                if new_id:
                    new_mcp_ids.append(new_id)

            agent = await Agent.create(
                name=doc.get("name", ""),
                description=doc.get("description"),
                system_prompt=doc.get("system_prompt", ""),
                skill_ids=new_skill_ids,
                mcp_server_ids=new_mcp_ids,
                tools_range=doc.get("tools_range", []),
                enabled=doc.get("enabled", True),
                sort_order=doc.get("sort_order", 0),
            )
            id_mapping[str(doc["_id"])] = agent.id
            success += 1
        except Exception as e:
            print(f"迁移失败: {doc.get('name')}, 错误: {e}")

    print(f"成功迁移: {success}")
    return id_mapping


async def main():
    """主迁移函数"""
    print("=" * 60)
    print("开始 AI 智能配置数据迁移...")
    print("=" * 60)

    # 初始化
    await init_tortoise()
    mongo_client = await get_mongo_client()
    db = mongo_client[settings.MONGO_DB_NAME]

    # 按依赖顺序迁移
    llm_mapping = await migrate_llm_models(db)
    await migrate_llm_config(db)
    kb_mapping = await migrate_knowledge_bases(db)
    mcp_mapping = await migrate_mcp_servers(db)
    skill_mapping = await migrate_skills(db)
    agent_mapping = await migrate_agents(db, skill_mapping, mcp_mapping)

    # 输出统计
    print("\n" + "=" * 60)
    print("迁移完成!")
    print(f"LLM 模型: {len(llm_mapping)}")
    print(f"知识库: {len(kb_mapping)}")
    print(f"MCP 服务器: {len(mcp_mapping)}")
    print(f"技能: {len(skill_mapping)}")
    print(f"Agent: {len(agent_mapping)}")
    print("=" * 60)

    # 验证
    print("\nMySQL 数据统计:")
    print(f"LLM 模型: {await LlmModel.all().count()}")
    print(f"LLM 配置: {await LlmConfig.all().count()}")
    print(f"知识库: {await KnowledgeBase.all().count()}")
    print(f"MCP 服务器: {await McpServer.all().count()}")
    print(f"技能: {await Skill.all().count()}")
    print(f"Agent: {await Agent.all().count()}")

    # 关闭连接
    mongo_client.close()
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Commit**

```bash
cd E:/ai_erp/aierp && git add backend/scripts/migrate_ai_config_to_mysql.py
git commit -m "feat: 添加 AI 智能配置数据迁移脚本

- 迁移 6 个 MongoDB 集合到 MySQL
- 处理 ObjectId 到整数 ID 映射
- 处理 Agent 关联 ID 列表映射

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 5: 更新前端 API 类型定义

**Files:**
- Modify: `web/src/services/api.ts`

- [ ] **Step 1: 更新 llmApi 的 ID 类型**

找到 `llmApi` 定义（约 1079 行），修改：

```typescript
export const llmApi = {
  list: (params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>('/llm/models', params)
  },
  getById: (id: number) => {  // string → number
    return apiService.get<any>(`/llm/models/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/llm/models', data)
  },
  update: (id: number, data: any) => {  // string → number
    return apiService.put<any>(`/llm/models/${id}`, data)
  },
  delete: (id: number) => {  // string → number
    return apiService.delete<any>(`/llm/models/${id}`)
  },
  getConfig: () => {
    return apiService.get<any>('/llm/config')
  },
  updateConfig: (data: any) => {
    return apiService.put<any>('/llm/config', data)
  },
  testConnection: (id: number) => {  // string → number
    return apiService.post<any>(`/llm/models/${id}/test`)
  }
}
```

- [ ] **Step 2: 更新 knowledgeBaseApi 的 ID 类型**

```typescript
export const knowledgeBaseApi = {
  list: (params?: { page?: number; page_size?: number; kb_type?: string }) => {
    return apiService.get<any>('/knowledge-base/collections', params)
  },
  getById: (id: number) => {  // string → number
    return apiService.get<any>(`/knowledge-base/collections/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/knowledge-base/collections', data)
  },
  update: (id: number, data: any) => {  // string → number
    return apiService.put<any>(`/knowledge-base/collections/${id}`, data)
  },
  delete: (id: number) => {  // string → number
    return apiService.delete<any>(`/knowledge-base/collections/${id}`)
  },
  // ... 其他方法保持不变
}
```

- [ ] **Step 3: 更新 mcpApi 的 ID 类型**

```typescript
export const mcpApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) => {
    return apiService.get<any>('/mcp/servers', params)
  },
  getById: (id: number) => {  // string → number
    return apiService.get<any>(`/mcp/servers/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/mcp/servers', data)
  },
  update: (id: number, data: any) => {  // string → number
    return apiService.put<any>(`/mcp/servers/${id}`, data)
  },
  delete: (id: number) => {  // string → number
    return apiService.delete<any>(`/mcp/servers/${id}`)
  },
  getTools: (serverId: number) => {  // string → number
    return apiService.get<any>(`/mcp/servers/${serverId}/tools`)
  },
  testConnection: (serverId: number) => {  // string → number
    return apiService.post<any>(`/mcp/servers/${serverId}/test`)
  }
}
```

- [ ] **Step 4: 更新 skillApi 的 ID 类型**

```typescript
export const skillApi = {
  list: (params?: { page?: number; page_size?: number; category?: string }) => {
    return apiService.get<any>('/skills', params)
  },
  getById: (id: number) => {  // string → number
    return apiService.get<any>(`/skills/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/skills', data)
  },
  update: (id: number, data: any) => {  // string → number
    return apiService.put<any>(`/skills/${id}`, data)
  },
  delete: (id: number) => {  // string → number
    return apiService.delete<any>(`/skills/${id}`)
  },
  enable: (id: number) => {  // string → number
    return apiService.patch<any>(`/skills/${id}/enable`)
  },
  disable: (id: number) => {  // string → number
    return apiService.patch<any>(`/skills/${id}/disable`)
  }
}
```

- [ ] **Step 5: 更新 agentApi 的 ID 类型**

```typescript
export const agentApi = {
  list: (params?: { page?: number; page_size?: number }) => {
    return apiService.get<any>('/agents', params)
  },
  getById: (id: number) => {  // string → number
    return apiService.get<any>(`/agents/${id}`)
  },
  create: (data: any) => {
    return apiService.post<any>('/agents', data)
  },
  update: (id: number, data: any) => {  // string → number
    return apiService.put<any>(`/agents/${id}`, data)
  },
  delete: (id: number) => {  // string → number
    return apiService.delete<any>(`/agents/${id}`)
  }
}
```

- [ ] **Step 6: Commit**

```bash
cd E:/ai_erp/aierp && git add web/src/services/api.ts
git commit -m "feat: 更新前端 AI 配置 API 类型为整数 ID

- llmApi、knowledgeBaseApi、mcpApi、skillApi、agentApi
- 所有 ID 参数从 string 改为 number

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 6: 更新前端组件 ID 类型

**Files:**
- Modify: `web/src/components/workspace/LlmSettings.vue`
- Modify: `web/src/components/workspace/KnowledgeBaseSettings.vue`
- Modify: `web/src/components/workspace/McpSettings.vue`
- Modify: `web/src/components/workspace/SkillsSettings.vue`
- Modify: `web/src/components/workspace/AgentSettings.vue`

- [ ] **Step 1: 更新 LlmSettings.vue**

修改接口定义和 ref 类型：

```typescript
// 将
interface LlmModel {
  id?: string
  name: string
  model_type: string
  status: string
}

// 改为
interface LlmModel {
  id?: number
  name: string
  model_type: string
  status: string
}

// 将
const testingModelId = ref<string | null>(null)
const deleteTargetId = ref<string | null>(null)

// 改为
const testingModelId = ref<number | null>(null)
const deleteTargetId = ref<number | null>(null)

// 将
const testConnection = async (modelId: string) => {
// 改为
const testConnection = async (modelId: number) => {

// 将
const confirmDelete = (id: string) => {
// 改为
const confirmDelete = (id: number) => {
```

- [ ] **Step 2: 更新 KnowledgeBaseSettings.vue**

同样的模式，将所有 `id?: string` 改为 `id?: number`，相关 ref 类型从 `string | null` 改为 `number | null`。

- [ ] **Step 3: 更新 McpSettings.vue**

同样的模式修改。

- [ ] **Step 4: 更新 SkillsSettings.vue**

同样的模式修改。

- [ ] **Step 5: 更新 AgentSettings.vue**

同样的模式修改。

- [ ] **Step 6: Commit**

```bash
cd E:/ai_erp/aierp && git add web/src/components/workspace/LlmSettings.vue web/src/components/workspace/KnowledgeBaseSettings.vue web/src/components/workspace/McpSettings.vue web/src/components/workspace/SkillsSettings.vue web/src/components/workspace/AgentSettings.vue
git commit -m "feat: 更新前端智能设置组件适配整数 ID

- LlmSettings、KnowledgeBaseSettings、McpSettings
- SkillsSettings、AgentSettings
- ID 类型从 string 改为 number

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Task 7: 验证与测试

- [ ] **Step 1: 启动后端服务验证**

Run: `cd E:/ai_erp/aierp/backend && venv/Scripts/python -m uvicorn app.main:app --reload`

Expected: 服务正常启动，无导入错误

- [ ] **Step 2: 测试 API 接口**

使用 curl 或 Postman 测试：
- GET `/api/v1/llm/models` - 应返回空列表或数据
- POST `/api/v1/llm/models` - 创建模型，返回整数 ID
- GET `/api/v1/llm/models/{id}` - 使用整数 ID 查询

- [ ] **Step 3: 启动前端验证**

Run: `cd E:/ai_erp/aierp/web && npm run dev`

Expected: 前端正常启动，智能设置页面无报错

- [ ] **Step 4: 端到端测试**

1. 打开智能设置页面
2. 创建 LLM 模型，验证 ID 为数字
3. 编辑模型，验证保存成功
4. 删除模型，验证删除成功

- [ ] **Step 5: 最终 Commit**

```bash
cd E:/ai_erp/aierp && git add -A
git commit -m "feat: 完成 AI 智能配置模块 MySQL 迁移

- 后端：MySQL ORM 模型、服务层、路由更新
- 前端：API 类型、组件 ID 类型更新
- 迁移脚本：支持 MongoDB 到 MySQL 数据迁移

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```