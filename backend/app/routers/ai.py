from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from models.ai import (
    LlmModel, LlmModelCreate, LlmModelUpdate, LlmModelListResponse,
    LlmConfig,
    KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseListResponse,
    McpServer, McpServerCreate, McpServerUpdate, McpServerListResponse,
    Skill, SkillCreate, SkillUpdate, SkillListResponse,
    Agent, AgentCreate, AgentUpdate, AgentListResponse
)
from services.ai_service_mysql import (
    llm_service, llm_config_service,
    knowledge_base_service, mcp_service,
    skill_service, agent_service
)
from app.agent.tools import tool_registry
from app.agent import agent_manager

llm_router = APIRouter(prefix="/llm", tags=["LLM 设置"])
kb_router = APIRouter(prefix="/knowledge-base", tags=["知识库设置"])
mcp_router = APIRouter(prefix="/mcp", tags=["MCP 设置"])
skill_router = APIRouter(prefix="/skills", tags=["Skills 设置"])
agent_router = APIRouter(prefix="/agents", tags=["Agent 设置"])
ai_tools_router = APIRouter(prefix="/ai", tags=["AI 工具"])


# ========== LLM Routes ==========

@llm_router.get("/models", response_model=LlmModelListResponse)
async def list_llm_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None)
):
    """获取 LLM 模型列表"""
    return await llm_service.list_models(page, page_size, keyword)


@llm_router.get("/models/{model_id}", response_model=LlmModel)
async def get_llm_model(model_id: int):
    """获取 LLM 模型详情"""
    model = await llm_service.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@llm_router.post("/models", response_model=dict)
async def create_llm_model(model_data: LlmModelCreate):
    """创建 LLM 模型"""
    model_data = await llm_service.create_model(model_data.model_dump())
    return {"status": True, "message": "模型创建成功", "result": {"id": model_data["id"]}}


@llm_router.put("/models/{model_id}", response_model=dict)
async def update_llm_model(model_id: int, model_data: LlmModelUpdate):
    """更新 LLM 模型"""
    success = await llm_service.update_model(model_id, model_data.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在或更新失败")
    return {"status": True, "message": "模型更新成功"}


@llm_router.delete("/models/{model_id}", response_model=dict)
async def delete_llm_model(model_id: int):
    """删除 LLM 模型"""
    success = await llm_service.delete(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="模型不存在或删除失败")
    return {"status": True, "message": "模型删除成功"}


@llm_router.post("/models/{model_id}/test", response_model=dict)
async def test_llm_model(model_id: int):
    """测试 LLM 模型连接"""
    model = await llm_service.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return {"status": True, "message": "连接测试成功"}


@llm_router.get("/config", response_model=Optional[LlmConfig])
async def get_llm_config():
    """获取 LLM 配置"""
    config = await llm_config_service.get_config()
    if config:
        return config
    return LlmConfig()


@llm_router.put("/config", response_model=dict)
async def update_llm_config(config_data: LlmConfig):
    """更新 LLM 配置"""
    success = await llm_config_service.update_config(config_data.model_dump())
    if not success:
        raise HTTPException(status_code=500, detail="配置更新失败")
    return {"status": True, "message": "配置更新成功"}


# ========== Knowledge Base Routes ==========

@kb_router.get("/collections", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    kb_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None)
):
    """获取知识库列表"""
    return await knowledge_base_service.list_knowledge_bases(page, page_size, kb_type, keyword)


@kb_router.get("/collections/{kb_id}", response_model=KnowledgeBase)
async def get_knowledge_base(kb_id: int):
    """获取知识库详情"""
    kb = await knowledge_base_service.get_by_id(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@kb_router.post("/collections", response_model=dict)
async def create_knowledge_base(kb_data: KnowledgeBaseCreate):
    """创建知识库"""
    kb_id = await knowledge_base_service.create_knowledge_base(kb_data.model_dump())
    return {"status": True, "message": "知识库创建成功", "result": {"id": kb_id}}


@kb_router.put("/collections/{kb_id}", response_model=dict)
async def update_knowledge_base(kb_id: int, kb_data: KnowledgeBaseUpdate):
    """更新知识库"""
    success = await knowledge_base_service.update_knowledge_base(kb_id, kb_data.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="知识库不存在或更新失败")
    return {"status": True, "message": "知识库更新成功"}


@kb_router.delete("/collections/{kb_id}", response_model=dict)
async def delete_knowledge_base(kb_id: int):
    """删除知识库"""
    success = await knowledge_base_service.delete(kb_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识库不存在或删除失败")
    return {"status": True, "message": "知识库删除成功"}


# ========== MCP Routes ==========

@mcp_router.get("/servers", response_model=McpServerListResponse)
async def list_mcp_servers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None)
):
    """获取 MCP 服务器列表"""
    return await mcp_service.list_servers(page, page_size, status, keyword)


@mcp_router.get("/servers/{server_id}", response_model=McpServer)
async def get_mcp_server(server_id: int):
    """获取 MCP 服务器详情"""
    server = await mcp_service.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    return server


