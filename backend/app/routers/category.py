from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CategoryListResponse,
    CategoryTreeNode,
)
from services.category_service import category_service
from .auth import get_current_active_user, require_permission

category_router = APIRouter(prefix="/categories", tags=["分类管理"])


@category_router.post("/", response_model=dict, status_code=201)
async def create_category(
    category: CategoryCreate,
    _: dict = Depends(require_permission("category.create"))
):
    """创建分类"""
    try:
        category_data = await category_service.create_category(category)
        return {
            "status": "success",
            "message": "分类创建成功",
            "result": category_data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@category_router.get("/", response_model=CategoryListResponse)
async def list_categories(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    parent_id: Optional[str] = Query(None, description="父分类ID"),
    _: dict = Depends(require_permission("category.view"))
):
    """获取分类列表"""
    result = await category_service.list_categories(
        page=page,
        page_size=page_size,
        keyword=keyword,
        parent_id=parent_id
    )
    return result


@category_router.get("/tree", response_model=dict)
async def get_category_tree(_: dict = Depends(require_permission("category.view"))):
    """获取分类树形结构"""
    tree = await category_service.get_category_tree()
    return {
        "status": "success",
        "result": tree
    }


@category_router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: str,
    _: dict = Depends(require_permission("category.view"))
):
    """获取分类详情"""
    category = await category_service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category


@category_router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: str,
    category: CategoryUpdate,
    _: dict = Depends(require_permission("category.edit"))
):
    """更新分类"""
    try:
        success = await category_service.update_category(category_id, category)
        if not success:
            raise HTTPException(status_code=404, detail="分类不存在或更新失败")
        return {
            "status": "success",
            "message": "分类更新成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@category_router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: str,
    _: dict = Depends(require_permission("category.delete"))
):
    """删除分类"""
    try:
        success = await category_service.delete_category(category_id)
        if not success:
            raise HTTPException(status_code=404, detail="分类不存在或删除失败")
        return {
            "status": "success",
            "message": "分类删除成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
