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