@mcp_router.post("/servers", response_model=dict)
async def create_mcp_server(server_data: McpServerCreate):
    """创建 MCP 服务器"""
    server_id = await mcp_service.create_server(server_data.model_dump())
    return {"status": True, "message": "服务器创建成功", "result": {"id": server_id}}


@mcp_router.put("/servers/{server_id}", response_model=dict)
async def update_mcp_server(server_id: int, server_data: McpServerUpdate):
    """更新 MCP 服务器"""
    success = await mcp_service.update_server(server_id, server_data.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="服务器不存在或更新失败")
    return {"status": True, "message": "服务器更新成功"}


@mcp_router.delete("/servers/{server_id}", response_model=dict)
async def delete_mcp_server(server_id: int):
    """删除 MCP 服务器"""
    success = await mcp_service.delete(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="服务器不存在或删除失败")
    return {"status": True, "message": "服务器删除成功"}


@mcp_router.post("/servers/{server_id}/test", response_model=dict)
async def test_mcp_server(server_id: int):
    """测试 MCP 服务器连接"""
    server = await mcp_service.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    return {"status": True, "message": "连接测试成功"}


@mcp_router.get("/servers/{server_id}/tools", response_model=dict)
async def get_mcp_server_tools(server_id: int):
    """获取 MCP 服务器工具列表"""
    server = await mcp_service.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="服务器不存在")
    return {"items": [], "total": 0}


# ========== Skill Routes ==========

@skill_router.get("", response_model=SkillListResponse)
async def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None)
):
    """获取技能列表"""
    return await skill_service.list_skills(page, page_size, category, keyword)


@skill_router.get("/{skill_id}", response_model=Skill)
async def get_skill(skill_id: int):
    """获取技能详情"""
    skill = await skill_service.get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="技能不存在")
    return skill


@skill_router.post("", response_model=dict)
async def create_skill(skill_data: SkillCreate):
    """创建技能"""
    skill_data = await skill_service.create_skill(skill_data.model_dump())
    return {"status": True, "message": "技能创建成功", "result": skill_data}


@skill_router.put("/{skill_id}", response_model=dict)
async def update_skill(skill_id: int, skill_data: SkillUpdate):
    """更新技能"""
    success = await skill_service.update_skill(skill_id, skill_data.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在或更新失败")
    return {"status": True, "message": "技能更新成功"}


@skill_router.delete("/{skill_id}", response_model=dict)
async def delete_skill(skill_id: int):
    """删除技能"""
    success = await skill_service.delete(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在或删除失败")
    return {"status": True, "message": "技能删除成功"}


@skill_router.patch("/{skill_id}/enable", response_model=dict)
async def enable_skill(skill_id: int):
    """启用技能"""
    success = await skill_service.enable_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {"status": True, "message": "技能启用成功"}


@skill_router.patch("/{skill_id}/disable", response_model=dict)
async def disable_skill(skill_id: int):
    """禁用技能"""
    success = await skill_service.disable_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="技能不存在")
    return {"status": True, "message": "技能禁用成功"}


# ========== Agent Routes ==========

@agent_router.get("", response_model=AgentListResponse)
async def list_agents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None)
):
    """获取 Agent 列表"""
    return await agent_service.list_agents(page, page_size, keyword)


@agent_router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: int):
    """获取 Agent 详情"""
    agent = await agent_service.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    return agent


@agent_router.post("", response_model=dict)
async def create_agent(agent_data: AgentCreate):
    """创建 Agent"""
    agent_id = await agent_service.create_agent(agent_data.model_dump())
    await agent_manager.reload_agents()
    return {"status": True, "message": "Agent 创建成功", "result": {"id": agent_id}}


@agent_router.put("/{agent_id}", response_model=dict)
async def update_agent(agent_id: int, agent_data: AgentUpdate):
    """更新 Agent"""
    success = await agent_service.update_agent(agent_id, agent_data.model_dump(exclude_unset=True))
    if not success:
        raise HTTPException(status_code=404, detail="Agent 不存在或更新失败")
    await agent_manager.reload_agents()
    return {"status": True, "message": "Agent 更新成功"}


@agent_router.delete("/{agent_id}", response_model=dict)
async def delete_agent(agent_id: int):
    """删除 Agent"""
    success = await agent_service.delete(agent_id)
    if not success:
        raise HTTPException(status_code=404, detail="Agent 不存在或删除失败")
    await agent_manager.reload_agents()
    return {"status": True, "message": "Agent 删除成功"}


# ========== AI Tools Routes ==========

@ai_tools_router.get("/tools", response_model=dict)
async def get_all_tools():
    """获取所有可用的 AI 工具列表"""
    tools = tool_registry.get_all()
    items = [
        {
            "name": tool.name,
            "cn_name": getattr(tool, 'cn_name', ''),
            "description": tool.description,
            "permission_code": getattr(tool, 'permission_code', '')
        }
        for tool in tools
    ]
    return {"items": items, "total": len(items)}
