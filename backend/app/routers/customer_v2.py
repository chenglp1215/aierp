"""
客户管理 - API路由
全新设计的客户管理接口
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional

from models.customer_v2 import (
    CustomerCreate,
    CustomerUpdate,
    CustomerStatus,
    InvoiceInfoCreate,
    InvoiceInfoUpdate,
    ShippingAddressCreate,
    ShippingAddressUpdate,
    ContactInfoUpdate,
    CustomerTransferRequest,
)
from services.customer_service_v2 import customer_service
from .auth import get_current_active_user, require_permission
from app.decorators import handle_result, validation_error, success_response, error_response

customer_router_v2 = APIRouter(prefix="/customers-v2", tags=["客户管理V2"])


async def check_customer_owner(customer_id: str, current_user: dict) -> Optional[dict]:
    """检查当前用户是否是客户的负责人"""
    user_roles = [
        role.get("code") if isinstance(role, dict) else role
        for role in current_user.get("roles", [])
    ]
    if "super_admin" in user_roles:
        return None
    customer = await customer_service.get_by_id(customer_id)
    if not customer:
        return error_response("客户不存在")
    if customer.get("sales_user_id") != current_user.get("id"):
        return error_response("您没有权限操作该客户")
    return None


@customer_router_v2.post("/", response_model=dict, status_code=201)
async def create_customer(
    customer: CustomerCreate,
    current_user: dict = Depends(require_permission("customer.create"))
):
    """创建客户"""
    is_valid, errors = customer_service.validate_customer_create(customer.model_dump())
    if not is_valid:
        return validation_error(errors, "客户创建参数验证失败")
    customer_data = await customer_service.create_customer(customer, current_user)
    return success_response("客户创建成功", customer_data)


@customer_router_v2.get("/", response_model=dict)
async def list_customers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="客户状态"),
    customer_type: Optional[str] = Query(None, description="客户类型: terminal/dealer"),
    sales_user_id: Optional[str] = Query(None, description="销售人ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("customer.view")),
):
    """获取客户列表"""
    # 校验用户是否有权限查看客户列表
    result = await customer_service.list_customers(
        page=page, page_size=page_size, status=status,
        customer_type=customer_type, sales_user_id=sales_user_id, keyword=keyword
    )
    return success_response("获取客户列表成功", result)


@customer_router_v2.get("/stats", response_model=dict)
async def get_customer_stats(_: dict = Depends(require_permission("customer.view"))):
    """获取客户统计信息"""
    stats = await customer_service.get_customer_stats()
    return success_response("获取客户统计成功", stats)


@customer_router_v2.get("/search", response_model=dict)
async def search_customers(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("customer.view"))
):
    """搜索客户（用于下拉选择等）"""
    items = await customer_service.search_customers(keyword, limit)
    return success_response("搜索客户成功", items)


@customer_router_v2.get("/{customer_id}", response_model=dict)
async def get_customer(
    customer_id: str,
    _: dict = Depends(require_permission("customer.view"))
):
    """获取客户详情"""
    customer = await customer_service.get_by_id(customer_id)
    if not customer:
        return error_response("客户不存在")
    return success_response("获取客户详情成功", customer)


@customer_router_v2.put("/{customer_id}", response_model=dict)
async def update_customer(
    customer_id: str,
    customer: CustomerUpdate,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """更新客户信息"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check

    is_valid, errors = customer_service.validate_customer_update(customer.model_dump(exclude_unset=True))
    if not is_valid:
        return validation_error(errors, "客户更新参数验证失败")
    success = await customer_service.update_customer(customer_id, customer)
    return handle_result(success, "客户更新成功", "客户不存在或更新失败")


@customer_router_v2.delete("/{customer_id}", response_model=dict)
async def delete_customer(
    customer_id: str,
    current_user: dict = Depends(require_permission("customer.delete"))
):
    """删除客户"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.delete_customer(customer_id)
    return handle_result(success, "客户删除成功", "客户不存在或删除失败")


@customer_router_v2.patch("/{customer_id}/status", response_model=dict)
async def update_customer_status(
    customer_id: str,
    status: CustomerStatus,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """更新客户状态"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.update_status(customer_id, status)
    return handle_result(success, "客户状态更新成功", "客户不存在或状态更新失败")


