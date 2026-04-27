from typing import Any, Dict, Optional
import logging

from app.agent.tools.base import BaseTool, ToolResult
from services.product_service import product_service

logger = logging.getLogger(__name__)


class ProductSearchTool(BaseTool):
    name = "product_search"
    cn_name = "搜索商品"
    description = "搜索商品信息。当用户询问商品、价格、库存、产品列表等问题时使用。"
    permission_code = "product.view"
    parameters = {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "搜索关键词（商品名称、编号、品牌）",
                "example": "iPhone"
            },
            "status": {
                "type": "string",
                "description": "商品状态筛选：active(在售)、inactive(下架)、archived(归档)",
                "default": "active",
                "example": "active"
            },
            "page": {
                "type": "integer",
                "description": "页码，默认1",
                "default": 1,
                "example": 1
            },
            "page_size": {
                "type": "integer",
                "description": "每页数量，默认20",
                "default": 20,
                "example": 20
            }
        },
        "required": []
    }

    async def execute(
        self,
        keyword: Optional[str] = None,
        status: str = "active",
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Product search: keyword={keyword}, status={status}, page={page}")

            result = await product_service.list_products(
                page=page,
                page_size=page_size,
                status=status,
                keyword=keyword
            )

            items = result.get("items", [])
            if not items:
                return ToolResult(
                    success=True,
                    content="未找到商品记录",
                    metadata={"total": 0}
                )

            content_lines = [f"共找到 {result.get('total', 0)} 个商品："]
            for product in items[:10]:
                content_lines.append(
                    f"[商品编码:{product.get('product_code', 'N/A')}] "
                    f"[ID:{product.get('id', 'N/A')}] "
                    f"名称: {product.get('name', 'N/A')} | "
                    f"品牌: {product.get('brand', 'N/A')} | "
                    f"价格: ¥{product.get('price', 0)} | "
                    f"规格: {product.get('packaging_spec', 'N/A')}"
                )

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata={"total": result.get("total", 0)}
            )

        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class ProductStatsTool(BaseTool):
    name = "product_stats"
    cn_name = "商品统计"
    description = "获取商品统计信息。当用户询问商品总数、在售商品数量、下架商品数量等统计类问题时使用。"
    permission_code = "product.view"
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def execute(self, **kwargs) -> ToolResult:
        try:
            stats = await product_service.get_product_stats()

            content_lines = ["商品统计信息："]
            content_lines.append(f"总商品数: {stats.get('total', 0)}")
            content_lines.append(f"在售商品: {stats.get('active_count', 0)}")
            content_lines.append(f"已下架: {stats.get('inactive_count', 0)}")

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata=stats
            )

        except Exception as e:
            logger.error(f"Product stats query failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


def register_product_tools():
    from app.agent import agent_manager

    agent_manager.register_tool(ProductSearchTool())
    agent_manager.register_tool(ProductStatsTool())
    logger.info("Product tools registered")
