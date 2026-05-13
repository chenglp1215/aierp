from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class AgentConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    name: str
    system_prompt: str = ""
    description: Optional[str] = None
    skill_ids: List[str] = []
    mcp_server_ids: List[str] = []
    enabled: bool = True
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools_range: List[str] = []