@customer_router_v2.put("/{customer_id}/contact-info", response_model=dict)
async def update_contact_info(
    customer_id: str,
    contact_info: ContactInfoUpdate,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """更新联系人信息"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    is_valid, errors = customer_service.validate_contact_info_update(contact_info.model_dump(exclude_unset=True))
    if not is_valid:
        return validation_error(errors, "联系人信息参数验证失败")
    success = await customer_service.update_contact_info(customer_id, contact_info)
    return handle_result(success, "联系人信息更新成功", "客户不存在或更新失败")


@customer_router_v2.post("/{customer_id}/invoice-infos", response_model=dict, status_code=201)
async def add_invoice_info(
    customer_id: str,
    invoice_info: InvoiceInfoCreate,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """添加开票信息"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    is_valid, errors = customer_service.validate_invoice_info_create(invoice_info.model_dump())
    if not is_valid:
        return validation_error(errors, "开票信息参数验证失败")
    result = await customer_service.add_invoice_info(customer_id, invoice_info)
    if not result:
        return error_response("客户不存在")
    return success_response("开票信息添加成功", result)


@customer_router_v2.put("/{customer_id}/invoice-infos/{invoice_id}", response_model=dict)
async def update_invoice_info(
    customer_id: str,
    invoice_id: str,
    invoice_info: InvoiceInfoUpdate,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """更新开票信息"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    is_valid, errors = customer_service.validate_invoice_info_update(invoice_info.model_dump(exclude_unset=True))
    if not is_valid:
        return validation_error(errors, "开票信息参数验证失败")
    success = await customer_service.update_invoice_info(customer_id, invoice_id, invoice_info)
    return handle_result(success, "开票信息更新成功", "客户不存在或开票信息不存在")


@customer_router_v2.delete("/{customer_id}/invoice-infos/{invoice_id}", response_model=dict)
async def delete_invoice_info(
    customer_id: str,
    invoice_id: str,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """删除开票信息"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.delete_invoice_info(customer_id, invoice_id)
    return handle_result(success, "开票信息删除成功", "客户不存在或开票信息不存在")


@customer_router_v2.patch("/{customer_id}/invoice-infos/{invoice_id}/default", response_model=dict)
async def set_default_invoice_info(
    customer_id: str,
    invoice_id: str,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """设置默认开票信息"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.set_default_invoice_info(customer_id, invoice_id)
    return handle_result(success, "默认开票信息设置成功", "客户不存在或开票信息不存在")


@customer_router_v2.post("/{customer_id}/shipping-addresses", response_model=dict, status_code=201)
async def add_shipping_address(
    customer_id: str,
    address: ShippingAddressCreate,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """添加收货地址"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    is_valid, errors = customer_service.validate_shipping_address_create(address.model_dump())
    if not is_valid:
        return validation_error(errors, "收货地址参数验证失败")
    result = await customer_service.add_shipping_address(customer_id, address)
    if not result:
        return error_response("客户不存在")
    return success_response("收货地址添加成功", result)


@customer_router_v2.put("/{customer_id}/shipping-addresses/{address_id}", response_model=dict)
async def update_shipping_address(
    customer_id: str,
    address_id: str,
    address: ShippingAddressUpdate,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """更新收货地址"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    is_valid, errors = customer_service.validate_shipping_address_update(address.model_dump(exclude_unset=True))
    if not is_valid:
        return validation_error(errors, "收货地址参数验证失败")
    success = await customer_service.update_shipping_address(customer_id, address_id, address)
    return handle_result(success, "收货地址更新成功", "客户不存在或收货地址不存在")


@customer_router_v2.delete("/{customer_id}/shipping-addresses/{address_id}", response_model=dict)
async def delete_shipping_address(
    customer_id: str,
    address_id: str,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """删除收货地址"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.delete_shipping_address(customer_id, address_id)
    return handle_result(success, "收货地址删除成功", "客户不存在或收货地址不存在")


@customer_router_v2.patch("/{customer_id}/shipping-addresses/{address_id}/default", response_model=dict)
async def set_default_shipping_address(
    customer_id: str,
    address_id: str,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """设置默认收货地址"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.set_default_shipping_address(customer_id, address_id)
    return handle_result(success, "默认收货地址设置成功", "客户不存在或收货地址不存在")


@customer_router_v2.patch("/{customer_id}/transfer", response_model=dict)
async def transfer_customer(
    customer_id: str,
    transfer_request: CustomerTransferRequest,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """转移客户给其他销售"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.transfer_customer(customer_id, transfer_request.new_sales_user_id)
    if not success:
        return error_response("目标销售不存在或客户转移失败")
    return success_response("客户转移成功")


@customer_router_v2.get("/sales-users/list", response_model=dict)
async def get_sales_users(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("customer.view"))
):
    """获取销售员列表"""
    sales_users = await customer_service.get_sales_users(keyword)
    return success_response("获取销售员列表成功", result=sales_users)
