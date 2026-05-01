"""
商品管理 - API路由
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional

from models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductListResponse,
    ProductSpec,
    ProductSpecCreate,
    ProductSpecUpdate,
    ProductSpecListResponse,
)
from services.product_service import product_service, product_spec_service
from .auth import require_permission
from app.decorators import handle_result, success_response, error_response

product_router = APIRouter(prefix="/products", tags=["商品管理"])


@product_router.post("/", response_model=dict, status_code=201)
async def create_product(
    product: ProductCreate,
    _: dict = Depends(require_permission("product.create"))
):
    """创建商品"""
    try:
        product_data = await product_service.create_product(product)
        return success_response("商品创建成功", product_data)
    except ValueError as e:
        return error_response(str(e))


@product_router.get("/", response_model=dict)
async def list_products(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    brand_id: Optional[str] = Query(None, description="品牌ID"),
    category_id: Optional[str] = Query(None, description="分类ID"),
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品列表（包含所有规格）"""
    result = await product_service.list_products(
        page=page,
        page_size=page_size,
        keyword=keyword,
        brand_id=brand_id,
        category_id=category_id
    )
    return success_response(result=result)


@product_router.get("/stats", response_model=dict)
async def get_product_stats(_: dict = Depends(require_permission("product.view"))):
    """获取商品统计信息"""
    stats = await product_service.get_product_stats()
    return success_response(result=stats)


@product_router.get("/search", response_model=dict)
async def search_products(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("product.view"))
):
    """搜索商品（用于下拉选择等）"""
    items = await product_service.search_products(keyword, limit)
    return success_response(result=items)


@product_router.get("/{product_id}", response_model=dict)
async def get_product(
    product_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品详情（包含规格列表）"""
    product = await product_service.get_product_with_specs(product_id)
    if not product:
        return error_response("商品不存在")
    return success_response(result=product)


@product_router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    _: dict = Depends(require_permission("product.edit"))
):
    """更新商品信息"""
    try:
        success = await product_service.update_product(product_id, product)
        return handle_result(success, "商品更新成功", "商品不存在或更新失败")
    except ValueError as e:
        return error_response(str(e))


@product_router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: str,
    _: dict = Depends(require_permission("product.delete"))
):
    """删除商品（同时删除关联规格）"""
    success = await product_service.delete(product_id)
    if not success:
        return error_response("商品不存在或删除失败")

    await product_spec_service.delete_many({"product_id": product_id})

    return success_response("商品删除成功")


@product_router.get("/{product_id}/specs", response_model=dict)
async def list_product_specs(
    product_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品的所有规格"""
    result = await product_spec_service.list_specs(
        page=page,
        page_size=page_size,
        product_id=product_id
    )
    return success_response(result=result)


@product_router.post("/{product_id}/specs", response_model=dict, status_code=201)
async def create_product_spec(
    product_id: str,
    spec: ProductSpecCreate,
    _: dict = Depends(require_permission("product.create"))
):
    """为商品创建规格"""
    product = await product_service.get_by_id(product_id)
    if not product:
        return error_response("商品不存在")

    spec_data = spec.model_dump()
    spec_data["product_id"] = product_id

    spec_create = ProductSpecCreate(**spec_data)
    spec_data = await product_spec_service.create_spec(spec_create)

    return success_response("规格创建成功", spec_data)


@product_router.get("/specs/search", response_model=dict)
async def search_specs(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("product.view"))
):
    """搜索商品规格（用于下拉选择等），返回规格及其关联的商品信息"""
    items = await product_spec_service.search_specs(keyword, limit)
    return success_response(result=items)


@product_router.get("/specs/{spec_id}", response_model=dict)
async def get_spec(
    spec_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取规格详情"""
    spec = await product_spec_service.get_by_id(spec_id)
    if not spec:
        return error_response("规格不存在")
    return success_response(result=spec)


@product_router.put("/specs/{spec_id}", response_model=dict)
async def update_spec(
    spec_id: str,
    spec: ProductSpecUpdate,
    _: dict = Depends(require_permission("product.edit"))
):
    """更新规格信息"""
    success = await product_spec_service.update_spec(spec_id, spec)
    return handle_result(success, "规格更新成功", "规格不存在或更新失败")


@product_router.delete("/specs/{spec_id}", response_model=dict)
async def delete_spec(
    spec_id: str,
    _: dict = Depends(require_permission("product.delete"))
):
    """删除规格"""
    success = await product_spec_service.delete_spec(spec_id)
    return handle_result(success, "规格删除成功", "规格不存在或删除失败")


@product_router.patch("/specs/{spec_id}/toggle-active", response_model=dict)
async def toggle_spec_active(
    spec_id: str,
    is_active: bool = Query(..., description="是否激活"),
    _: dict = Depends(require_permission("product.edit"))
):
    """切换规格激活状态"""
    success = await product_spec_service.toggle_spec_active(spec_id, is_active)
    return handle_result(success, f"规格已{'激活' if is_active else '停用'}", "规格不存在或更新失败")


@product_router.get("/specs/{spec_id}/stock-detail", response_model=dict)
async def get_spec_stock_detail(
    spec_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取规格库存明细"""
    items = await product_service.get_product_stock_detail(spec_id)
    total = sum(item.get("quantity", 0) for item in items)
    return success_response(result={"items": items, "total_quantity": total})


@product_router.get("/all-specs/", response_model=dict)
async def list_all_specs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="规格编号关键词（模糊匹配）"),
    product_keyword: Optional[str] = Query(None, description="商品编码关键词（模糊匹配，筛选指定商品的规格）"),
    _: dict = Depends(require_permission("product.view"))
):
    """获取所有规格列表，支持按规格编号或商品编码搜索"""
    result = await product_spec_service.list_specs(
        page=page,
        page_size=page_size,
        keyword=keyword,
        product_keyword=product_keyword
    )
    return success_response(result=result)
