"""
客户管理 - API路由
"""
import json
from fastapi import APIRouter, Query, Depends, Body
from fastapi.responses import StreamingResponse
from typing import Optional

from app.routers.prompts.customer import CREATE_CUSTOMER_PROMPT, PARSE_CUSTOMER_SYSTEM_PROMPT
from app.routers.prompts.province_city import PROVINCE_CITY_DATA
from services.customer_service_mysql import customer_service, customer_discount_service
from validators.customer_ai_parse_validator import CustomerAiParseRequest
from validators.shipping_address_ai_parse_validator import ShippingAddressAiParseRequest
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


def _is_admin(user: dict) -> bool:
    """判断用户是否为管理员"""
    user_roles = [
        role.get("code") if isinstance(role, dict) else role
        for role in user.get("roles", [])
    ]
    return "super_admin" in user_roles or "admin" in user_roles


async def check_customer_owner(customer_id: str, current_user: dict) -> Optional[dict]:
    """检查当前用户是否是客户的负责人（基于 created_by）"""
    if _is_admin(current_user):
        return None
    customer = await customer_service.get_customer_by_id(to_int_id(customer_id))
    if not customer:
        raise ValueError("客户不存在")
    # 公共池客户，管理员可操作，普通用户不可操作
    if customer.get("customer_status") == 2:
        raise ValueError("公共池客户不可操作，请先认领")
    # 基于 created_by 判断归属
    if customer.get("created_by") != current_user.get("id"):
        raise ValueError("您没有权限操作该客户")
    return None


# ============ 客户 CRUD 路由 ============

@customer_router.post("/", response_model=dict)
@wrap_response
async def create_customer(
    customer: dict,
    current_user: dict = Depends(require_permission("customer.create"))
):
    """创建客户"""
    customer_data = await customer_service.create_customer(customer, current_user)
    return customer_data


@customer_router.post("/parse-by-ai", response_model=dict)
@wrap_response
async def parse_customer_by_ai(
    request: CustomerAiParseRequest,
    current_user: dict = Depends(require_permission("customer.create"))
):
    """
    AI智能解析客户信息

    接受文本描述和/或图片（base64），调用大模型提取结构化客户数据。
    返回的数据可直接用于创建客户接口。
    返回结构: { customer: {...}, research_groups: [...], invoice_info: {...}, shipping_address: {...} }
    """
    from services.customer_ai_parse_service import CustomerAiParseService
    service = CustomerAiParseService()
    try:
        result = await service.parse_customer(request)
        return result
    except RuntimeError as e:
        raise ValueError(str(e))


@customer_router.post("/shipping-addresses/parse-by-ai", response_model=dict)
@wrap_response
async def parse_shipping_address_by_ai(
    request: ShippingAddressAiParseRequest,
    current_user: dict = Depends(require_permission("customer.create"))
):
    """
    AI智能解析收货地址信息

    接受文本描述和/或图片（base64），调用大模型提取结构化地址数据。
    返回结构: { receiver, phone, province, city, district, address }
    """
    from services.shipping_address_ai_parse_service import shipping_address_ai_parse_service
    try:
        result = await shipping_address_ai_parse_service.parse_shipping_address(request)
        return result
    except RuntimeError as e:
        raise ValueError(str(e))


