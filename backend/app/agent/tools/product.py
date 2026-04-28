from typing import Any, Dict, List, Optional
import logging

from app.agent.tools.base import BaseTool, ToolResult
from services.product_service import product_service, product_spec_service

logger = logging.getLogger(__name__)


def format_validation_errors(errors: Dict[str, list]) -> str:
    lines = [f"{field}: {', '.join(msgs)}" for field, msgs in errors.items()]
    return "; ".join(lines)


def format_product_list(items: List[Dict], total: int, max_display: int = 10) -> str:
    if not items:
        return "未找到商品记录"

    lines = [f"共找到 {total} 个商品："]
    for product in items[:max_display]:
        spec_count = len(product.get("specs", []))
        lines.append(
            f"[商品编码:{product.get('product_code', 'N/A')}] "
            f"[ID:{product.get('id', 'N/A')}] "
            f"名称: {product.get('name', 'N/A')} | "
            f"品牌: {product.get('brand', 'N/A')} | "
            f"规格数: {spec_count}"
        )
    return "\n".join(lines)


def format_product_detail(product: Dict) -> str:
    lines = [
        f"商品详情：",
        f"商品编码: {product.get('product_code', 'N/A')}",
        f"名称: {product.get('name', 'N/A')}",
        f"品牌: {product.get('brand', 'N/A')}",
        f"分类: {product.get('category', 'N/A')}",
        f"图片: {product.get('image_url', 'N/A')}",
        f"税务编码: {product.get('tax_code', 'N/A')}",
        f"创建时间: {product.get('created_at', 'N/A')}",
        f"更新时间: {product.get('updated_at', 'N/A')}",
    ]

    specs = product.get("specs", [])
    if specs:
        lines.append(f"\n规格列表（共 {len(specs)} 个）：")
        for spec in specs:
            lines.append(
                f"  [规格ID:{spec.get('id', 'N/A')}] "
                f"规格编码: {spec.get('spec_code', 'N/A')} | "
                f"价格: {spec.get('price', 'N/A')} | "
                f"包装: {spec.get('packaging', 'N/A')} | "
                f"销售规格: {spec.get('sales_spec', 'N/A')} | "
                f"库存: {spec.get('stock_quantity', 0)} | "
                f"状态: {spec.get('stock_status', 'N/A')}"
            )
    else:
        lines.append("\n暂无规格")

    return "\n".join(lines)


def format_spec_list(items: List[Dict], total: int, max_display: int = 10) -> str:
    if not items:
        return "未找到规格记录"

    lines = [f"共找到 {total} 个规格："]
    for spec in items[:max_display]:
        lines.append(
            f"[规格ID:{spec.get('id', 'N/A')}] "
            f"[商品ID:{spec.get('product_id', 'N/A')}] "
            f"规格编码: {spec.get('spec_code', 'N/A')} | "
            f"价格: {spec.get('price', 'N/A')} | "
            f"包装: {spec.get('packaging', 'N/A')} | "
            f"库存: {spec.get('stock_quantity', 0)}"
        )
    return "\n".join(lines)


