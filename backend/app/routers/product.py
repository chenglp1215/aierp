"""
商品管理 - API路由
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional, Dict, Any
from services.product_service import product_service, product_spec_service, brand_service, category_service
from .auth import require_permission
from app.decorators import wrap_response

brand_router = APIRouter(prefix="/brands", tags=["品牌管理"])
category_router = APIRouter(prefix="/categories", tags=["分类管理"])
product_router = APIRouter(prefix="/products", tags=["商品管理"])



@product_router.get("/specs/search", response_model=dict)
@wrap_response
async def search_specs(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("product.view"))
):
    """搜索商品规格（用于下拉选择等），返回规格及其关联的商品信息"""
    items, total = await product_spec_service.get_spec_by_keyword(keyword=keyword, page=1, page_size=limit, is_formatted=True)
    product_ids = list({s.get("product_id") for s in items if s.get("product_id")})
    products = await product_service.get_product_by_ids(product_ids)
    product_map = {p["id"]: p for p in products}
    enriched_items = []
    for spec in items:
        product = product_map.get(spec.get("product_id"), {})
        enriched_items.append({
            **spec,
            "product_name": product.get("name", ""),
            "product_code": product.get("product_code", ""),
        })
    return {
        "total": total,
        "items": enriched_items
    }


@product_router.get("/specs/{spec_id}", response_model=dict)
@wrap_response
async def get_spec(
    spec_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取规格详情"""
    spec = await product_spec_service.get_by_id(spec_id)
    if not spec:
        raise ValueError("规格不存在")
    return spec


@product_router.put("/specs/{spec_id}", response_model=dict)
@wrap_response
async def update_spec(
    spec_id: str,
    spec: Dict[str, Any],
    _: dict = Depends(require_permission("product.edit"))
):
    """更新规格信息"""
    await product_spec_service.update_spec(spec_id, spec)
    return "规格更新成功"


@product_router.delete("/specs/{spec_id}", response_model=dict)
@wrap_response
async def delete_spec(
    spec_id: str,
    _: dict = Depends(require_permission("product.delete"))
):
    """删除规格"""
    await product_spec_service.delete_spec(spec_id)
    return "规格删除成功"



@product_router.post("/", response_model=dict)
@wrap_response
async def create_product(
    product: Dict[str, Any],
    _: dict = Depends(require_permission("product.create"))
):
    """创建商品"""
    product_data = await product_service.create_product(product)
    return product_data


@product_router.get("/", response_model=dict)
@wrap_response
async def list_products(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    brand_id: Optional[str] = Query(None, description="品牌ID"),
    category_id: Optional[str] = Query(None, description="分类ID"),
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品列表（包含所有规格）"""
    products, total = await product_service.list_products(
        page=page,
        page_size=page_size,
        keyword=keyword,
        brand_id=brand_id,
        category_id=category_id,
        is_formatted=True
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": products
    }

@product_router.get("/{product_id}", response_model=dict)
@wrap_response
async def get_product(
    product_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品详情（包含规格列表）"""
    product = await product_service.get_product_by_id(product_id, is_formatted=True)
    return product


@product_router.put("/{product_id}", response_model=dict)
@wrap_response
async def update_product(
    product_id: str,
    product: Dict[str, Any],
    _: dict = Depends(require_permission("product.edit"))
):
    """更新商品信息"""
    await product_service.update_product(product_id, product)
    return "商品更新成功"


@product_router.delete("/{product_id}", response_model=dict)
@wrap_response
async def delete_product(
    product_id: str,
    _: dict = Depends(require_permission("product.delete"))
):
    """删除商品（同时删除关联规格）"""
    await product_service.delete_product(product_id)
    return "商品删除成功"


@product_router.get("/{product_id}/specs", response_model=dict)
@wrap_response
async def list_product_specs(
    product_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取商品的所有规格"""
    specs = await product_spec_service.get_spec_by_product_id(product_id=product_id, is_formatted=True)
    return {
        "total": len(specs),
        "items": specs
    }


@product_router.post("/{product_id}/specs", response_model=dict)
@wrap_response
async def create_product_spec(
    product_id: str,
    spec: Dict[str, Any],
    _: dict = Depends(require_permission("product.create"))
):
    """为商品创建规格"""
    await product_service.get_product_by_id(product_id)
    spec["product_id"] = product_id
    spec_data = await product_spec_service.create_spec(spec)
    return spec_data

"""
品牌管理 - API路由
"""


@brand_router.get("/", response_model=dict)
@wrap_response
async def list_brands(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("brand.view"))
):
    """获取品牌列表"""
    result, total = await brand_service.get_brand_by_keyword(
        page=page,
        page_size=page_size,
        keyword=keyword,
    )
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": result
    }


### 获取全部品牌（不分页）
@brand_router.get("/all", response_model=dict)
@wrap_response
async def list_all_brands(
    _: dict = Depends(require_permission("brand.view"))
):
    """获取全部品牌（不分页）"""
    result = await brand_service.get_all_brands()
    return result

@brand_router.post("/", response_model=dict)
@wrap_response
async def create_brand(
    brand: Dict[str, Any],
    _: dict = Depends(require_permission("brand.create"))
):
    """创建品牌"""
    brand_data = await brand_service.create_brand(brand)
    return brand_data


@brand_router.put("/{brand_id}", response_model=dict)
@wrap_response
async def update_brand(
    brand_id: str,
    brand: Dict[str, Any],
    _: dict = Depends(require_permission("brand.edit"))
):
    """更新品牌"""
    await brand_service.update_brand(brand_id, brand)
    return "品牌更新成功"

@brand_router.get("/{brand_id}", response_model=dict)
@wrap_response
async def get_brand(
    brand_id: str,
    _: dict = Depends(require_permission("brand.view"))
):
    """获取品牌详情"""
    brand = await brand_service.get_brand_by_id(brand_id)
    return brand


@brand_router.delete("/{brand_id}", response_model=dict)
@wrap_response
async def delete_brand(
    brand_id: str,
    _: dict = Depends(require_permission("brand.delete"))
):
    """删除品牌"""
    await brand_service.delete_brand(brand_id)
    return "品牌删除成功"

"""
分类管理 - API路由
"""

@category_router.get("/", response_model=dict)
@wrap_response
async def list_categories(
    _: dict = Depends(require_permission("category.view"))
):
    """获取分类树"""
    result = await category_service.get_category_tree()
    return result

@category_router.post("/", response_model=dict)
@wrap_response
async def create_category(
    category: Dict[str, Any],
    _: dict = Depends(require_permission("category.create"))
):
    """创建分类"""
    category_data = await category_service.create_category(category)
    return category_data

@category_router.put("/{category_id}", response_model=dict)
@wrap_response
async def update_category(
    category_id: str,
    category: Dict[str, Any],
    _: dict = Depends(require_permission("category.edit"))
):
    """更新分类"""
    await category_service.update_category(category_id, category)
    return "分类更新成功"

@category_router.get("/{category_id}", response_model=dict)
@wrap_response
async def get_category(
    category_id: str,
    _: dict = Depends(require_permission("category.view"))
):
    """获取分类详情"""
    category = await category_service.get_category_by_id(category_id, is_formatted=True)
    return category

@category_router.delete("/{category_id}", response_model=dict)
@wrap_response
async def delete_category(
    category_id: str,
    _: dict = Depends(require_permission("category.delete"))
):
    """删除分类"""
    await category_service.delete_category(category_id)
    return "分类删除成功"
    