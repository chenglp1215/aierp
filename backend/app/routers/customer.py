"""
客户管理 - API路由
全新设计的客户管理接口
"""
import json
from fastapi import APIRouter, Query, Depends, Body
from typing import Optional

from app.routers.prompts.customer import CREATE_CUSTOMER_PROMPT
from app.routers.prompts.province_city import PROVINCE_CITY_DATA
from services.customer_service_mysql import customer_service, customer_discount_service
from .auth import get_current_active_user, require_permission
from app.decorators import wrap_response

customer_router = APIRouter(prefix="/customers", tags=["客户管理"])
customer_discount_router = APIRouter(prefix="/customer-discounts", tags=["客户折扣管理"])


def to_int_id(id_str: str) -> int:
    """将字符串 ID 转换为整数 ID"""
    try:
        return int(id_str)
    except (ValueError, TypeError):
        raise ValueError("无效的ID格式")


async def check_customer_owner(customer_id: str, current_user: dict) -> Optional[dict]:
    """检查当前用户是否是客户的负责人"""
    user_roles = [
        role.get("code") if isinstance(role, dict) else role
        for role in current_user.get("roles", [])
    ]
    if "super_admin" in user_roles:
        return None
    customer = await customer_service.get_customer_by_id(to_int_id(customer_id))
    if not customer:
        raise ValueError("客户不存在")
    if customer.get("sales_user_id") != current_user.get("id"):
        raise ValueError("您没有权限操作该客户")
    return None


@customer_router.post("/", response_model=dict)
@wrap_response
async def create_customer(
    customer: dict,
    current_user: dict = Depends(require_permission("customer.create"))
):
    """创建客户"""
    customer_data = await customer_service.create_customer(customer, current_user)
    return customer_data


@customer_router.post("/create_customer_from_ai", response_model=dict)
@wrap_response
async def create_customer_from_ai(
    input: Optional[str] = Body(None, description="输入文本"),
    file_path: Optional[str] = Query(None, description="文件路径"),
    current_user: dict = Depends(require_permission("customer.create"))
):
    """创建客户"""
    from app.agent.manager import agent_manager
    if not input and not file_path:
        raise ValueError("输入文本或文件路径不能为空")
    if agent := agent_manager.get_agent_by_name("运营助手"):
        try:
            customer_data = await agent.single_chat(
                user_message=input, file_path=file_path,
                system_prompt=PROVINCE_CITY_DATA + CREATE_CUSTOMER_PROMPT
            )
            customer_data = json.loads(customer_data)
            customer_data["sales_user_id"] = current_user.get("id")
            return customer_data
        except Exception as e:
            raise ValueError(f"AI返回的JSON格式错误: {e}")
    else:
        raise ValueError("运营助手不存在")


@customer_router.get("/", response_model=dict)
@wrap_response
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
    # 处理 sales_user_id 转换
    sales_user_id_int = to_int_id(sales_user_id) if sales_user_id else None
    result, total = await customer_service.list_customers(
        page=page, page_size=page_size, status=status,
        customer_type=customer_type, sales_user_id=sales_user_id_int, keyword=keyword
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result
    }


@customer_router.get("/stats", response_model=dict)
@wrap_response
async def get_customer_stats(_: dict = Depends(require_permission("customer.view"))):
    """获取客户统计信息"""
    stats = await customer_service.get_customer_stats()
    return stats


@customer_router.get("/search", response_model=dict)
@wrap_response
async def search_customers(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    _: dict = Depends(require_permission("customer.view"))
):
    """搜索客户（用于下拉选择等）废弃，复用list_customers接口"""
    return "搜索客户成功"


@customer_router.get("/{customer_id}", response_model=dict)
@wrap_response
async def get_customer(
    customer_id: str,
    _: dict = Depends(require_permission("customer.view"))
):
    """获取客户详情"""
    customer = await customer_service.get_customer_by_id(to_int_id(customer_id))
    if not customer:
        raise ValueError("客户不存在")
    return customer


