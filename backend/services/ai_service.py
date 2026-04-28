from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from .base_service import BaseService

logger = logging.getLogger(__name__)


class LlmService(BaseService):
    """LLM 模型服务"""

    def __init__(self):
        super().__init__("llm_models")

    async def create_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建模型"""
        model_data["created_at"] = datetime.now()
        model_data["updated_at"] = datetime.now()
        model_data["id"] = await self.create(model_data)
        return model_data

    async def update_model(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """更新模型"""
        return await self.update(model_id, model_data)

    async def list_models(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询模型列表"""
        filters = {}
        if keyword:
            filters["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"model_type": {"$regex": keyword, "$options": "i"}}
            ]
        return await self.list(page, page_size, filters, "created_at", -1)


class LlmConfigService(BaseService):
    """LLM 配置服务"""

    def __init__(self):
        super().__init__("llm_config")

    async def get_config(self) -> Optional[Dict[str, Any]]:
        """获取配置"""
        config = await self.collection.find_one({})
        if config:
            config["id"] = str(config.pop("_id"))
        return config

    async def update_config(self, config_data: Dict[str, Any]) -> bool:
        """更新配置"""
        existing = await self.collection.find_one({})
        if existing:
            config_data["updated_at"] = datetime.now()
            result = await self.collection.update_one({}, {"$set": config_data})
            return result.modified_count > 0
        else:
            config_data["created_at"] = datetime.now()
            config_data["updated_at"] = datetime.now()
            await self.collection.insert_one(config_data)
            return True


class KnowledgeBaseService(BaseService):
    """知识库服务"""

    def __init__(self):
        super().__init__("knowledge_bases")

    async def create_knowledge_base(self, kb_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建知识库"""
        kb_data["document_count"] = 0
        return await self.create(kb_data)

    async def update_knowledge_base(self, kb_id: str, kb_data: Dict[str, Any]) -> bool:
        """更新知识库"""
        return await self.update(kb_id, kb_data)

    async def list_knowledge_bases(
        self,
        page: int = 1,
        page_size: int = 20,
        kb_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询知识库列表"""
        filters = {}
        if kb_type:
            filters["kb_type"] = kb_type
        if keyword:
            filters["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}}
            ]
        return await self.list(page, page_size, filters, "created_at", -1)


class McpService(BaseService):
    """MCP 服务器服务"""

    def __init__(self):
        super().__init__("mcp_servers")

    async def create_server(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建 MCP 服务器"""
        server_data["tool_count"] = 0
        return await self.create(server_data)

    async def update_server(self, server_id: str, server_data: Dict[str, Any]) -> bool:
        """更新 MCP 服务器"""
        return await self.update(server_id, server_data)

    async def list_servers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询服务器列表"""
        filters = {}
        if status:
            filters["status"] = status
        if keyword:
            filters["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}}
            ]
        return await self.list(page, page_size, filters, "created_at", -1)


class SkillService(BaseService):
    """技能服务"""

    def __init__(self):
        super().__init__("skills")

    async def create_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建技能"""
        from app.agent.skills.loader import load_skill_from_db
        skill_data = load_skill_from_db(skill_data)
        skill_data["id"] = await self.create(skill_data)
        return skill_data

    async def update_skill(self, skill_id: str, skill_data: Dict[str, Any]) -> bool:
        """更新技能"""
        from app.agent.skills.loader import load_skill_from_db
        skill_data = load_skill_from_db(skill_data)
        return await self.update(skill_id, skill_data)

    async def enable_skill(self, skill_id: str) -> bool:
        """启用技能"""
        return await self.update(skill_id, {"enabled": True})

    async def disable_skill(self, skill_id: str) -> bool:
        """禁用技能"""
        return await self.update(skill_id, {"enabled": False})

    async def list_skills(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询技能列表"""
        filters = {}
        if category:
            filters["category"] = category
        if keyword:
            filters["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}}
            ]
        return await self.list(page, page_size, filters, "priority", -1)

    async def get_skills_by_ids(self, skill_ids: list) -> list:
        """根据 ID 列表获取技能"""
        from bson import ObjectId
        from app.agent.skills.loader import load_skill_from_db

        if not skill_ids:
            return []

        skills = []
        cursor = self.collection.find({
            "_id": {"$in": [ObjectId(sid) for sid in skill_ids]},
            "enabled": True
        })
        async for skill in cursor:
            skill["id"] = str(skill.pop("_id"))
            skill = load_skill_from_db(skill)
            skills.append(skill)
        return skills


class AgentService(BaseService):
    """Agent 服务"""

    def __init__(self):
        super().__init__("agents")

    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建 Agent"""
        return await self.create(agent_data)

    async def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> bool:
        """更新 Agent"""
        return await self.update(agent_id, agent_data)

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取单个 Agent"""
        from bson import ObjectId
        try:
            agent = await self.collection.find_one({"_id": ObjectId(agent_id)})
            if agent:
                agent["id"] = str(agent.pop("_id"))
            return agent
        except Exception:
            return None

    async def list_agents(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """分页查询 Agent 列表"""
        filters = {}
        if keyword:
            filters["$or"] = [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}}
            ]
        return await self.list(page, page_size, filters, "sort_order", 1)

    async def init_default_agents(self) -> None:
        """初始化默认 Agent"""
        existing = await self.count({})
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
            await self.create(agent_data)
        logger.info("默认 Agent 初始化完成")


# 全局实例
llm_service = LlmService()
llm_config_service = LlmConfigService()
knowledge_base_service = KnowledgeBaseService()
mcp_service = McpService()
skill_service = SkillService()
agent_service = AgentService()
