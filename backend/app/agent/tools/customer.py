from typing import Any, Dict, Optional
import logging

from app.agent.tools.base import BaseTool, ToolResult
from services.customer_service import customer_service
from models.customer import CustomerCreate, CustomerUpdate, ShippingAddressCreate, ShippingAddressUpdate, CustomerType

logger = logging.getLogger(__name__)


class CustomerSearchTool(BaseTool):
    name = "customer_search"
    cn_name = "搜索客户"
    description = "搜索客户。当用户询问客户信息、查找客户、搜索客户列表时使用。"
    permission_code = "customer.view"
    parameters = {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "搜索关键词（客户名称、编码、联系人、电话）",
                "example": "张三"
            },
            "level": {
                "type": "string",
                "description": "客户级别筛选：vip(VIP客户)、potential(潜在客户)、normal(普通客户)",
                "example": "vip"
            },
            "status": {
                "type": "string",
                "description": "客户状态筛选：normal(正常)、inactive(未激活)、blacklisted(黑名单)",
                "default": "normal",
                "example": "normal"
            },
            "page": {
                "type": "integer",
                "description": "页码，默认1",
                "default": 1,
                "example": 1
            },
            "page_size": {
                "type": "integer",
                "description": "每页数量，默认20",
                "default": 20,
                "example": 20
            }
        },
        "required": []
    }

    async def execute(
        self,
        keyword: Optional[str] = None,
        level: Optional[str] = None,
        status: str = "normal",
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Customer search: keyword={keyword}, level={level}")

            result = await customer_service.list_customers(
                page=page,
                page_size=page_size,
                status=status,
                level=level,
                keyword=keyword
            )

            items = result.get("items", [])
            if not items:
                return ToolResult(
                    success=True,
                    content="未找到客户记录",
                    metadata={"total": 0}
                )

            content_lines = [f"共找到 {result.get('total', 0)} 家客户："]
            for customer in items[:10]:
                content_lines.append(
                    f"[客户编码:{customer.get('customer_code', 'N/A')}] "
                    f"[ID:{customer.get('id', 'N/A')}] "
                    f"名称: {customer.get('name', 'N/A')} | "
                    f"级别: {customer.get('level', 'N/A')} | "
                    f"联系人: {customer.get('contact_person', 'N/A')} | "
                    f"电话: {customer.get('contact_phone', 'N/A')}"
                )

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata={"total": result.get("total", 0)}
            )

        except Exception as e:
            logger.error(f"Customer search failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class CustomerCreateTool(BaseTool):
    name = "customer_create"
    cn_name = "创建客户"
    description = "创建新客户。当用户要求新建客户、添加客户时使用。"
    permission_code = "customer.create"
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "客户名称（必填）",
                "example": "深圳市某某公司"
            },
            "customer_type": {
                "type": "string",
                "description": "客户类型：enterprise(企业)、individual(个人)、government(政府)",
                "default": "company",
                "example": "enterprise"
            },
            "level": {
                "type": "string",
                "description": "客户级别：vip(VIP)、potential(潜在)、normal(普通)",
                "default": "normal",
                "example": "normal"
            },
            "contact_person": {
                "type": "string",
                "description": "联系人",
                "example": "张三"
            },
            "contact_phone": {
                "type": "string",
                "description": "联系电话",
                "example": "13800138000"
            },
            "contact_email": {
                "type": "string",
                "description": "联系邮箱",
                "example": "zhangsan@example.com"
            },
            "address": {
                "type": "string",
                "description": "客户地址",
                "example": "深圳市南山区科技园"
            },
            "tax_number": {
                "type": "string",
                "description": "税号",
                "example": "91440300MA5xxxxx"
            },
            "bank_name": {
                "type": "string",
                "description": "开户银行",
                "example": "中国银行深圳分行"
            },
            "bank_account": {
                "type": "string",
                "description": "银行账号",
                "example": "6222021234567890"
            },
            "remarks": {
                "type": "string",
                "description": "备注",
                "example": "长期合作客户"
            }
        },
        "required": ["name"]
    }

    async def execute(
        self,
        name: str,
        customer_type: str = "company",
        level: str = "normal",
        contact_person: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        address: Optional[str] = None,
        tax_number: Optional[str] = None,
        bank_name: Optional[str] = None,
        bank_account: Optional[str] = None,
        remarks: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Customer create: name={name}")

            customer_type_enum = CustomerType(customer_type) if customer_type else CustomerType.COMPANY

            customer_data = CustomerCreate(
                name=name,
                customer_type=customer_type_enum,
                level=level,
                contact_person=contact_person,
                contact_phone=contact_phone,
                contact_email=contact_email,
                address=address,
                tax_number=tax_number,
                bank_name=bank_name,
                bank_account=bank_account,
                remarks=remarks
            )

            customer_code, db_id = await customer_service.create_customer(customer_data)

            return ToolResult(
                success=True,
                content=f"客户创建成功！客户编码: {customer_code}",
                metadata={"customer_code": customer_code, "db_id": db_id}
            )

        except Exception as e:
            logger.error(f"Customer create failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class CustomerDetailTool(BaseTool):
    name = "customer_detail"
    cn_name = "客户详情管理"
    description = "管理客户详情。当用户要求修改客户信息、更新客户资料、管理客户收货地址时使用。"
    permission_code = "customer.edit"
    parameters = {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "客户编码（必填）",
                "example": "CUST202401010001"
            },
            "action": {
                "type": "string",
                "description": "操作类型：update_info(更新客户信息)、add_address(添加收货地址)、update_address(更新收货地址)、delete_address(删除收货地址)、set_default_address(设默认收货地址)",
                "example": "update_info"
            },
            "name": {
                "type": "string",
                "description": "客户名称",
                "example": "深圳市新公司名称"
            },
            "customer_type": {
                "type": "string",
                "description": "客户类型：individual(个人)、company(企业)、government(政府)",
                "example": "enterprise"
            },
            "level": {
                "type": "string",
                "description": "客户级别：vip、potential、normal",
                "example": "vip"
            },
            "status": {
                "type": "string",
                "description": "客户状态：normal、inactive、blacklisted",
                "example": "normal"
            },
            "contact_person": {
                "type": "string",
                "description": "联系人",
                "example": "李四"
            },
            "contact_phone": {
                "type": "string",
                "description": "联系电话",
                "example": "13900139000"
            },
            "contact_email": {
                "type": "string",
                "description": "联系邮箱",
                "example": "lisi@example.com"
            },
            "address": {
                "type": "string",
                "description": "客户地址",
                "example": "深圳市福田区CBD"
            },
            "city": {
                "type": "string",
                "description": "城市",
                "example": "深圳"
            },
            "province": {
                "type": "string",
                "description": "省份",
                "example": "广东"
            },
            "industry": {
                "type": "string",
                "description": "行业",
                "example": "科技"
            },
            "tax_number": {
                "type": "string",
                "description": "税号",
                "example": "91440300MA5xxxxx"
            },
            "bank_name": {
                "type": "string",
                "description": "开户银行",
                "example": "工商银行深圳分行"
            },
            "bank_account": {
                "type": "string",
                "description": "银行账号",
                "example": "6222021234567890"
            },
            "credit_limit": {
                "type": "number",
                "description": "信用额度",
                "example": 100000
            },
            "remarks": {
                "type": "string",
                "description": "备注",
                "example": "重要客户"
            },
            "address_id": {
                "type": "string",
                "description": "收货地址编码（更新/删除/设默认地址时必填）",
                "example": "ADDR202401010001"
            },
            "recipient_name": {
                "type": "string",
                "description": "收货人姓名",
                "example": "王五"
            },
            "recipient_phone": {
                "type": "string",
                "description": "收货人电话",
                "example": "13700137000"
            },
            "district": {
                "type": "string",
                "description": "区县",
                "example": "南山区"
            },
            "is_default": {
                "type": "boolean",
                "description": "是否设为默认地址",
                "default": False,
                "example": False
            }
        },
        "required": ["customer_id", "action"]
    }

    async def execute(
        self,
        customer_id: str,
        action: str,
        name: Optional[str] = None,
        customer_type: Optional[str] = None,
        level: Optional[str] = None,
        status: Optional[str] = None,
        contact_person: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        industry: Optional[str] = None,
        tax_number: Optional[str] = None,
        bank_name: Optional[str] = None,
        bank_account: Optional[str] = None,
        credit_limit: Optional[float] = None,
        remarks: Optional[str] = None,
        address_id: Optional[str] = None,
        recipient_name: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        district: Optional[str] = None,
        is_default: bool = False,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Customer detail: customer_id={customer_id}, action={action}")

            if action == "update_info":
                return await self._update_customer_info(
                    customer_id, name, customer_type, level, status,
                    contact_person, contact_phone, contact_email, address,
                    city, province, industry, tax_number, bank_name,
                    bank_account, credit_limit, remarks
                )
            elif action == "add_address":
                return await self._add_address(
                    customer_id, recipient_name, recipient_phone,
                    province, city, district, address, is_default
                )
            elif action == "update_address":
                return await self._update_address(
                    customer_id, address_id, recipient_name, recipient_phone,
                    province, city, district, address, is_default
                )
            elif action == "delete_address":
                return await self._delete_address(customer_id, address_id)
            elif action == "set_default_address":
                return await self._set_default_address(customer_id, address_id)
            else:
                return ToolResult(
                    success=False,
                    content=f"无效的操作类型: {action}，可选: update_info/add_address/update_address/delete_address/set_default_address"
                )

        except Exception as e:
            logger.error(f"Customer detail failed: {e}")
            return ToolResult(success=False, content="", error=str(e))

    async def _update_customer_info(
        self,
        customer_id: str,
        name: Optional[str],
        customer_type: Optional[str],
        level: Optional[str],
        status: Optional[str],
        contact_person: Optional[str],
        contact_phone: Optional[str],
        contact_email: Optional[str],
        address: Optional[str],
        city: Optional[str],
        province: Optional[str],
        industry: Optional[str],
        tax_number: Optional[str],
        bank_name: Optional[str],
        bank_account: Optional[str],
        credit_limit: Optional[float],
        remarks: Optional[str]
    ) -> ToolResult:
        update_data = CustomerUpdate()
        if name is not None:
            update_data.name = name
        if customer_type is not None:
            update_data.customer_type = CustomerType(customer_type)
        if level is not None:
            update_data.level = level
        if status is not None:
            update_data.status = status
        if contact_person is not None:
            update_data.contact_person = contact_person
        if contact_phone is not None:
            update_data.contact_phone = contact_phone
        if contact_email is not None:
            update_data.contact_email = contact_email
        if address is not None:
            update_data.address = address
        if city is not None:
            update_data.city = city
        if province is not None:
            update_data.province = province
        if industry is not None:
            update_data.industry = industry
        if tax_number is not None:
            update_data.tax_number = tax_number
        if bank_name is not None:
            update_data.bank_name = bank_name
        if bank_account is not None:
            update_data.bank_account = bank_account
        if credit_limit is not None:
            update_data.credit_limit = credit_limit
        if remarks is not None:
            update_data.remarks = remarks

        success = await customer_service.update_customer(customer_id, update_data)

        if success:
            return ToolResult(success=True, content="客户信息更新成功")
        else:
            return ToolResult(success=False, content="客户信息更新失败")

    async def _add_address(
        self,
        customer_id: str,
        recipient_name: Optional[str],
        recipient_phone: Optional[str],
        province: Optional[str],
        city: Optional[str],
        district: Optional[str],
        address: Optional[str],
        is_default: bool
    ) -> ToolResult:
        addr_data = ShippingAddressCreate(
            recipient_name=recipient_name or "",
            recipient_phone=recipient_phone or "",
            province=province or "",
            city=city or "",
            district=district or "",
            address=address or "",
            is_default=is_default
        )
        result = await customer_service.add_shipping_address(customer_id, addr_data)
        if result:
            return ToolResult(success=True, content="收货地址添加成功", metadata=result)
        else:
            return ToolResult(success=False, content="收货地址添加失败")

    async def _update_address(
        self,
        customer_id: str,
        address_id: Optional[str],
        recipient_name: Optional[str],
        recipient_phone: Optional[str],
        province: Optional[str],
        city: Optional[str],
        district: Optional[str],
        address: Optional[str],
        is_default: bool
    ) -> ToolResult:
        if not address_id:
            return ToolResult(success=False, content="更新地址需要提供address_id")
        addr_data = ShippingAddressUpdate(
            receiver_name=recipient_name,
            receiver_phone=recipient_phone,
            province=province,
            city=city,
            district=district,
            address=address,
            is_default=is_default
        )
        success = await customer_service.update_shipping_address(
            customer_id, address_id, addr_data
        )
        return ToolResult(
            success=success,
            content="收货地址更新成功" if success else "收货地址更新失败"
        )

    async def _delete_address(self, customer_id: str, address_id: Optional[str]) -> ToolResult:
        if not address_id:
            return ToolResult(success=False, content="删除地址需要提供address_id")
        success = await customer_service.delete_shipping_address(customer_id, address_id)
        return ToolResult(
            success=success,
            content="收货地址删除成功" if success else "收货地址删除失败"
        )

    async def _set_default_address(self, customer_id: str, address_id: Optional[str]) -> ToolResult:
        if not address_id:
            return ToolResult(success=False, content="设默认需要提供address_id")
        success = await customer_service.set_default_shipping_address(customer_id, address_id)
        return ToolResult(
            success=success,
            content="默认地址设置成功" if success else "默认地址设置失败"
        )


class CustomerStatsTool(BaseTool):
    name = "customer_stats"
    cn_name = "客户统计"
    description = "获取客户统计信息。当用户询问客户总数、客户构成、客户分析等统计类问题时使用。"
    permission_code = "customer.view"
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    async def execute(self, **kwargs) -> ToolResult:
        try:
            stats = await customer_service.get_customer_stats()

            content_lines = ["客户统计信息："]
            content_lines.append(f"总客户数: {stats.get('total', 0)}")
            content_lines.append(f"VIP客户: {stats.get('vip_count', 0)}")
            content_lines.append(f"潜在客户: {stats.get('potential_count', 0)}")

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata=stats
            )

        except Exception as e:
            logger.error(f"Customer stats query failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


def register_customer_tools():
    from app.agent import agent_manager

    agent_manager.register_tool(CustomerSearchTool())
    agent_manager.register_tool(CustomerCreateTool())
    agent_manager.register_tool(CustomerDetailTool())
    agent_manager.register_tool(CustomerStatsTool())
    logger.info("Customer tools registered")
