from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from models.customer import (
    Customer,
    CustomerCreate,
    CustomerUpdate,
    CustomerListResponse,
    CustomerType,
    CustomerLevel,
    CustomerStatus,
    ShippingAddressCreate,
    ShippingAddressUpdate
)
from services.customer_service import customer_service
from .auth import get_current_active_user, require_permission

customer_router = APIRouter(prefix="/customers", tags=["客户管理"])


@customer_router.post("/", response_model=dict, status_code=201)
async def create_customer(
    customer: CustomerCreate,
    _: dict = Depends(require_permission("customer.create"))
):
    """创建客户"""
    is_valid, errors = customer_service.validate_customer_create(customer)
    if not is_valid:
        return {
            "status": "error",
            "message": "客户创建参数验证失败",
            "validation_errors": errors
        }
    customer_data = await customer_service.create_customer(customer)
    return {
        "status": "success",
        "message": "客户创建成功",
        "result": customer_data
    }


@customer_router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="客户状态"),
    level: Optional[str] = Query(None, description="客户级别"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("customer.view"))
):
    """获取客户列表"""
    result = await customer_service.list_customers(
        page=page,
        page_size=page_size,
        status=status,
        level=level,
        keyword=keyword
    )
    return result


@customer_router.get("/stats", response_model=dict)
async def get_customer_stats(_: dict = Depends(require_permission("customer.view"))):
    """获取客户统计信息"""
    stats = await customer_service.get_customer_stats()
    return {
        "status": "success",
        "result": stats
    }


@customer_router.get("/search", response_model=dict)
async def search_customers(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("customer.view"))
):
    """搜索客户（用于下拉选择等）"""
    items = await customer_service.search_customers(keyword, limit)
    return {
        "status": "success",
        "result": items
    }


@customer_router.get("/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    _: dict = Depends(require_permission("customer.view"))
):
    """获取客户详情"""
    customer = await customer_service.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")
    return customer


@customer_router.put("/{customer_id}", response_model=dict)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    _: dict = Depends(require_permission("customer.edit"))
):
    """更新客户信息"""
    is_valid, errors = customer_service.validate_customer_update(customer)
    if not is_valid:
        return {
            "status": "error",
            "message": "客户更新参数验证失败",
            "validation_errors": errors
        }
    success = await customer_service.update_customer(customer_id, customer)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在或更新失败")
    return {
        "status": "success",
        "message": "客户更新成功"
    }


@customer_router.delete("/{customer_id}", response_model=dict)
async def delete_customer(
    customer_id: str,
    _: dict = Depends(require_permission("customer.delete"))
):
    """删除客户"""
    success = await customer_service.delete(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在或删除失败")
    return {
        "status": "success",
        "message": "客户删除成功"
    }


@customer_router.patch("/{customer_id}/status", response_model=dict)
async def update_customer_status(
    customer_id: str,
    status: CustomerStatus,
    _: dict = Depends(require_permission("customer.edit"))
):
    """更新客户状态"""
    success = await customer_service.update_status(customer_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在或状态更新失败")
    return {
        "status": "success",
        "message": "客户状态更新成功"
    }


@customer_router.post("/{customer_id}/shipping-addresses", response_model=dict, status_code=201)
async def add_shipping_address(
    customer_id: str,
    address: ShippingAddressCreate,
    _: dict = Depends(require_permission("customer.edit"))
):
    """添加收货地址"""
    is_valid, errors = customer_service.validate_shipping_address_create(address)
    if not is_valid:
        return {
            "status": "error",
            "message": "收货地址参数验证失败",
            "validation_errors": errors
        }
    result = await customer_service.add_shipping_address(customer_id, address)
    if not result:
        raise HTTPException(status_code=404, detail="客户不存在")
    return {
        "status": "success",
        "message": "收货地址添加成功",
        "result": result
    }


@customer_router.put("/{customer_id}/shipping-addresses/{address_id}", response_model=dict)
async def update_shipping_address(
    customer_id: str,
    address_id: str,
    address: ShippingAddressUpdate,
    _: dict = Depends(require_permission("customer.edit"))
):
    """更新收货地址"""
    is_valid, errors = customer_service.validate_shipping_address_update(address)
    if not is_valid:
        return {
            "status": "error",
            "message": "收货地址参数验证失败",
            "validation_errors": errors
        }
    success = await customer_service.update_shipping_address(customer_id, address_id, address)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在或地址不存在")
    return {
        "status": "success",
        "message": "收货地址更新成功"
    }


@customer_router.delete("/{customer_id}/shipping-addresses/{address_id}", response_model=dict)
async def delete_shipping_address(
    customer_id: str,
    address_id: str,
    _: dict = Depends(require_permission("customer.edit"))
):
    """删除收货地址"""
    success = await customer_service.delete_shipping_address(customer_id, address_id)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在或地址不存在")
    return {
        "status": "success",
        "message": "收货地址删除成功"
    }


@customer_router.patch("/{customer_id}/shipping-addresses/{address_id}/default", response_model=dict)
async def set_default_shipping_address(
    customer_id: str,
    address_id: str,
    _: dict = Depends(require_permission("customer.edit"))
):
    """设置默认收货地址"""
    success = await customer_service.set_default_shipping_address(customer_id, address_id)
    if not success:
        raise HTTPException(status_code=404, detail="客户不存在或地址不存在")
    return {
        "status": "success",
        "message": "默认收货地址设置成功"
    }
