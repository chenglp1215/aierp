from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductListResponse,
    ProductStatus,
)
from services.product_service import product_service
from .auth import get_current_active_user, require_permission

product_router = APIRouter(prefix="/products", tags=["商品管理"])


@product_router.post("/", response_model=dict, status_code=201)
async def create_product(
    product: ProductCreate,
    _: dict = Depends(require_permission("product.create"))
):
    """创建商品"""
    product_id = await product_service.create_product(product)
    return {
        "status": "success",
        "message": "商品创建成功",
        "result": {"id": product_id}
    }


@product_router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="商品状态"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品列表"""
    result = await product_service.list_products(
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword
    )
    return result


@product_router.get("/stats", response_model=dict)
async def get_product_stats(_: dict = Depends(require_permission("product.view"))):
    """获取商品统计信息"""
    stats = await product_service.get_product_stats()
    return {
        "status": "success",
        "result": stats
    }


@product_router.get("/search", response_model=dict)
async def search_products(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("product.view"))
):
    """搜索商品（用于下拉选择等）"""
    items = await product_service.search_products(keyword, limit)
    return {
        "status": "success",
        "result": items
    }


@product_router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品详情"""
    product = await product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    return product


@product_router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: str,
    product: ProductUpdate,
    _: dict = Depends(require_permission("product.edit"))
):
    """更新商品信息"""
    success = await product_service.update_product(product_id, product)
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在或更新失败")
    return {
        "status": "success",
        "message": "商品更新成功"
    }


@product_router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: str,
    _: dict = Depends(require_permission("product.delete"))
):
    """删除商品"""
    success = await product_service.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在或删除失败")
    return {
        "status": "success",
        "message": "商品删除成功"
    }


@product_router.patch("/{product_id}/status", response_model=dict)
async def update_product_status(
    product_id: str,
    status: ProductStatus,
    _: dict = Depends(require_permission("product.edit"))
):
    """更新商品状态"""
    success = await product_service.update_status(product_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="商品不存在或状态更新失败")
    return {
        "status": "success",
        "message": "商品状态更新成功"
    }
