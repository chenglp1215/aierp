from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class LLMConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    default_model: str = "gpt-4"
    api_base_url: str = ""
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 8192
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    streaming: bool = True
    timeout: int = 60
    retry_count: int = 3


class ModelConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    name: str
    model_type: str
    status: str = "active"
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