@customer_router.put("/{customer_id}", response_model=dict)
@wrap_response
async def update_customer(
    customer_id: str,
    customer: dict,
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """更新客户信息"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.update_customer(to_int_id(customer_id), customer)
    return "客户更新成功"


@customer_router.delete("/{customer_id}", response_model=dict)
@wrap_response
async def delete_customer(
    customer_id: str,
    current_user: dict = Depends(require_permission("customer.delete"))
):
    """删除客户"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    success = await customer_service.delete_customer(to_int_id(customer_id))
    return "客户删除成功"


@customer_router.patch("/{customer_id}/status", response_model=dict)
@wrap_response
async def update_customer_status(
    customer_id: str,
    status_data: dict = Body(..., description="状态更新数据"),
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """更新客户状态"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    status = status_data.get("status")
    if not status:
        raise ValueError("status字段为必填")
    success = await customer_service.update_status(to_int_id(customer_id), status)
    return "客户状态更新成功"


@customer_router.patch("/{customer_id}/transfer", response_model=dict)
@wrap_response
async def transfer_customer(
    customer_id: str,
    transfer_data: dict = Body(..., description="转移客户数据"),
    current_user: dict = Depends(require_permission("customer.edit"))
):
    """转移客户给其他销售"""
    owner_check = await check_customer_owner(customer_id, current_user)
    if owner_check:
        return owner_check
    new_user_id = transfer_data.get("new_user_id")
    if not new_user_id:
        raise ValueError("new_user_id字段为必填")

    # 获取目标用户信息
    from services.auth_service import mysql_user_service
    new_user = await mysql_user_service.get_by_id(int(new_user_id))
    if not new_user:
        raise ValueError("目标销售不存在")

    success = await customer_service.transfer_customer(
        to_int_id(customer_id),
        int(new_user_id),
        new_user.get("full_name") or new_user.get("username")
    )
    return "客户转移成功"



#### 客户折扣管理
@customer_discount_router.post("/", response_model=dict)
@wrap_response
async def create_customer_discount(
    discount: dict,
    _: dict = Depends(require_permission("customer_discount.create"))
):
    result = await customer_discount_service.create_discount(discount)
    return result


@customer_discount_router.get("/", response_model=dict)
@wrap_response
async def list_customer_discounts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    customer_id: Optional[str] = Query(None, description="客户ID"),
    brand_id: Optional[str] = Query(None, description="品牌ID"),
    is_active: Optional[bool] = Query(None, description="是否生效"),
    _: dict = Depends(require_permission("customer_discount.view"))
):
    """获取客户折扣列表"""
    customer_id_int = to_int_id(customer_id) if customer_id else None
    brand_id_int = to_int_id(brand_id) if brand_id else None
    result, total = await customer_discount_service.list_discounts(
        page=page,
        page_size=page_size,
        customer_id=customer_id_int,
        brand_id=brand_id_int,
        is_active=is_active
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result
    }


@customer_discount_router.get("/{discount_id}", response_model=dict)
@wrap_response
async def get_customer_discount(
    discount_id: str,
    _: dict = Depends(require_permission("customer_discount.view"))
):
    """获取客户折扣详情"""
    discount = await customer_discount_service.get_discount_by_id(to_int_id(discount_id))
    if not discount:
        raise ValueError("客户折扣不存在")
    return discount


@customer_discount_router.get("/customer/{customer_id}/brand/{brand_id}", response_model=dict)
@wrap_response
async def get_discount_by_customer_and_brand(
    customer_id: str,
    brand_id: str,
    _: dict = Depends(require_permission("customer_discount.view"))
):
    """获取指定客户和品牌的折扣"""
    discount = await customer_discount_service.get_discount_by_customer_and_brand(
        to_int_id(customer_id), to_int_id(brand_id)
    )
    if not discount:
        raise ValueError("该客户和品牌的折扣配置不存在")
    return discount


@customer_discount_router.put("/{discount_id}", response_model=dict)
@wrap_response
async def update_customer_discount(
    discount_id: str,
    discount: dict,
    _: dict = Depends(require_permission("customer_discount.edit"))
):
    """更新客户折扣"""
    existing = await customer_discount_service.get_discount_by_id(to_int_id(discount_id))
    if not existing:
        raise ValueError("客户折扣不存在")
    success = await customer_discount_service.update_discount(to_int_id(discount_id), discount)
    return "客户折扣更新成功"


@customer_discount_router.delete("/{discount_id}", response_model=dict)
@wrap_response
async def delete_customer_discount(
    discount_id: str,
    _: dict = Depends(require_permission("customer_discount.delete"))
):
    """删除客户折扣"""
    existing = await customer_discount_service.get_discount_by_id(to_int_id(discount_id))
    if not existing:
        raise ValueError("客户折扣不存在")
    success = await customer_discount_service.delete_discount(to_int_id(discount_id))
    return "客户折扣删除成功"


@customer_discount_router.patch("/{discount_id}/status", response_model=dict)
@wrap_response
async def toggle_discount_status(
    discount_id: str,
    is_active: bool = Query(..., description="是否生效"),
    _: dict = Depends(require_permission("customer_discount.edit"))
):
    """切换客户折扣状态"""
    existing = await customer_discount_service.get_discount_by_id(to_int_id(discount_id))
    if not existing:
        raise ValueError("客户折扣不存在")
    success = await customer_discount_service.toggle_discount_status(to_int_id(discount_id), is_active)
    return "客户折扣状态更新成功"