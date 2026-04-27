from typing import Any, Dict
import logging

from app.agent.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class SearchKnowledgeBaseTool(BaseTool):
    name = "search_knowledge_base"
    cn_name = "搜索知识库"
    description = "搜索知识库获取相关信息。当用户询问产品信息、服务内容、公司政策等问题时使用。"
    permission_code = "knowledge.view"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索查询关键词",
                "example": "产品退货政策"
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 5,
                "example": 5
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, top_k: int = 5, **kwargs) -> ToolResult:
        try:
            logger.info(f"Searching knowledge base: query={query}, top_k={top_k}")

            return ToolResult(
                success=True,
                content=f"知识库搜索结果：关于「{query}」的信息。\n\n（这里应该连接实际的知识库服务返回真实数据）",
                metadata={"query": query, "count": 0}
            )

        except Exception as e:
            logger.error(f"Search knowledge base failed: {e}")
            return ToolResult(
                success=False,
                content="",
                error=str(e)
            )


def register_business_tools():
    from app.agent import agent_manager
    from app.agent.tools.sales_order import (
        register_sales_order_tools
    )
    from app.agent.tools.customer import (
        register_customer_tools
    )
    from app.agent.tools.inventory import (
        register_inventory_tools
    )
    from app.agent.tools.product import (
        register_product_tools
    )

    register_sales_order_tools()
    register_customer_tools()
    register_inventory_tools()
    register_product_tools()
    logger.info("Business tools registered")
