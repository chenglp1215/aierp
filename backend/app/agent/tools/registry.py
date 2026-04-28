from typing import Dict, Callable, Any, List
from .base import BaseTool, ToolResult


class ToolRegistry:
    _instance = None
    _tools: Dict[str, BaseTool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError("Tool name cannot be empty")
        self._tools[tool.name] = tool

    def register_skill_as_tool(self, skill_data: Dict[str, Any]) -> None:
        skill_name = skill_data.get("name", "")
        if not skill_name:
            return
        skill_tool = SkillAsTool(skill_data)
        self._tools[skill_name] = skill_tool

    def unregister(self, name: str) -> None:
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> BaseTool:
        return self._tools.get(name)

    def get_all(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_tools(self, tools_range, user_permissions: List[str] = None) -> List[Dict[str, Any]]:
        if tools_range is None:
            return self._tools.values()
        elif len(tools_range) == 0:
            return []

        tools = [t for t in self._tools.values() if t.name in tools_range]
        if user_permissions is not None:
            tools = [t for t in tools if not getattr(t, 'permission_code', '') or getattr(t, 'permission_code', '') in user_permissions]
        return tools

    def get_tools_by_permissions(self, user_permissions: List[str] = None) -> List[BaseTool]:
        if user_permissions is None:
            return list(self._tools.values())
        return [t for t in self._tools.values() if not getattr(t, 'permission_code', '') or getattr(t, 'permission_code', '') in user_permissions]

    def has(self, name: str) -> bool:
        return name in self._tools

    def clear(self) -> None:
        self._tools.clear()


class SkillAsTool(BaseTool):
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    permission_code: str = ""

    def __init__(self, skill_data: Dict[str, Any]):
        self.name = skill_data.get("name", "")
        self.description = skill_data.get("description", "")
        self.parameters = skill_data.get("parameters", {})
        self.permission_code = skill_data.get("permission_code", "")
        self.content = skill_data.get("content", "")
        self.enabled = skill_data.get("enabled", True)

    async def execute(self, **kwargs) -> ToolResult:
        from app.agent.skills import SkillContext, SkillResult
        message = kwargs.get("message", "")

        try:
            result_content = self.content or f"[Skill: {self.name}] 执行完成"
            return ToolResult(
                success=True,
                content=result_content,
                metadata={"skill_name": self.name}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )


tool_registry = ToolRegistry()
