import logging
from typing import Optional, Dict, Any, List

from .agent import Agent, AgentConfig
from .llm import llm_client
from .tools import tool_registry, BaseTool

logger = logging.getLogger(__name__)


class AgentManager:
    _instance = None
    _agents: Dict[str, Agent] = {}
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        if self._initialized:
            return

        logger.info("Initializing AgentManager...")

        await llm_client.load_config()

        await self._register_builtin_components()

        await self._load_agents()

        self._initialized = True
        logger.info("AgentManager initialized successfully")

    async def _register_builtin_components(self) -> None:
        from .tools.builtin import register_business_tools
        register_business_tools()
        await self._register_skills_from_db()

    async def _register_skills_from_db(self) -> None:
        from services.ai_service import skill_service
        from app.agent.tools.registry import SkillAsTool

        try:
            result = await skill_service.list_skills(page=1, page_size=1000)
            items = result.get("items", [])
            for skill_data in items:
                if skill_data.get("enabled", False):
                    skill_tool = SkillAsTool(skill_data)
                    tool_registry.register(skill_tool)
                    logger.info(f"Registered skill as tool: {skill_tool.name}")
            logger.info(f"Loaded {len(items)} skills from database")
        except Exception as e:
            logger.error(f"Failed to load skills from database: {e}")

    async def reload_agents(self) -> None:
        self._agents.clear()
        tool_registry.clear()
        await self._register_builtin_components()
        await self._load_agents()
        logger.info("Agents reloaded")

    async def _load_agents(self) -> None:
        from services.ai_service import agent_service

        try:
            result = await agent_service.list_agents(1, 100)
            items = result.get("items", [])

            for agent_data in items:
                if not agent_data.get("enabled", True):
                    continue

                config = AgentConfig(
                    id=agent_data["id"],
                    name=agent_data["name"],
                    system_prompt=agent_data.get("system_prompt", ""),
                    description=agent_data.get("description"),
                    skill_ids=agent_data.get("skill_ids", []),
                    mcp_server_ids=agent_data.get("mcp_server_ids", []),
                    enabled=agent_data.get("enabled", True),
                    tools_range=agent_data.get("tools_range", [])
                )

                agent = Agent(config)
                await agent.initialize()
                self._agents[config.id] = agent

            logger.info(f"Loaded {len(self._agents)} agents")

        except Exception as e:
            logger.error(f"Failed to load agents: {e}")

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def get_agent_by_name(self, agent_name: str) -> Optional[Agent]:
        for agent in self._agents.values():
            if agent.config.name == agent_name:
                return agent
        return None

    def get_all_agents(self) -> List[Agent]:
        return list(self._agents.values())

    def register_tool(self, tool: BaseTool) -> None:
        tool_registry.register(tool)
        logger.info(f"Registered tool: {tool.name}")

    def unregister_tool(self, name: str) -> None:
        tool_registry.unregister(name)
        logger.info(f"Unregistered tool: {name}")


agent_manager = AgentManager()