# DEPRECATED: 请使用 POST /customers/parse-by-ai 替代
@customer_router.post("/create_customer_from_ai", response_model=dict, deprecated=True)
@wrap_response
async def create_customer_from_ai(
    input: Optional[str] = Body(None, description="输入文本"),
    file_path: Optional[str] = Query(None, description="文件路径"),
    current_user: dict = Depends(require_permission("customer.create"))
):
    """AI创建客户"""
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
    customer_status: Optional[int] = Query(None, description="客户状态: 1=正常, 2=公共池"),
    customer_type: Optional[str] = Query(None, description="客户类型: terminal/dealer"),
    sales_user_id: Optional[str] = Query(None, description="业务员ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    created_at_start: Optional[str] = Query(None, description="创建时间起"),
    created_at_end: Optional[str] = Query(None, description="创建时间止"),
    current_user: dict = Depends(require_permission("customer.view")),
):
    """获取客户列表（普通用户按 created_by 过滤）"""
    sales_user_id_int = to_int_id(sales_user_id) if sales_user_id else None
    is_admin = _is_admin(current_user)
    user_id = current_user.get("id")

    result, total = await customer_service.list_customers(
        page=page, page_size=page_size,
        customer_status=customer_status,
        customer_type=customer_type,
        sales_user_id=sales_user_id_int,
        keyword=keyword,
        created_at_start=created_at_start,
        created_at_end=created_at_end,
        user_id=user_id,
        is_admin=is_admin,
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
    limit: int = Query(5, ge=1, le=10, description="返回数量，最多5条"),
    _: dict = Depends(require_permission("customer.view"))
):
    """搜索客户（用于下拉选择等），返回 id/name/code 格式的客户列表"""
    result = await customer_service.search_customers(keyword=keyword, limit=limit)
    return result


@customer_router.get("/check-overdue", response_model=dict)
@wrap_response
async def check_overdue(
    _: dict = Depends(require_permission("customer.view"))
):
    """批量超账期判断"""
    result = await customer_service.check_overdue_status()
    return result


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
    success = await customer_service.update_customer(to_int_id(customer_id), customer, current_user)
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


# ============ 客户状态和转移路由 ============

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
    customer_status = status_data.get("customer_status")
    if not customer_status:
        raise ValueError("customer_status字段为必填")
    success = await customer_service.update_status(to_int_id(customer_id), int(customer_status))
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


# ============ 新增功能路由 ============

@customer_router.post("/{customer_id}/claim", response_model=dict)
@wrap_response
async def claim_customer(
    customer_id: str,
    current_user: dict = Depends(require_permission("customer.claim"))
):
    """客户认领：从公共池认领客户恢复为正常状态"""
    user_id = current_user.get("id")
    user_name = current_user.get("full_name") or current_user.get("username")
    result = await customer_service.claim_customer(to_int_id(customer_id), user_id, user_name)
    return result


@customer_router.put("/{customer_id}/member-account", response_model=dict)
@wrap_response
async def register_member(
    customer_id: str,
    data: dict,
    current_user: dict = Depends(require_permission("customer.member"))
):
    """为客户注册会员账号"""
    member_account = data.get("member_account")
    if not member_account:
        raise ValueError("会员账号不能为空")
    result = await customer_service.register_member(to_int_id(customer_id), member_account)
    return result


@customer_router.put("/{customer_id}/order-defaults", response_model=dict)
@wrap_response
async def set_order_defaults(
    customer_id: str,
    data: dict,
    current_user: dict = Depends(require_permission("customer.order-defaults"))
):
    """设置客户订单默认值"""
    result = await customer_service.set_order_defaults(to_int_id(customer_id), data)
    return result


@customer_router.put("/{customer_id}/credit", response_model=dict)
@wrap_response
async def set_credit(
    customer_id: str,
    data: dict,
    current_user: dict = Depends(require_permission("customer.credit"))
):
    """设置客户账期额度"""
    credit_days = data.get("credit_days", 0)
    credit_limit = data.get("credit_limit", 0)
    result = await customer_service.set_credit(to_int_id(customer_id), int(credit_days), float(credit_limit))
    return result


@customer_router.post("/export", response_model=None)
async def export_customers(
    data: dict,
    current_user: dict = Depends(require_permission("customer.export"))
):
    """批量导出客户数据为Excel"""
    is_admin = _is_admin(current_user)
    user_id = current_user.get("id")
    customer_ids = data.get("customer_ids")
    if customer_ids:
        customer_ids = [int(id) for id in customer_ids]
    result = await customer_service.export_customers(
        customer_ids=customer_ids,
        filters=data,
        user_id=user_id,
        is_admin=is_admin,
    )
    return result


# ============ 客户折扣管理 ============

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