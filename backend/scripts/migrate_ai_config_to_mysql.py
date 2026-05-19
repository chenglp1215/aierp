"""
AI 智能配置数据迁移脚本 - MongoDB 到 MySQL
迁移内容：LlmModel、LlmConfig、KnowledgeBase、McpServer、Skill、Agent
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from tortoise import Tortoise
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.settings import settings
from models_mysql.ai import (
    LlmModel, LlmConfig, LlmModelType, LlmModelStatus,
    KnowledgeBase, KnowledgeBaseType,
    McpServer, McpServerType, McpServerStatus,
    Skill, SkillCategory,
    Agent
)


async def get_mongo_client():
    """获取 MongoDB 客户端"""
    mongo_url = settings.MONGO_URL
    client = AsyncIOMotorClient(mongo_url)
    return client


async def init_tortoise():
    """初始化 Tortoise ORM"""
    await Tortoise.init(
        db_url=f"mysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
        modules={"models": ["models_mysql.ai"]},
    )
    await Tortoise.generate_schemas()


# ========== ID 映射表 ==========
# 用于存储 MongoDB ObjectId 到 MySQL 整数 ID 的映射
id_mappings: Dict[str, Dict[str, int]] = {
    "llm_models": {},
    "knowledge_bases": {},
    "mcp_servers": {},
    "skills": {},
    "agents": {},
}


async def migrate_llm_models(db) -> Dict[str, int]:
    """迁移 LLM 模型"""
    collection = db["llm_models"]
    mapping: Dict[str, int] = {}

    total = await collection.count_documents({})
    print(f"\n[LLM 模型] MongoDB 总数: {total}")

    success = 0
    skip = 0
    error = 0

    cursor = collection.find({})
    async for doc in cursor:
        try:
            mongo_id = str(doc.get("_id"))
            name = doc.get("name")

            if not name:
                skip += 1
                continue

            # 检查是否已存在
            existing = await LlmModel.filter(name=name).first()
            if existing:
                mapping[mongo_id] = existing.id
                skip += 1
                continue

            # 映射模型类型
            model_type_str = doc.get("model_type", "openai")
            model_type = LlmModelType.OPENAI
            if model_type_str in ["anthropic", "ANTHROPIC"]:
                model_type = LlmModelType.ANTHROPIC
            elif model_type_str in ["azure", "AZURE"]:
                model_type = LlmModelType.AZURE
            elif model_type_str in ["custom", "CUSTOM"]:
                model_type = LlmModelType.CUSTOM

            # 映射状态
            status_str = doc.get("status", "active")
            status = LlmModelStatus.ACTIVE if status_str == "active" else LlmModelStatus.INACTIVE

            model = await LlmModel.create(
                name=name,
                model_type=model_type,
                status=status,
            )
            mapping[mongo_id] = model.id
            success += 1

        except Exception as e:
            print(f"  迁移失败: {doc.get('name')}, 错误: {e}")
            error += 1

    print(f"[LLM 模型] 成功: {success}, 跳过: {skip}, 失败: {error}")
    return mapping


async def migrate_llm_config(db) -> bool:
    """迁移 LLM 配置（单例）"""
    collection = db["llm_config"]

    total = await collection.count_documents({})
    print(f"\n[LLM 配置] MongoDB 总数: {total}")

    if total == 0:
        print("[LLM 配置] 无数据，跳过")
        return True

    # 检查是否已存在配置
    existing = await LlmConfig.first()
    if existing:
        print("[LLM 配置] 已存在，跳过")
        return True

    doc = await collection.find_one({})
    if doc:
        await LlmConfig.create(
            default_model=doc.get("default_model", ""),
            api_base_url=doc.get("api_base_url", ""),
            api_key=doc.get("api_key", ""),
            streaming=doc.get("streaming", True),
            timeout=doc.get("timeout", 60),
            retry_count=doc.get("retry_count", 3),
        )
        print("[LLM 配置] 迁移成功")

    return True


async def migrate_knowledge_bases(db) -> Dict[str, int]:
    """迁移知识库"""
    collection = db["knowledge_bases"]
    mapping: Dict[str, int] = {}

    total = await collection.count_documents({})
    print(f"\n[知识库] MongoDB 总数: {total}")

    success = 0
    skip = 0
    error = 0

    cursor = collection.find({})
    async for doc in cursor:
        try:
            mongo_id = str(doc.get("_id"))
            name = doc.get("name")

            if not name:
                skip += 1
                continue

            # 检查是否已存在
            existing = await KnowledgeBase.filter(name=name).first()
            if existing:
                mapping[mongo_id] = existing.id
                skip += 1
                continue

            # 映射知识库类型
            kb_type_str = doc.get("kb_type", "document")
            kb_type = KnowledgeBaseType.DOCUMENT
            if kb_type_str in ["qa", "QA"]:
                kb_type = KnowledgeBaseType.QA
            elif kb_type_str in ["web", "WEB"]:
                kb_type = KnowledgeBaseType.WEB

            kb = await KnowledgeBase.create(
                name=name,
                kb_type=kb_type,
                description=doc.get("description"),
                status=doc.get("status", "active"),
                document_count=doc.get("document_count", 0),
            )
            mapping[mongo_id] = kb.id
            success += 1

        except Exception as e:
            print(f"  迁移失败: {doc.get('name')}, 错误: {e}")
            error += 1

    print(f"[知识库] 成功: {success}, 跳过: {skip}, 失败: {error}")
    return mapping


async def migrate_mcp_servers(db) -> Dict[str, int]:
    """迁移 MCP 服务器"""
    collection = db["mcp_servers"]
    mapping: Dict[str, int] = {}

    total = await collection.count_documents({})
    print(f"\n[MCP 服务器] MongoDB 总数: {total}")

    success = 0
    skip = 0
    error = 0

    cursor = collection.find({})
    async for doc in cursor:
        try:
            mongo_id = str(doc.get("_id"))
            name = doc.get("name")

            if not name:
                skip += 1
                continue

            # 检查是否已存在
            existing = await McpServer.filter(name=name).first()
            if existing:
                mapping[mongo_id] = existing.id
                skip += 1
                continue

            # 映射服务器类型
            server_type_str = doc.get("server_type", "http")
            server_type = McpServerType.HTTP
            if server_type_str in ["stdio", "STDIO"]:
                server_type = McpServerType.STDIO
            elif server_type_str in ["sse", "SSE"]:
                server_type = McpServerType.SSE

            # 映射状态
            status_str = doc.get("status", "active")
            status = McpServerStatus.ACTIVE
            if status_str == "inactive":
                status = McpServerStatus.INACTIVE
            elif status_str == "error":
                status = McpServerStatus.ERROR

            server = await McpServer.create(
                name=name,
                server_type=server_type,
                url=doc.get("url"),
                description=doc.get("description"),
                timeout=doc.get("timeout", 30),
                tool_count=doc.get("tool_count", 0),
                status=status,
            )
            mapping[mongo_id] = server.id
            success += 1

        except Exception as e:
            print(f"  迁移失败: {doc.get('name')}, 错误: {e}")
            error += 1

    print(f"[MCP 服务器] 成功: {success}, 跳过: {skip}, 失败: {error}")
    return mapping


async def migrate_skills(db) -> Dict[str, int]:
    """迁移技能"""
    collection = db["skills"]
    mapping: Dict[str, int] = {}

    total = await collection.count_documents({})
    print(f"\n[技能] MongoDB 总数: {total}")

    success = 0
    skip = 0
    error = 0

    cursor = collection.find({})
    async for doc in cursor:
        try:
            mongo_id = str(doc.get("_id"))
            name = doc.get("name")

            if not name:
                skip += 1
                continue

            # 检查是否已存在
            existing = await Skill.filter(name=name).first()
            if existing:
                mapping[mongo_id] = existing.id
                skip += 1
                continue

            # 映射技能分类
            category_str = doc.get("category", "tool")
            category = SkillCategory.TOOL
            if category_str in ["conversation", "CONVERSATION"]:
                category = SkillCategory.CONVERSATION
            elif category_str in ["workflow", "WORKFLOW"]:
                category = SkillCategory.WORKFLOW
            elif category_str in ["analysis", "ANALYSIS"]:
                category = SkillCategory.ANALYSIS

            skill = await Skill.create(
                name=name,
                description=doc.get("description"),
                category=category,
                enabled=doc.get("enabled", True),
                priority=doc.get("priority", 5),
                permission_code=doc.get("permission_code", ""),
                parameters=doc.get("parameters", {}),
                content=doc.get("content"),
                config=doc.get("config", {}),
            )
            mapping[mongo_id] = skill.id
            success += 1

        except Exception as e:
            print(f"  迁移失败: {doc.get('name')}, 错误: {e}")
            error += 1

    print(f"[技能] 成功: {success}, 跳过: {skip}, 失败: {error}")
    return mapping


async def migrate_agents(db, skill_mapping: Dict[str, int], mcp_mapping: Dict[str, int]) -> Dict[str, int]:
    """迁移 Agent"""
    collection = db["agents"]
    mapping: Dict[str, int] = {}

    total = await collection.count_documents({})
    print(f"\n[Agent] MongoDB 总数: {total}")

    success = 0
    skip = 0
    error = 0

    cursor = collection.find({})
    async for doc in cursor:
        try:
            mongo_id = str(doc.get("_id"))
            name = doc.get("name")

            if not name:
                skip += 1
                continue

            # 检查是否已存在
            existing = await Agent.filter(name=name).first()
            if existing:
                mapping[mongo_id] = existing.id
                skip += 1
                continue

            # 映射 skill_ids：MongoDB ObjectId -> MySQL 整数 ID
            old_skill_ids = doc.get("skill_ids", [])
            new_skill_ids = []
            for skill_oid in old_skill_ids:
                skill_oid_str = str(skill_oid)
                if skill_oid_str in skill_mapping:
                    new_skill_ids.append(skill_mapping[skill_oid_str])

            # 映射 mcp_server_ids：MongoDB ObjectId -> MySQL 整数 ID
            old_mcp_ids = doc.get("mcp_server_ids", [])
            new_mcp_ids = []
            for mcp_oid in old_mcp_ids:
                mcp_oid_str = str(mcp_oid)
                if mcp_oid_str in mcp_mapping:
                    new_mcp_ids.append(mcp_mapping[mcp_oid_str])

            agent = await Agent.create(
                name=name,
                description=doc.get("description"),
                system_prompt=doc.get("system_prompt", ""),
                skill_ids=new_skill_ids,
                mcp_server_ids=new_mcp_ids,
                tools_range=doc.get("tools_range", []),
                enabled=doc.get("enabled", True),
                sort_order=doc.get("sort_order", 0),
            )
            mapping[mongo_id] = agent.id
            success += 1

        except Exception as e:
            print(f"  迁移失败: {doc.get('name')}, 错误: {e}")
            error += 1

    print(f"[Agent] 成功: {success}, 跳过: {skip}, 失败: {error}")
    return mapping


async def main():
    """主迁移函数"""
    print("=" * 60)
    print("开始 AI 智能配置数据迁移...")
    print("=" * 60)

    # 初始化
    await init_tortoise()
    mongo_client = await get_mongo_client()
    db = mongo_client[settings.MONGO_DB_NAME]

    # 按依赖顺序迁移
    # 1. LLM 模型（无依赖）
    id_mappings["llm_models"] = await migrate_llm_models(db)

    # 2. LLM 配置（单例）
    await migrate_llm_config(db)

    # 3. 知识库（无依赖）
    id_mappings["knowledge_bases"] = await migrate_knowledge_bases(db)

    # 4. MCP 服务器（无依赖）
    id_mappings["mcp_servers"] = await migrate_mcp_servers(db)

    # 5. 技能（无依赖）
    id_mappings["skills"] = await migrate_skills(db)

    # 6. Agent（依赖技能和 MCP 服务器）
    id_mappings["agents"] = await migrate_agents(
        db,
        id_mappings["skills"],
        id_mappings["mcp_servers"]
    )

    # 输出最终统计
    print("\n" + "=" * 60)
    print("迁移完成! 最终统计:")
    print("=" * 60)

    # 验证 MySQL 数据
    llm_count = await LlmModel.all().count()
    kb_count = await KnowledgeBase.all().count()
    mcp_count = await McpServer.all().count()
    skill_count = await Skill.all().count()
    agent_count = await Agent.all().count()

    print(f"MySQL LLM 模型总数: {llm_count}")
    print(f"MySQL 知识库总数: {kb_count}")
    print(f"MySQL MCP 服务器总数: {mcp_count}")
    print(f"MySQL 技能总数: {skill_count}")
    print(f"MySQL Agent 总数: {agent_count}")

    print("\n" + "=" * 60)
    print("ID 映射表（MongoDB ObjectId -> MySQL 整数 ID）:")
    print("=" * 60)
    for entity_type, mapping in id_mappings.items():
        if mapping:
            print(f"\n{entity_type}:")
            for mongo_id, mysql_id in mapping.items():
                print(f"  {mongo_id} -> {mysql_id}")

    # 关闭连接
    mongo_client.close()
    await Tortoise.close_connections()

    print("\n迁移脚本执行完毕!")


if __name__ == "__main__":
    asyncio.run(main())