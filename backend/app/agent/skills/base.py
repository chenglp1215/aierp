from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class SkillContext(BaseModel):
    user_id: str
    agent_id: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class SkillResult(BaseModel):
    success: bool
    content: str
    skill_name: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseSkill(ABC):
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    enabled: bool = True
    priority: int = 5
    content: str = ""

    @abstractmethod
    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        pass

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority
        }


class DynamicSkill(BaseSkill):
    """从 md 文档动态加载的 Skill"""

    def __init__(self, skill_data: Dict[str, Any]):
        self.name = skill_data.get("name", "unknown")
        self.description = skill_data.get("description", "")
        self.parameters = skill_data.get("parameters", {})
        self.enabled = skill_data.get("enabled", True)
        self.priority = skill_data.get("priority", 5)
        self.content = skill_data.get("content", "")
        self.config = skill_data.get("config", {})

    async def execute(self, context: SkillContext, **kwargs) -> SkillResult:
        message = kwargs.get("message", "")

        try:
            logger.info(f"DynamicSkill {self.name} executed for user {context.user_id}")

            response = self.content or f"[DynamicSkill: {self.name}] 技能执行中..."

            return SkillResult(
                success=True,
                content=response,
                skill_name=self.name,
                metadata={"message": message}
            )

        except Exception as e:
            logger.error(f"DynamicSkill {self.name} execution failed: {e}")
            return SkillResult(
                success=False,
                content="",
                skill_name=self.name,
                error=str(e)
            )
