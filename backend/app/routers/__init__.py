from fastapi import APIRouter
from .health import health_router
from .sales_order import sales_order_router
from .customer import customer_router
from .product import product_router
from .category import category_router
from .auth import auth_router
from .role import role_router
from .permission import permission_router
from .ai import llm_router, kb_router, mcp_router, skill_router, agent_router, ai_tools_router
from .inventory import warehouse_router, stock_router, inbound_router, outbound_router
from .procurement import procurement_router
from .accounts_receivable import accounts_receivable_router
from .ws import ws_router
from .upload import upload_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["健康检查"])
api_router.include_router(auth_router, tags=["认证"])
api_router.include_router(role_router, prefix="/auth", tags=["角色管理"])
api_router.include_router(permission_router, prefix="/auth", tags=["权限管理"])
api_router.include_router(sales_order_router, tags=["销售订单"])
api_router.include_router(customer_router, tags=["客户管理"])
api_router.include_router(product_router, tags=["商品管理"])
api_router.include_router(category_router, tags=["分类管理"])
api_router.include_router(procurement_router, tags=["采购单管理"])
api_router.include_router(accounts_receivable_router, tags=["应收款管理"])
api_router.include_router(llm_router, tags=["LLM 设置"])
api_router.include_router(kb_router, tags=["知识库设置"])
api_router.include_router(mcp_router, tags=["MCP 设置"])
api_router.include_router(skill_router, tags=["Skills 设置"])
api_router.include_router(agent_router, tags=["Agent 设置"])
api_router.include_router(ai_tools_router, tags=["AI 工具"])
api_router.include_router(warehouse_router, tags=["仓库管理"])
api_router.include_router(stock_router, tags=["库存管理"])
api_router.include_router(inbound_router, tags=["入库批次管理"])
api_router.include_router(outbound_router, tags=["出库批次管理"])
api_router.include_router(upload_router, tags=["文件上传"])
api_router.include_router(ws_router, prefix="/ws")
