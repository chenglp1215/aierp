from typing import Any, Dict, Optional
import logging

from app.agent.tools.base import BaseTool, ToolResult
from services.inventory_service import warehouse_service, stock_service

logger = logging.getLogger(__name__)


class StockSearchTool(BaseTool):
    name = "stock_search"
    cn_name = "搜索库存"
    description = "搜索库存。当用户询问库存情况、查看库存列表、搜索库存商品时使用。"
    permission_code = "inventory.stock.view"
    parameters = {
        "type": "object",
        "properties": {
            "warehouse_id": {
                "type": "string",
                "description": "仓库ID",
                "example": "60f1b2c3d4e5f6a7b8c9d0e1"
            },
            "product_id": {
                "type": "string",
                "description": "商品ID",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            },
            "status": {
                "type": "string",
                "description": "库存状态筛选：normal(正常)、low_stock(库存不足)、out_of_stock(缺货)、overstock(超额)",
                "example": "normal"
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
        product_id: Optional[str] = None,
        status: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Stock search: warehouse_id={warehouse_id}, product_id={product_id}, status={status}")

            result = await stock_service.list_stocks(
                page=page,
                page_size=page_size,
                warehouse_id=warehouse_id,
                product_id=product_id,
                status=status,
            )

            items = result.get("items", [])
            if not items:
                return ToolResult(
                    success=True,
                    content="未找到库存记录",
                    metadata={"total": 0}
                )

            content_lines = [f"共找到 {result.get('total', 0)} 条库存记录："]
            for stock in items[:10]:
                content_lines.append(
                    f"[ID:{stock.get('id', 'N/A')}] "
                    f"商品: {stock.get('product_name', 'N/A')} | "
                    f"[商品ID:{stock.get('product_id', 'N/A')}] "
                    f"仓库: {stock.get('warehouse_name', 'N/A')} | "
                    f"[仓库ID:{stock.get('warehouse_id', 'N/A')}] "
                    f"数量: {stock.get('quantity', 0)} | "
                    f"状态: {stock.get('status', 'N/A')}"
                )

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata={"total": result.get("total", 0)}
            )

        except Exception as e:
            logger.error(f"Stock search failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class StockStatsTool(BaseTool):
    name = "stock_stats"
    cn_name = "获取库存统计"
    description = "获取库存统计信息。当用户询问库存统计、库存汇总、库存预警等统计类问题时使用。"
    permission_code = "inventory.stock.view"
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def execute(self, **kwargs) -> ToolResult:
        try:
            logger.info("Stock stats query")

            stats = await stock_service.get_stock_stats()

            content_lines = ["库存统计信息："]
            content_lines.append(f"总库存记录数: {stats.get('total', 0)}")
            content_lines.append(f"正常库存: {stats.get('normal', 0)}")
            content_lines.append(f"库存不足: {stats.get('low_stock', 0)}")
            content_lines.append(f"缺货: {stats.get('out_of_stock', 0)}")
            content_lines.append(f"超额库存: {stats.get('overstock', 0)}")

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata=stats
            )

        except Exception as e:
            logger.error(f"Stock stats query failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class WarehouseSearchTool(BaseTool):
    name = "warehouse_search"
    cn_name = "搜索仓库"
    description = "搜索仓库。当用户询问仓库信息、查找仓库列表时使用。"
    permission_code = "warehouse.view"
    parameters = {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "搜索关键词（仓库编码、仓库名称、管理员）",
                "example": "深圳仓"
            },
            "status": {
                "type": "string",
                "description": "仓库状态筛选：active(活跃)、inactive(不活跃)",
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
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Warehouse search: keyword={keyword}")

            result = await warehouse_service.list_warehouses(
                page=page,
                page_size=page_size,
                status=status,
                keyword=keyword
            )

            items = result.get("items", [])
            if not items:
                return ToolResult(
                    success=True,
                    content="未找到仓库记录",
                    metadata={"total": 0}
                )

            content_lines = [f"共找到 {result.get('total', 0)} 个仓库："]
            for warehouse in items[:10]:
                content_lines.append(
                    f"[仓库编码:{warehouse.get('warehouse_code', 'N/A')}] "
                    f"[仓库ID:{warehouse.get('id', 'N/A')}] "
                    f"名称: {warehouse.get('name', 'N/A')} | "
                    f"地址: {warehouse.get('address', 'N/A')} | "
                    f"管理员: {warehouse.get('manager_name', 'N/A')} | "
                    f"状态: {warehouse.get('status', 'N/A')}"
                )

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata={"total": result.get("total", 0)}
            )

        except Exception as e:
            logger.error(f"Warehouse search failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


def register_inventory_tools():
    from app.agent import agent_manager
    agent_manager.register_tool(StockSearchTool())
    agent_manager.register_tool(StockStatsTool())
    agent_manager.register_tool(WarehouseSearchTool())
    logger.info("Inventory tools registered")
