from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    name: str = ""
    cn_name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    permission_code: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        pass

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            },
        }

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        required_fields = self.parameters.get("required", [])
        if not required_fields:
            return True, None

        for field in required_fields:
            if field not in params or params[field] is None:
                return False, f"缺少必填参数: {field}"
            if isinstance(params[field], list) and len(params[field]) == 0:
                return False, f"参数 {field} 不能为空列表"

        return True, None

    async def execute_with_validation(self, **kwargs) -> ToolResult:
        valid, error_msg = self.validate_params(kwargs)
        if not valid:
            return ToolResult(success=False, content="", error=error_msg)
        return await self.execute(**kwargs)
