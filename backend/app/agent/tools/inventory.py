from typing import Any, Dict, Optional
import logging

from app.agent.tools.base import BaseTool, ToolResult
from services.inventory_service import warehouse_service, stock_service

logger = logging.getLogger(__name__)


class WarehouseSearchTool(BaseTool):
    name = "warehouse_search"
    cn_name = "搜索仓库"
    description = "搜索仓库信息。当用户询问仓库、仓库列表、仓库管理等问题时使用。"
    permission_code = "warehouse.view"
    parameters = {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "搜索关键词（仓库名称、编码、负责人）",
                "example": "深圳"
            },
            "status": {
                "type": "string",
                "description": "仓库状态筛选：active(活跃)、inactive(停用)",
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
            logger.info(f"Werehouse search: keyword={keyword}, status={status}")

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
            for wh in items[:10]:
                content_lines.append(
                    f"[仓库编码:{wh.get('warehouse_code', 'N/A')}] "
                    f"名称: {wh.get('name', 'N/A')} | "
                    f"负责人: {wh.get('manager_name', 'N/A')} | "
                    f"地址: {wh.get('address', 'N/A')}"
                )

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata={"total": result.get("total", 0)}
            )

        except Exception as e:
            logger.error(f"Werehouse search failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class WarehouseCreateTool(BaseTool):
    name = "warehouse_create"
    cn_name = "创建仓库"
    description = "创建新仓库。当用户要求新建仓库、添加仓库时使用。"
    permission_code = "warehouse.create"
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "仓库名称（必填）",
                "example": "深圳仓库"
            },
            "address": {
                "type": "string",
                "description": "仓库地址（必填）",
                "example": "深圳市南山区科技园"
            },
            "manager_name": {
                "type": "string",
                "description": "仓库负责人姓名",
                "example": "张三"
            },
            "manager_id": {
                "type": "string",
                "description": "仓库负责人工号",
                "example": "MGR001"
            },
            "contact_phone": {
                "type": "string",
                "description": "仓库联系电话",
                "example": "0755-12345678"
            },
            "remarks": {
                "type": "string",
                "description": "备注",
                "example": "主仓库"
            }
        },
        "required": ["name", "address"]
    }

    async def execute(
        self,
        name: str,
        address: str,
        manager_name: Optional[str] = None,
        manager_id: Optional[str] = None,
        contact_phone: Optional[str] = None,
        remarks: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Werehouse create: name={name}")

            from models.inventory import WarehouseCreate
            warehouse_data = WarehouseCreate(
                name=name,
                address=address,
                manager_name=manager_name,
                manager_id=manager_id,
                contact_phone=contact_phone,
                remarks=remarks
            )

            is_valid, errors = warehouse_service.validate_warehouse_create(warehouse_data)
            if not is_valid:
                error_msg = self._format_validation_errors(errors)
                return ToolResult(success=False, content=f"仓库创建参数验证失败: {error_msg}")

            result = await warehouse_service.create_warehouse(warehouse_data)

            return ToolResult(
                success=True,
                content=f"仓库创建成功！仓库编码: {result.get('warehouse_code', '')}",
                metadata={"warehouse_id": result.get("id", ""), "warehouse_code": result.get("warehouse_code", "")}
            )

        except Exception as e:
            logger.exception(f"Werehouse create failed: {e}")
            return ToolResult(success=False, content="", error=str(e))

    def _format_validation_errors(self, errors: Dict[str, list]) -> str:
        lines = []
        for field, msgs in errors.items():
            lines.append(f"{field}: {', '.join(msgs)}")
        return "; ".join(lines)


class WarehouseUpdateTool(BaseTool):
    name = "warehouse_update"
    cn_name = "更新仓库"
    description = "更新仓库信息。当用户要求修改仓库信息、更新仓库资料时使用。"
    permission_code = "warehouse.edit"
    parameters = {
        "type": "object",
        "properties": {
            "warehouse_code": {
                "type": "string",
                "description": "仓库编码（必填）",
                "example": "WH202401010001"
            },
            "name": {
                "type": "string",
                "description": "仓库名称",
                "example": "深圳仓库"
            },
            "address": {
                "type": "string",
                "description": "仓库地址",
                "example": "深圳市福田区"
            },
            "manager_name": {
                "type": "string",
                "description": "仓库负责人姓名",
                "example": "李四"
            },
            "manager_id": {
                "type": "string",
                "description": "仓库负责人工号",
                "example": "MGR002"
            },
            "contact_phone": {
                "type": "string",
                "description": "仓库联系电话",
                "example": "0755-87654321"
            },
            "remarks": {
                "type": "string",
                "description": "备注",
                "example": "副仓库"
            }
        },
        "required": ["warehouse_code"]
    }

    async def execute(
        self,
        warehouse_code: str,
        name: Optional[str] = None,
        address: Optional[str] = None,
        manager_name: Optional[str] = None,
        manager_id: Optional[str] = None,
        contact_phone: Optional[str] = None,
        remarks: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Werehouse update: warehouse_code={warehouse_code}")

            from models.inventory import WarehouseUpdate
            update_data = WarehouseUpdate()
            if name is not None:
                update_data.name = name
            if address is not None:
                update_data.address = address
            if manager_name is not None:
                update_data.manager_name = manager_name
            if manager_id is not None:
                update_data.manager_id = manager_id
            if contact_phone is not None:
                update_data.contact_phone = contact_phone
            if remarks is not None:
                update_data.remarks = remarks

            is_valid, errors = warehouse_service.validate_warehouse_update(update_data)
            if not is_valid:
                error_msg = self._format_validation_errors(errors)
                return ToolResult(success=False, content=f"仓库更新参数验证失败: {error_msg}")

            success = await warehouse_service.update_warehouse(warehouse_code, update_data)

            if success:
                return ToolResult(success=True, content="仓库信息更新成功")
            else:
                return ToolResult(success=False, content="仓库信息更新失败，仓库不存在")

        except Exception as e:
            logger.exception(f"Werehouse update failed: {e}")
            return ToolResult(success=False, content="", error=str(e))

    def _format_validation_errors(self, errors: Dict[str, list]) -> str:
        lines = []
        for field, msgs in errors.items():
            lines.append(f"{field}: {', '.join(msgs)}")
        return "; ".join(lines)


class StockCreateTool(BaseTool):
    name = "stock_create"
    cn_name = "创建库存记录"
    description = "创建库存记录。当用户要求添加库存、创建库存台账时使用。"
    permission_code = "stock.create"
    parameters = {
        "type": "object",
        "properties": {
            "spec_id": {
                "type": "string",
                "description": "商品规格ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            },
            "warehouse_id": {
                "type": "string",
                "description": "仓库ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e3"
            },
            "quantity": {
                "type": "number",
                "description": "库存数量（必填，最小0）",
                "example": 100
            },
            "min_stock": {
                "type": "number",
                "description": "最低库存警戒线",
                "example": 10
            },
            "max_stock": {
                "type": "number",
                "description": "最高库存警戒线",
                "example": 1000
            }
        },
        "required": ["spec_id", "warehouse_id", "quantity"]
    }

    async def execute(
        self,
        spec_id: str,
        warehouse_id: str,
        quantity: float,
        min_stock: Optional[float] = None,
        max_stock: Optional[float] = None,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Stock create: spec_id={spec_id}, warehouse_id={warehouse_id}, quantity={quantity}")

            from models.inventory import StockCreate
            stock_data = StockCreate(
                spec_id=spec_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                min_stock=min_stock,
                max_stock=max_stock
            )

            is_valid, errors = stock_service.validate_stock_create(stock_data)
            if not is_valid:
                error_msg = self._format_validation_errors(errors)
                return ToolResult(success=False, content=f"库存创建参数验证失败: {error_msg}")

            result = await stock_service.create_stock(stock_data)

            return ToolResult(
                success=True,
                content=f"库存记录创建成功！",
                metadata={"stock_id": result.get("id", "")}
            )

        except Exception as e:
            logger.exception(f"Stock create failed: {e}")
            return ToolResult(success=False, content="", error=str(e))

    def _format_validation_errors(self, errors: Dict[str, list]) -> str:
        lines = []
        for field, msgs in errors.items():
            lines.append(f"{field}: {', '.join(msgs)}")
        return "; ".join(lines)


class StockUpdateTool(BaseTool):
    name = "stock_update"
    cn_name = "更新库存"
    description = "更新库存信息。当用户要求修改库存数量、调整库存时使用。"
    permission_code = "stock.edit"
    parameters = {
        "type": "object",
        "properties": {
            "stock_id": {
                "type": "string",
                "description": "库存记录ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e4"
            },
            "quantity": {
                "type": "number",
                "description": "库存数量（最小0）",
                "example": 150
            },
            "min_stock": {
                "type": "number",
                "description": "最低库存警戒线",
                "example": 20
            },
            "max_stock": {
                "type": "number",
                "description": "最高库存警戒线",
                "example": 2000
            }
        },
        "required": ["stock_id"]
    }

    async def execute(
        self,
        stock_id: str,
        quantity: Optional[float] = None,
        min_stock: Optional[float] = None,
        max_stock: Optional[float] = None,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Stock update: stock_id={stock_id}")

            from models.inventory import StockUpdate
            update_data = StockUpdate()
            if quantity is not None:
                update_data.quantity = quantity
            if min_stock is not None:
                update_data.min_stock = min_stock
            if max_stock is not None:
                update_data.max_stock = max_stock

            is_valid, errors = stock_service.validate_stock_update(update_data)
            if not is_valid:
                error_msg = self._format_validation_errors(errors)
                return ToolResult(success=False, content=f"库存更新参数验证失败: {error_msg}")

            success = await stock_service.update_stock(stock_id, update_data)

            if success:
                return ToolResult(success=True, content="库存更新成功")
            else:
                return ToolResult(success=False, content="库存更新失败，库存记录不存在")

        except Exception as e:
            logger.exception(f"Stock update failed: {e}")
            return ToolResult(success=False, content="", error=str(e))

    def _format_validation_errors(self, errors: Dict[str, list]) -> str:
        lines = []
        for field, msgs in errors.items():
            lines.append(f"{field}: {', '.join(msgs)}")
        return "; ".join(lines)


class StockStatsTool(BaseTool):
    name = "stock_stats"
    cn_name = "库存统计"
    description = "获取库存统计信息。当用户询问库存数量、库存状态、库存预警等统计类问题时使用。"
    permission_code = "stock.view"
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def execute(self, **kwargs) -> ToolResult:
        try:
            stats = await stock_service.get_stock_stats()

            content_lines = ["库存统计信息："]
            content_lines.append(f"总库存记录数: {stats.get('total', 0)}")
            content_lines.append(f"正常库存: {stats.get('normal', 0)}")
            content_lines.append(f"低库存预警: {stats.get('low_stock', 0)}")
            content_lines.append(f"缺货: {stats.get('out_of_stock', 0)}")
            content_lines.append(f"超库存: {stats.get('overstock', 0)}")

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata=stats
            )

        except Exception as e:
            logger.error(f"Stock stats query failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


def register_inventory_tools():
    from app.agent import agent_manager

    agent_manager.register_tool(WarehouseSearchTool())
    agent_manager.register_tool(WarehouseCreateTool())
    agent_manager.register_tool(WarehouseUpdateTool())
    agent_manager.register_tool(StockCreateTool())
    agent_manager.register_tool(StockUpdateTool())
    agent_manager.register_tool(StockStatsTool())
    logger.info("Inventory tools registered")