def format_spec_detail(spec: Dict) -> str:
    return (
        f"规格详情：\n"
        f"规格ID: {spec.get('id', 'N/A')}\n"
        f"商品ID: {spec.get('product_id', 'N/A')}\n"
        f"规格编码: {spec.get('spec_code', 'N/A')}\n"
        f"价格: {spec.get('price', 'N/A')}\n"
        f"包装: {spec.get('packaging', 'N/A')}\n"
        f"销售规格: {spec.get('sales_spec', 'N/A')}\n"
        f"CAS号: {spec.get('cas_number', 'N/A')}\n"
        f"是否有效: {spec.get('is_active', True)}\n"
        f"库存数量: {spec.get('stock_quantity', 0)}\n"
        f"库存状态: {spec.get('stock_status', 'N/A')}\n"
        f"创建时间: {spec.get('created_at', 'N/A')}\n"
        f"更新时间: {spec.get('updated_at', 'N/A')}"
    )


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
    ) -> str:
        try:
            logger.info(f"Product search: keyword={keyword}, status={status}, page={page}")

            result = await product_service.list_products(
                page=page,
                page_size=page_size,
                keyword=keyword
            )

            items = result.get("items", [])
            content = format_product_list(items, result.get("total", 0))

            return ToolResult(
                success=True,
                content=content,
                metadata={"total": result.get("total", 0)}
            ).model_dump_json()

        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductDetailTool(BaseTool):
    name = "product_detail"
    cn_name = "商品详情"
    description = "查看商品详细信息及规格。当用户要求查看具体商品、了解商品详情时使用。"
    permission_code = "product.view"
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "商品ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            }
        },
        "required": ["product_id"]
    }

    async def execute(self, product_id: str, **kwargs) -> str:
        try:
            logger.info(f"Product detail: product_id={product_id}")

            product = await product_service.get_product_with_specs(product_id)
            if not product:
                return ToolResult(success=False, content="商品不存在").model_dump_json()

            content = format_product_detail(product)
            return ToolResult(success=True, content=content, metadata={"product_id": product_id}).model_dump_json()

        except Exception as e:
            logger.error(f"Product detail failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductCreateTool(BaseTool):
    name = "product_create"
    cn_name = "创建商品"
    description = "创建新商品。当用户要求新建商品、添加商品时使用。"
    permission_code = "product.create"
    parameters = {
        "type": "object",
        "properties": {
            "product_code": {
                "type": "string",
                "description": "商品编号（只能包含字母、数字、横线和下划线）",
                "example": "PROD-001"
            },
            "name": {
                "type": "string",
                "description": "商品名称（必填）",
                "example": "iPhone 15"
            },
            "image_url": {
                "type": "string",
                "description": "商品图片URL",
                "example": "https://example.com/iphone15.jpg"
            },
            "brand": {
                "type": "string",
                "description": "品牌",
                "example": "Apple"
            },
            "category": {
                "type": "string",
                "description": "分类",
                "example": "手机"
            },
            "tax_code": {
                "type": "string",
                "description": "税务编码",
                "example": "TAX001"
            }
        },
        "required": ["name"]
    }

    async def execute(
        self,
        name: str,
        product_code: Optional[str] = None,
        image_url: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        tax_code: Optional[str] = None,
        **kwargs
    ) -> str:
        try:
            logger.info(f"Product create: name={name}")

            from models.product import ProductCreate
            product_data = ProductCreate(
                product_code=product_code or "",
                name=name,
                image_url=image_url,
                brand=brand,
                category=category,
                tax_code=tax_code
            )

            is_valid, errors = product_service.validate_product_create(product_data)
            if not is_valid:
                return ToolResult(
                    success=False,
                    content=f"商品创建参数验证失败: {format_validation_errors(errors)}"
                ).model_dump_json()

            result = await product_service.create_product(product_data)

            return ToolResult(
                success=True,
                content=f"商品创建成功！商品编码: {result.get('product_code', '')}",
                metadata={"product_id": result.get("id", ""), "product_code": result.get("product_code", "")}
            ).model_dump_json()

        except Exception as e:
            logger.exception(f"Product create failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductUpdateTool(BaseTool):
    name = "product_update"
    cn_name = "更新商品"
    description = "更新商品信息。当用户要求修改商品信息、更新商品资料时使用。"
    permission_code = "product.edit"
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "商品ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            },
            "name": {
                "type": "string",
                "description": "商品名称",
                "example": "iPhone 15 Pro"
            },
            "product_code": {
                "type": "string",
                "description": "商品编号",
                "example": "PROD-002"
            },
            "image_url": {
                "type": "string",
                "description": "商品图片URL",
                "example": "https://example.com/iphone15pro.jpg"
            },
            "brand": {
                "type": "string",
                "description": "品牌",
                "example": "Apple"
            },
            "category": {
                "type": "string",
                "description": "分类",
                "example": "手机"
            }
        },
        "required": ["product_id"]
    }

    async def execute(
        self,
        product_id: str,
        name: Optional[str] = None,
        product_code: Optional[str] = None,
        image_url: Optional[str] = None,
        brand: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs
    ) -> str:
        try:
            logger.info(f"Product update: product_id={product_id}")

            from models.product import ProductUpdate
            update_data = ProductUpdate(
                name=name,
                product_code=product_code,
                image_url=image_url,
                brand=brand,
                category=category
            )

            is_valid, errors = product_service.validate_product_update(update_data)
            if not is_valid:
                return ToolResult(
                    success=False,
                    content=f"商品更新参数验证失败: {format_validation_errors(errors)}"
                ).model_dump_json()

            success = await product_service.update_product(product_id, update_data)
            content = "商品信息更新成功" if success else "商品信息更新失败，商品不存在"

            return ToolResult(success=success, content=content).model_dump_json()

        except Exception as e:
            logger.exception(f"Product update failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductDeleteTool(BaseTool):
    name = "product_delete"
    cn_name = "删除商品"
    description = "删除商品。当用户要求删除商品、移除商品时使用。"
    permission_code = "product.delete"
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "商品ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            }
        },
        "required": ["product_id"]
    }

    async def execute(self, product_id: str, **kwargs) -> str:
        try:
            logger.info(f"Product delete: product_id={product_id}")

            product = await product_service.get_by_id(product_id)
            if not product:
                return ToolResult(success=False, content="商品不存在").model_dump_json()

            success = await product_service.delete(product_id)
            content = "商品删除成功" if success else "商品删除失败"

            return ToolResult(success=success, content=content).model_dump_json()

        except Exception as e:
            logger.exception(f"Product delete failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductSpecSearchTool(BaseTool):
    name = "product_spec_search"
    cn_name = "搜索商品规格"
    description = "搜索商品规格。当用户询问规格、价格列表、规格详情时使用。"
    permission_code = "product.view"
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "商品ID（可填，筛选指定商品的规格）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            },
            "product_keyword": {
                "type": "string",
                "description": "商品编码关键词（可填，筛选指定商品的规格，支持模糊匹配）",
                "example": "PROD2026"
            },
            "keyword": {
                "type": "string",
                "description": "规格编号关键词（模糊匹配规格编号）",
                "example": "SPEC-001"
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
        product_keyword: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> str:
        try:
            logger.info(f"Product spec search: product_id={product_id}, product_keyword={product_keyword}, keyword={keyword}")

            result = await product_spec_service.list_specs(
                page=page,
                page_size=page_size,
                product_id=product_id,
                product_keyword=product_keyword,
                keyword=keyword
            )

            items = result.get("items", [])
            content = format_spec_list(items, result.get("total", 0))

            return ToolResult(
                success=True,
                content=content,
                metadata={"total": result.get("total", 0)}
            ).model_dump_json()

        except Exception as e:
            logger.error(f"Product spec search failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductSpecDetailTool(BaseTool):
    name = "product_spec_detail"
    cn_name = "规格详情"
    description = "查看单个商品规格的详细信息。"
    permission_code = "product.view"
    parameters = {
        "type": "object",
        "properties": {
            "spec_id": {
                "type": "string",
                "description": "规格ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e3"
            }
        },
        "required": ["spec_id"]
    }

    async def execute(self, spec_id: str, **kwargs) -> str:
        try:
            logger.info(f"Product spec detail: spec_id={spec_id}")

            spec = await product_spec_service.get_by_id(spec_id)
            if not spec:
                return ToolResult(success=False, content="规格不存在").model_dump_json()

            spec["stock_quantity"] = 0
            specs_enriched = await product_spec_service._enrich_stock_status([spec])
            spec = specs_enriched[0] if specs_enriched else spec

            content = format_spec_detail(spec)
            return ToolResult(success=True, content=content, metadata={"spec_id": spec_id}).model_dump_json()

        except Exception as e:
            logger.error(f"Product spec detail failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductSpecCreateTool(BaseTool):
    name = "product_spec_create"
    cn_name = "创建商品规格"
    description = "创建商品规格。当用户要求为商品添加规格、规格报价时使用。"
    permission_code = "product.create"
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "商品ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            },
            "spec_code": {
                "type": "string",
                "description": "规格编号",
                "example": "SPEC-001"
            },
            "price": {
                "type": "number",
                "description": "价格（必填）",
                "example": 5999.00
            },
            "packaging": {
                "type": "string",
                "description": "包装规格",
                "example": "1台/盒"
            },
            "sales_spec": {
                "type": "string",
                "description": "销售规格",
                "example": "128GB/太空灰"
            },
            "cas_number": {
                "type": "string",
                "description": "CAS号",
                "example": "68917-21-1"
            }
        },
        "required": ["product_id", "price"]
    }

    async def execute(
        self,
        product_id: str,
        price: float,
        spec_code: Optional[str] = None,
        packaging: Optional[str] = None,
        sales_spec: Optional[str] = None,
        cas_number: Optional[str] = None,
        **kwargs
    ) -> str:
        try:
            logger.info(f"Product spec create: product_id={product_id}, price={price}")

            from models.product import ProductSpecCreate
            spec_data = ProductSpecCreate(
                spec_code=spec_code or "",
                price=price,
                packaging=packaging,
                sales_spec=sales_spec,
                cas_number=cas_number
            )

            is_valid, errors = product_spec_service.validate_spec_create(spec_data)
            if not is_valid:
                return ToolResult(
                    success=False,
                    content=f"规格创建参数验证失败: {format_validation_errors(errors)}"
                ).model_dump_json()

            spec_data.product_id = product_id
            result = await product_spec_service.create_spec(spec_data)

            return ToolResult(
                success=True,
                content=f"商品规格创建成功！规格编码: {result.get('spec_code', '')}",
                metadata={"spec_id": result.get("id", ""), "spec_code": result.get("spec_code", "")}
            ).model_dump_json()

        except Exception as e:
            logger.exception(f"Product spec create failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductSpecUpdateTool(BaseTool):
    name = "product_spec_update"
    cn_name = "更新商品规格"
    description = "更新商品规格。当用户要求修改规格信息、价格调整时使用。"
    permission_code = "product.edit"
    parameters = {
        "type": "object",
        "properties": {
            "spec_id": {
                "type": "string",
                "description": "规格ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e3"
            },
            "spec_code": {
                "type": "string",
                "description": "规格编号",
                "example": "SPEC-002"
            },
            "price": {
                "type": "number",
                "description": "价格",
                "example": 5499.00
            },
            "packaging": {
                "type": "string",
                "description": "包装规格",
                "example": "2台/盒"
            },
            "sales_spec": {
                "type": "string",
                "description": "销售规格",
                "example": "256GB/金色"
            },
            "cas_number": {
                "type": "string",
                "description": "CAS号",
                "example": "68917-21-2"
            },
            "is_active": {
                "type": "boolean",
                "description": "是否有效",
                "example": True
            }
        },
        "required": ["spec_id"]
    }

    async def execute(
        self,
        spec_id: str,
        spec_code: Optional[str] = None,
        price: Optional[float] = None,
        packaging: Optional[str] = None,
        sales_spec: Optional[str] = None,
        cas_number: Optional[str] = None,
        is_active: Optional[bool] = None,
        **kwargs
    ) -> str:
        try:
            logger.info(f"Product spec update: spec_id={spec_id}")

            from models.product import ProductSpecUpdate
            update_data = ProductSpecUpdate(
                spec_code=spec_code,
                price=price,
                packaging=packaging,
                sales_spec=sales_spec,
                cas_number=cas_number,
                is_active=is_active
            )

            is_valid, errors = product_spec_service.validate_spec_update(update_data)
            if not is_valid:
                return ToolResult(
                    success=False,
                    content=f"规格更新参数验证失败: {format_validation_errors(errors)}"
                ).model_dump_json()

            success = await product_spec_service.update_spec(spec_id, update_data)
            content = "规格信息更新成功" if success else "规格信息更新失败"

            return ToolResult(success=success, content=content).model_dump_json()

        except Exception as e:
            logger.exception(f"Product spec update failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


class ProductSpecDeleteTool(BaseTool):
    name = "product_spec_delete"
    cn_name = "删除商品规格"
    description = "删除商品规格。当用户要求删除规格、移除规格时使用。"
    permission_code = "product.delete"
    parameters = {
        "type": "object",
        "properties": {
            "spec_id": {
                "type": "string",
                "description": "规格ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e3"
            }
        },
        "required": ["spec_id"]
    }

    async def execute(self, spec_id: str, **kwargs) -> str:
        try:
            logger.info(f"Product spec delete: spec_id={spec_id}")

            spec = await product_spec_service.get_by_id(spec_id)
            if not spec:
                return ToolResult(success=False, content="规格不存在").model_dump_json()

            success = await product_spec_service.delete_spec(spec_id)
            content = "规格删除成功" if success else "规格删除失败"

            return ToolResult(success=success, content=content).model_dump_json()

        except Exception as e:
            logger.exception(f"Product spec delete failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


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

    async def execute(self, **kwargs) -> str:
        try:
            stats = await product_service.get_product_stats()

            content_lines = [
                "商品统计信息：",
                f"总商品数: {stats.get('total', 0)}",
                f"总规格数: {stats.get('total_specs', 0)}",
                f"总库存: {stats.get('total_stock', 0)}"
            ]

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata=stats
            ).model_dump_json()

        except Exception as e:
            logger.error(f"Product stats query failed: {e}")
            return ToolResult(success=False, content="", error=str(e)).model_dump_json()


def register_product_tools():
    from app.agent import agent_manager

    agent_manager.register_tool(ProductSearchTool())
    agent_manager.register_tool(ProductDetailTool())
    agent_manager.register_tool(ProductCreateTool())
    agent_manager.register_tool(ProductUpdateTool())
    agent_manager.register_tool(ProductDeleteTool())
    agent_manager.register_tool(ProductSpecSearchTool())
    agent_manager.register_tool(ProductSpecDetailTool())
    agent_manager.register_tool(ProductSpecCreateTool())
    agent_manager.register_tool(ProductSpecUpdateTool())
    agent_manager.register_tool(ProductSpecDeleteTool())
    agent_manager.register_tool(ProductStatsTool())
    logger.info("Product tools registered")
