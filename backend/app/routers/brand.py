"""
品牌管理 - API路由
"""
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional, List, Dict, Any

from models.product import (
    Brand,
    BrandCreate,
    BrandUpdate,
    BrandListResponse,
)
from services.brand_service import brand_service
from .auth import get_current_active_user, require_permission
from app.decorators import handle_result, success_response, error_response

brand_router = APIRouter(prefix="/brands", tags=["品牌管理"])


async def _enrich_brand_purchaser(brand: Dict[str, Any]) -> Dict[str, Any]:
    """富化品牌的采购人员名称"""
    purchaser_id = brand.get("purchaser_id")
    if purchaser_id:
        try:
            from bson import ObjectId
            from app.database import db
            mongo_db = db.get_mongo_db()
            user = await mongo_db["users"].find_one({"_id": ObjectId(purchaser_id)})
            if user:
                brand["purchaser_name"] = user.get("full_name", user.get("username", ""))
            else:
                brand["purchaser_name"] = ""
        except Exception:
            brand["purchaser_name"] = ""
    else:
        brand["purchaser_name"] = ""
    return brand


@brand_router.post("/", response_model=dict, status_code=201)
async def create_brand(
    brand: BrandCreate,
    _: dict = Depends(require_permission("brand.create"))
):
    """创建品牌"""
    existing = await brand_service.get_brand_by_name(brand.name)
    if existing:
        return error_response("品牌名称已存在")
    brand_data = await brand_service.create_brand(brand)
    return success_response("品牌创建成功", brand_data)


@brand_router.get("/", response_model=BrandListResponse)
async def list_brands(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    _: dict = Depends(require_permission("brand.view"))
):
    """获取品牌列表"""
    result = await brand_service.list_brands(
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_active=is_active
    )
    # 富化采购人员名称
    for item in result.get("items", []):
        await _enrich_brand_purchaser(item)
    return result


@brand_router.get("/all", response_model=dict)
async def get_all_brands(
    is_active: Optional[bool] = Query(None, description="是否激活"),
    _: dict = Depends(require_permission("brand.view"))
):
    """获取所有品牌（用于下拉选择等）"""
    items = await brand_service.get_all_brands(is_active=is_active)
    return success_response("获取品牌列表成功", items)


@brand_router.post("/batch-purchasers", response_model=dict)
async def batch_get_brand_purchasers(
    brand_ids: List[str] = Body(..., description="品牌ID列表"),
    _: dict = Depends(require_permission("brand.view"))
):
    """批量获取品牌的采购人信息"""
    from bson import ObjectId
    from app.database import db

    result = {}
    valid_ids = []
    for bid in brand_ids:
        try:
            valid_ids.append(ObjectId(bid))
        except Exception:
            pass

    if valid_ids:
        mongo_db = db.get_mongo_db()
        brands = await mongo_db["brands"].find(
            {"_id": {"$in": valid_ids}}
        ).to_list(length=None)

        # 收集所有 purchaser_id，批量查询用户名
        purchaser_ids = set()
        for b in brands:
            pid = b.get("purchaser_id")
            if pid:
                try:
                    purchaser_ids.add(ObjectId(pid))
                except Exception:
                    pass

        user_map = {}
        if purchaser_ids:
            users = await mongo_db["users"].find(
                {"_id": {"$in": list(purchaser_ids)}}
            ).to_list(length=None)
            for u in users:
                user_map[str(u["_id"])] = u.get("full_name", u.get("username", ""))

        for b in brands:
            bid = str(b["_id"])
            pid = b.get("purchaser_id", "")
            purchaser_name = ""
            if pid:
                purchaser_name = user_map.get(pid, "")
            result[bid] = {
                "purchaser_id": pid,
                "purchaser_name": purchaser_name
            }

    return success_response(result=result)


@brand_router.get("/purchaser-candidates", response_model=dict)
async def get_purchaser_candidates(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("brand.view"))
):
    """获取采购组人员候选列表"""
    from services.auth_service import role_service, auth_service

    purchaser_role = await role_service.find_one({"code": "purchaser_group"})
    if not purchaser_role:
        return success_response(result=[])

    purchaser_role_id = str(purchaser_role["id"])

    users = await auth_service.collection.find({
        "status": "active",
        "role_ids": purchaser_role_id
    }).to_list(length=100)

    candidates = []
    for user in users:
        user_id = str(user.get("_id"))
        full_name = user.get("full_name", "")
        username = user.get("username", "")

        if keyword:
            if keyword.lower() not in (full_name or "").lower() and keyword.lower() not in username.lower():
                continue

        candidates.append({
            "id": user_id,
            "full_name": full_name,
            "username": username
        })

    return success_response(result=candidates)


@brand_router.get("/{brand_id}", response_model=dict)
async def get_brand(
    brand_id: str,
    _: dict = Depends(require_permission("brand.view"))
):
    """获取品牌详情"""
    brand = await brand_service.get_brand_by_id(brand_id)
    if not brand:
        return error_response("品牌不存在")
    brand = await _enrich_brand_purchaser(brand)
    return success_response("获取品牌详情成功", brand)


@brand_router.put("/{brand_id}", response_model=dict)
async def update_brand(
    brand_id: str,
    brand: BrandUpdate,
    _: dict = Depends(require_permission("brand.edit"))
):
    """更新品牌"""
    if brand.name:
        existing = await brand_service.get_brand_by_name(brand.name)
        if existing and existing["id"] != brand_id:
            return error_response("品牌名称已存在")
    success = await brand_service.update_brand(brand_id, brand)
    return handle_result(success, "品牌更新成功", "品牌不存在或更新失败")


@brand_router.delete("/{brand_id}", response_model=dict)
async def delete_brand(
    brand_id: str,
    _: dict = Depends(require_permission("brand.delete"))
):
    """删除品牌"""
    try:
        success = await brand_service.delete_brand(brand_id)
        return handle_result(success, "品牌删除成功", "品牌不存在或删除失败")
    except ValueError as e:
        return error_response(str(e))


@brand_router.patch("/{brand_id}/toggle-active", response_model=dict)
async def toggle_brand_active(
    brand_id: str,
    is_active: bool = Query(..., description="是否激活"),
    _: dict = Depends(require_permission("brand.edit"))
):
    """切换品牌激活状态"""
    success = await brand_service.toggle_brand_active(brand_id, is_active)
    return handle_result(success, f"品牌已{'激活' if is_active else '停用'}", "品牌不存在或更新失败")
