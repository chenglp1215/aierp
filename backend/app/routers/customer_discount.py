"""
客户折扣管理 - API路由
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional

from models.customer_discount import (
    CustomerDiscountCreate,
    CustomerDiscountUpdate,
)
from services.customer_discount_service import customer_discount_service
from .auth import require_permission
from app.decorators import handle_result, success_response, error_response

customer_discount_router = APIRouter(prefix="/customer-discounts", tags=["客户折扣管理"])


@customer_discount_router.post("/", response_model=dict, status_code=201)
async def create_customer_discount(
    discount: CustomerDiscountCreate,
    _: dict = Depends(require_permission("customer_discount.create"))
):
    """创建客户折扣"""
    is_duplicate = await customer_discount_service.check_duplicate(
        discount.customer_id, discount.brand_id
    )
    if is_duplicate:
        return error_response("该客户和品牌的折扣配置已存在")
    result = await customer_discount_service.create_discount(discount)
    return success_response("客户折扣创建成功", result)


@customer_discount_router.get("/", response_model=dict)
async def list_customer_discounts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    brand_id: Optional[str] = Query(None, description="品牌ID"),
    is_active: Optional[bool] = Query(None, description="是否生效"),
    _: dict = Depends(require_permission("customer_discount.view"))
):
    """获取客户折扣列表"""
    result = await customer_discount_service.list_discounts(
        page=page,
        page_size=page_size,
        customer_id=customer_id,
        brand_id=brand_id,
        is_active=is_active
    )
    return success_response("获取客户折扣列表成功", result)


@customer_discount_router.get("/{discount_id}", response_model=dict)
async def get_customer_discount(
    discount_id: str,
    _: dict = Depends(require_permission("customer_discount.view"))
):
    """获取客户折扣详情"""
    discount = await customer_discount_service.get_by_id(discount_id)
    if not discount:
        return error_response("客户折扣不存在")
    
    # 获取品牌名称
    if discount.get("brand_id"):
        # TODO: brand_service 已迁移至 services.product_service，需更新导入路径
        from services.brand_service import brand_service
        brand = await brand_service.get_brand_by_id(discount["brand_id"])
        if brand:
            discount["brand_name"] = brand.get("name", "")
    
    return success_response("获取客户折扣详情成功", discount)


@customer_discount_router.get("/customer/{customer_id}/brand/{brand_id}", response_model=dict)
async def get_discount_by_customer_and_brand(
    customer_id: str,
    brand_id: str,
    _: dict = Depends(require_permission("customer_discount.view"))
):
    """获取指定客户和品牌的折扣"""
    discount = await customer_discount_service.get_discount_by_customer_and_brand(
        customer_id, brand_id
    )
    if not discount:
        return error_response("该客户和品牌的折扣配置不存在")
    
    # 获取品牌名称
    if discount.get("brand_id"):
        # TODO: brand_service 已迁移至 services.product_service，需更新导入路径
        from services.brand_service import brand_service
        brand = await brand_service.get_brand_by_id(discount["brand_id"])
        if brand:
            discount["brand_name"] = brand.get("name", "")
    
    return success_response("获取客户折扣成功", discount)


@customer_discount_router.put("/{discount_id}", response_model=dict)
async def update_customer_discount(
    discount_id: str,
    discount: CustomerDiscountUpdate,
    _: dict = Depends(require_permission("customer_discount.edit"))
):
    """更新客户折扣"""
    existing = await customer_discount_service.get_by_id(discount_id)
    if not existing:
        return error_response("客户折扣不存在")
    success = await customer_discount_service.update_discount(discount_id, discount)
    return handle_result(success, "客户折扣更新成功", "客户折扣更新失败")


@customer_discount_router.delete("/{discount_id}", response_model=dict)
async def delete_customer_discount(
    discount_id: str,
    _: dict = Depends(require_permission("customer_discount.delete"))
):
    """删除客户折扣"""
    existing = await customer_discount_service.get_by_id(discount_id)
    if not existing:
        return error_response("客户折扣不存在")
    success = await customer_discount_service.delete_discount(discount_id)
    return handle_result(success, "客户折扣删除成功", "客户折扣删除失败")


@customer_discount_router.patch("/{discount_id}/status", response_model=dict)
async def toggle_discount_status(
    discount_id: str,
    is_active: bool = Query(..., description="是否生效"),
    _: dict = Depends(require_permission("customer_discount.edit"))
):
    """切换客户折扣状态"""
    existing = await customer_discount_service.get_by_id(discount_id)
    if not existing:
        return error_response("客户折扣不存在")
    success = await customer_discount_service.toggle_discount_status(discount_id, is_active)
    return handle_result(success, "客户折扣状态更新成功", "客户折扣状态更新失败")
