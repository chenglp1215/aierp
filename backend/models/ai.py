from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class LlmModelType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    CUSTOM = "custom"


class LlmModelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class LlmModel(BaseModel):
    id: str = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    model_type: LlmModelType = Field(..., description="模型类型")
    status: LlmModelStatus = Field(default=LlmModelStatus.ACTIVE, description="状态")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LlmModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    model_type: LlmModelType = Field(..., description="模型类型")
    status: LlmModelStatus = Field(default=LlmModelStatus.ACTIVE, description="状态")


class LlmModelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_type: Optional[LlmModelType] = None
    status: Optional[LlmModelStatus] = None


class LlmModelListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[LlmModel] = Field(..., description="模型列表")


class LlmConfig(BaseModel):
    default_model: str = Field(default="", description="默认模型")
    api_base_url: str = Field(default="", description="API Base URL")
    api_key: str = Field(default="", description="API Key")
    streaming: bool = Field(default=True, description="是否启用流式输出")
    timeout: int = Field(default=60, description="超时时间(秒)")
    retry_count: int = Field(default=3, description="重试次数")


class KnowledgeBaseType(str, Enum):
    DOCUMENT = "document"
    QA = "qa"
    WEB = "web"


class KnowledgeBase(BaseModel):
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    kb_type: KnowledgeBaseType = Field(..., description="知识库类型")
    description: Optional[str] = Field(None, description="描述")
    status: str = Field(default="active", description="状态")
    document_count: int = Field(default=0, description="文档数量")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="知识库名称")
    kb_type: KnowledgeBaseType = Field(..., description="知识库类型")
    description: Optional[str] = Field(None, description="描述")


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    kb_type: Optional[KnowledgeBaseType] = None
    description: Optional[str] = None


class KnowledgeBaseListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[KnowledgeBase] = Field(..., description="知识库列表")


class McpServerType(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class McpServerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class McpServer(BaseModel):
    id: str = Field(..., description="服务器ID")
    name: str = Field(..., description="服务器名称")
    server_type: McpServerType = Field(..., description="服务器类型")
    url: Optional[str] = Field(None, description="服务器URL")
    status: McpServerStatus = Field(default=McpServerStatus.ACTIVE, description="状态")
    description: Optional[str] = Field(None, description="描述")
    timeout: int = Field(default=30, description="超时时间")
    tool_count: int = Field(default=0, description="工具数量")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class McpServerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="服务器名称")
    server_type: McpServerType = Field(..., description="服务器类型")
    url: Optional[str] = Field(None, description="服务器URL")
    description: Optional[str] = Field(None, description="描述")
    timeout: int = Field(default=30, description="超时时间")


class McpServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    server_type: Optional[McpServerType] = None
    url: Optional[str] = None
    description: Optional[str] = None
    timeout: Optional[int] = None


class McpServerListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[McpServer] = Field(..., description="服务器列表")


class SkillCategory(str, Enum):
    CONVERSATION = "conversation"
    TOOL = "tool"
    WORKFLOW = "workflow"
    ANALYSIS = "analysis"


class SkillStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Skill(BaseModel):
    id: str = Field(..., description="技能ID")
    name: str = Field(..., description="技能名称")
    description: Optional[str] = Field(None, description="描述")
    category: SkillCategory = Field(..., description="分类")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=5, description="优先级(1-10)")
    permission_code: str = Field(default="", description="权限码(为空则所有用户可用)")
    parameters: Optional[dict] = Field(default={}, description="技能参数")
    content: Optional[str] = Field(None, description="技能内容(Markdown)")
    config: Optional[dict] = Field(None, description="技能配置")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="技能名称")
    description: Optional[str] = Field(None, description="描述")
    category: SkillCategory = Field(..., description="分类")
    enabled: bool = Field(default=True, description="是否启用")
    priority: int = Field(default=5, ge=1, le=10, description="优先级")
    permission_code: str = Field(default="", description="权限码(为空则所有用户可用)")
    parameters: Optional[dict] = Field(default={}, description="技能参数")
    content: Optional[str] = Field(None, description="技能内容(Markdown)")


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[SkillCategory] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    permission_code: Optional[str] = None
    parameters: Optional[dict] = None
    content: Optional[str] = None
    config: Optional[dict] = None


class SkillListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Skill] = Field(..., description="技能列表")


class Agent(BaseModel):
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent名称")
    description: Optional[str] = Field(None, description="描述")
    system_prompt: str = Field(default="", description="系统提示词")
    skill_ids: List[str] = Field(default=[], description="关联技能ID列表")
    mcp_server_ids: List[str] = Field(default=[], description="关联MCP服务器ID列表")
    tools_range: List[str] = Field(default=[], description="工具范围(为空则不使用任何工具)")
    enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序权重(越小越靠前)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Agent名称")
    description: Optional[str] = Field(None, description="描述")
    system_prompt: str = Field(default="", description="系统提示词")
    skill_ids: List[str] = Field(default=[], description="关联技能ID列表")
    mcp_server_ids: List[str] = Field(default=[], description="关联MCP服务器ID列表")
    tools_range: List[str] = Field(default=[], description="工具范围(为空则不使用任何工具)")
    enabled: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序权重")


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    skill_ids: Optional[List[str]] = None
    mcp_server_ids: Optional[List[str]] = None
    tools_range: Optional[List[str]] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = Field(None, description="排序权重")


class AgentListResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    items: List[Agent] = Field(..., description="Agent列表")
