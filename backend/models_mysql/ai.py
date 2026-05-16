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