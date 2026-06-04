"""
客户管理模块服务层 - MySQL 版本
"""
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from urllib.parse import quote

from tortoise.expressions import Q, F
from tortoise.transactions import atomic

from models_mysql.customer import Customer, InvoiceInfo, ShippingAddress, CustomerDiscount, CustomerResearchGroup

logger = logging.getLogger(__name__)


class CustomerService:
    """客户服务"""

    def _generate_customer_code(self) -> str:
        """生成客户编码"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"CUST{date_str}{random_str}"

    # ============ CRUD 方法 ============

    async def create_customer(self, customer_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """创建客户"""
        customer_name = customer_data.get("customer_name")
        if not customer_name:
            raise ValueError("客户名称不能为空")

        customer_type = customer_data.get("customer_type")
        if not customer_type:
            raise ValueError("客户类型不能为空")

        # 生成客户编码
        customer_code = customer_data.get("customer_code") or self._generate_customer_code()

        # 检查编码唯一性
        existing = await Customer.filter(customer_code=customer_code).first()
        if existing:
            customer_code = self._generate_customer_code()

        # 判断是否管理员
        user_roles = [
            role.get("code") if isinstance(role, dict) else role
            for role in current_user.get("roles", [])
        ]
        is_admin = "super_admin" in user_roles or "admin" in user_roles

        # 创建客户
        customer = await Customer.create(
            customer_code=customer_code,
            customer_name=customer_name,
            customer_type=customer_type,
            customer_status=customer_data.get("customer_status", 1),
            settlement_method=customer_data.get("settlement_method", 1),
            contact_person=customer_data.get("contact_person"),
            contact_phone=customer_data.get("contact_phone"),
            province=customer_data.get("province"),
            city=customer_data.get("city"),
            district=customer_data.get("district"),
            address=customer_data.get("address"),
            remark=customer_data.get("remark"),
            sales_user_id=customer_data.get("sales_user_id") or current_user.get("id"),
            sales_user_name=customer_data.get("sales_user_name") or current_user.get("full_name") or current_user.get("username"),
            created_by=current_user.get("id"),
            member_account=customer_data.get("member_account"),
            credit_limit=customer_data.get("credit_limit", 0),
            credit_days=customer_data.get("credit_days", 0),
        )

        # 创建课题组信息（终端客户时）
        research_groups_data = customer_data.get("research_groups", [])
        if customer_type == "terminal" and research_groups_data:
            for rg in research_groups_data:
                await CustomerResearchGroup.create(
                    customer=customer,
                    research_group_name=rg.get("research_group_name", ""),
                    research_leader=rg.get("research_leader"),
                    contact_phone=rg.get("contact_phone"),
                )

        # 创建开票信息
        await self._create_invoice_infos(customer, customer_data.get("invoice_infos", []))

        # 创建收货地址
        await self._create_shipping_addresses(customer, customer_data.get("shipping_addresses", []))

        return await self.get_customer_by_id(customer.id)

    async def update_customer(self, customer_id: int, customer_data: Dict[str, Any], current_user: Dict[str, Any] = None) -> bool:
        """更新客户"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        # 判断是否管理员
        is_admin = False
        if current_user:
            user_roles = [
                role.get("code") if isinstance(role, dict) else role
                for role in current_user.get("roles", [])
            ]
            is_admin = "super_admin" in user_roles or "admin" in user_roles

        # 公共池客户编辑校验（非管理员不可编辑）
        if customer.customer_status == 2 and not is_admin:
            raise ValueError("公共池客户不可编辑，请先认领")

        # 更新客户基本信息
        updatable_fields = [
            "customer_name", "customer_type", "customer_status",
            "settlement_method", "contact_person", "contact_phone",
            "province", "city", "district", "address", "remark",
            "sales_user_id", "sales_user_name",
            "member_account", "credit_limit", "credit_days",
            "default_shipping_address_id", "default_invoice_info_id", "default_tax_rate",
        ]
        for field in updatable_fields:
            if field in customer_data:
                setattr(customer, field, customer_data[field])

        await customer.save()

        # 更新课题组信息（先删后建）
        if "research_groups" in customer_data:
            await CustomerResearchGroup.filter(customer_id=customer_id).delete()
            research_groups_data = customer_data["research_groups"]
            if customer.customer_type == "terminal" and research_groups_data:
                for rg in research_groups_data:
                    await CustomerResearchGroup.create(
                        customer_id=customer_id,
                        research_group_name=rg.get("research_group_name", ""),
                        research_leader=rg.get("research_leader"),
                        contact_phone=rg.get("contact_phone"),
                    )

        # 更新开票信息（整体替换）
        if "invoice_infos" in customer_data:
            await InvoiceInfo.filter(customer_id=customer_id).delete()
            await self._create_invoice_infos(customer, customer_data["invoice_infos"])

        # 更新收货地址（整体替换）
        if "shipping_addresses" in customer_data:
            await ShippingAddress.filter(customer_id=customer_id).delete()
            await self._create_shipping_addresses(customer, customer_data["shipping_addresses"])

        return True

    async def delete_customer(self, customer_id: int) -> bool:
        """删除客户（级联删除关联数据）"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        await customer.delete()
        return True

    async def get_customer_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取客户详情"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            return None

        result = customer.to_dict()

        # 获取关联的课题组信息
        research_groups = await CustomerResearchGroup.filter(customer_id=customer_id).all()
        result["research_groups"] = [rg.to_dict() for rg in research_groups]

        # 获取关联的开票信息
        invoice_infos = await InvoiceInfo.filter(customer_id=customer_id).all()
        result["invoice_infos"] = [inv.to_dict() for inv in invoice_infos]

        # 获取关联的收货地址
        shipping_addresses = await ShippingAddress.filter(customer_id=customer_id).all()
        result["shipping_addresses"] = [addr.to_dict() for addr in shipping_addresses]

        # 获取关联的折扣
        discounts = await CustomerDiscount.filter(customer_id=customer_id).all()
        result["discounts"] = [d.to_dict() for d in discounts]

        return result

    async def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        customer_status: Optional[int] = None,
        customer_type: Optional[str] = None,
        sales_user_id: Optional[int] = None,
        keyword: Optional[str] = None,
        created_at_start: Optional[str] = None,
        created_at_end: Optional[str] = None,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取客户列表，支持权限过滤（普通用户按 created_by 过滤）"""
        query = Customer.all()

        if customer_status is not None:
            query = query.filter(customer_status=customer_status)
        if customer_type:
            query = query.filter(customer_type=customer_type)
        if sales_user_id:
            query = query.filter(sales_user_id=sales_user_id)
        if keyword:
            query = query.filter(
                Q(customer_code__contains=keyword) | Q(customer_name__contains=keyword)
            )
        if created_at_start:
            query = query.filter(created_at__gte=created_at_start)
        if created_at_end:
            query = query.filter(created_at__lte=created_at_end)

        # 权限过滤：普通用户按 created_by 过滤，管理员不过滤
        if not is_admin and user_id:
            query = query.filter(created_by=user_id)

        total = await query.count()
        customers = await query.offset((page - 1) * page_size).limit(page_size)

        return [c.to_dict() for c in customers], total

    async def get_customer_stats(self) -> Dict[str, Any]:
        """获取客户统计"""
        total = await Customer.all().count()
        normal_count = await Customer.filter(customer_status=1).count()
        pool_count = await Customer.filter(customer_status=2).count()
        terminal_count = await Customer.filter(customer_type="terminal").count()
        dealer_count = await Customer.filter(customer_type="dealer").count()
        overdue_count = await Customer.filter(is_overdue=1).count()
        return {
            "total": total,
            "normal_count": normal_count,
            "pool_count": pool_count,
            "terminal_count": terminal_count,
            "dealer_count": dealer_count,
            "overdue_count": overdue_count,
        }

    async def update_status(self, customer_id: int, customer_status: int) -> bool:
        """更新客户状态"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        if customer_status not in (1, 2):
            raise ValueError("客户状态值无效，允许值: 1=正常, 2=公共池")

        customer.customer_status = customer_status
        await customer.save()
        return True

    async def transfer_customer(self, customer_id: int, new_sales_user_id: int, new_sales_user_name: str) -> bool:
        """转移客户给另一个销售"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        if customer.customer_status == 2:
            raise ValueError("公共池客户不可转移，请先认领")

        customer.sales_user_id = new_sales_user_id
        customer.sales_user_name = new_sales_user_name
        await customer.save()
        return True

    # ============ 辅助方法 ============

    async def _create_invoice_infos(self, customer, invoice_infos_data: list):
        """批量创建开票信息"""
        for idx, inv_data in enumerate(invoice_infos_data):
            await InvoiceInfo.create(
                customer=customer,
                invoice_title=inv_data.get("invoice_title"),
                tax_number=inv_data.get("tax_number"),
                bank_name=inv_data.get("bank_name"),
                bank_account=inv_data.get("bank_account"),
                address_phone=inv_data.get("address_phone"),
                is_default=inv_data.get("is_default", idx == 0),
            )

    async def _create_shipping_addresses(self, customer, shipping_addresses_data: list):
        """批量创建收货地址"""
        for idx, addr_data in enumerate(shipping_addresses_data):
            await ShippingAddress.create(
                customer=customer,
                receiver=addr_data.get("receiver"),
                phone=addr_data.get("phone"),
                province=addr_data.get("province"),
                province_code=addr_data.get("province_code"),
                city=addr_data.get("city"),
                city_code=addr_data.get("city_code"),
                district=addr_data.get("district"),
                address=addr_data.get("address"),
                is_default=addr_data.get("is_default", idx == 0),
            )

    # ============ 客户认领 ============

    async def claim_customer(self, customer_id: int, user_id: int, user_name: str) -> dict:
        """客户认领：从公共池认领客户恢复为正常状态（并发安全，使用filter+update原子操作）"""
        affected = await Customer.filter(id=customer_id, customer_status=2).update(
            customer_status=1,
            sales_user_id=user_id,
            sales_user_name=user_name,
        )
        if affected == 0:
            customer = await Customer.get_or_none(id=customer_id)
            if not customer:
                raise ValueError("客户不存在")
            raise ValueError("该客户不在公共池中，无法认领")

        return {"message": "认领成功", "customer_id": customer_id}

    # ============ 注册会员 ============

    async def register_member(self, customer_id: int, member_account: str) -> dict:
        """为客户注册会员账号"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")
        if customer.customer_status != 1:
            raise ValueError("公共池客户不可注册会员")

        # 校验会员账号唯一性
        existing = await Customer.filter(member_account=member_account).exclude(id=customer_id).first()
        if existing:
            raise ValueError("该会员账号已被使用")

        customer.member_account = member_account
        await customer.save()

        return {"message": "会员账号设置成功", "member_account": member_account}

    # ============ 订单默认值设置 ============

    async def set_order_defaults(self, customer_id: int, data: dict) -> dict:
        """设置客户订单默认值（默认收货地址、开票信息、结算方式、税率）"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        # 校验默认收货地址属于该客户
        shipping_id = data.get("default_shipping_address_id")
        if shipping_id:
            addr = await ShippingAddress.get_or_none(id=shipping_id, customer_id=customer_id)
            if not addr:
                raise ValueError("收货地址不属于该客户")
            customer.default_shipping_address_id = shipping_id

        # 校验默认开票信息属于该客户
        invoice_id = data.get("default_invoice_info_id")
        if invoice_id:
            inv = await InvoiceInfo.get_or_none(id=invoice_id, customer_id=customer_id)
            if not inv:
                raise ValueError("开票信息不属于该客户")
            customer.default_invoice_info_id = invoice_id

        if "settlement_method" in data:
            customer.settlement_method = data["settlement_method"]
        if "default_tax_rate" in data:
            customer.default_tax_rate = data["default_tax_rate"]

        await customer.save()
        return {"message": "订单默认值设置成功"}

    # ============ 账期额度设置 ============

    async def set_credit(self, customer_id: int, credit_days: int, credit_limit: float) -> dict:
        """设置客户账期天数和信用额度"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")
        if customer.customer_status != 1:
            raise ValueError("公共池客户不可设置账期额度")

        customer.credit_days = credit_days
        customer.credit_limit = credit_limit
        await customer.save()

        # 设置后自动触发超账期检查
        await self.check_and_update_overdue(customer_id)

        return {"message": "账期额度设置成功", "credit_days": credit_days, "credit_limit": credit_limit}

    # ============ 超账期判断 ============

    async def check_and_update_overdue(self, customer_id: int = None) -> dict:
        """
        检查并更新客户超账期状态
        customer_id: 指定客户ID检查单个，None检查所有符合条件的客户
        """
        if customer_id:
            customer = await Customer.get_or_none(id=customer_id)
            customers = [customer] if customer else []
        else:
            # 查询所有正常状态、有账期天数、有尾单时间的客户
            customers = await Customer.filter(
                customer_status=1,
                credit_days__gt=0,
                last_order_time__not_isnull=True,
            )

        overdue_count = 0
        for customer in customers:
            if not customer or not customer.last_order_time or customer.credit_days <= 0:
                continue

            days_since_last_order = (datetime.now() - customer.last_order_time).days
            new_overdue = 1 if days_since_last_order > customer.credit_days else 0

            if customer.is_overdue != new_overdue:
                customer.is_overdue = new_overdue
                await customer.save(update_fields=["is_overdue"])

            if new_overdue:
                overdue_count += 1

        return {"overdue_count": overdue_count, "checked_count": len(customers)}

    async def check_overdue_status(self) -> dict:
        """批量超账期判断，返回超账期统计信息"""
        result = await self.check_and_update_overdue()
        overdue_customers = await Customer.filter(is_overdue=1).values(
            "id", "customer_name", "customer_code", "credit_days", "last_order_time"
        )
        return {
            "overdue_count": result["overdue_count"],
            "overdue_customers": list(overdue_customers),
        }

    # ============ 批量导出 ============

    async def export_customers(self, customer_ids: list = None, filters: dict = None,
                               user_id: int = None, is_admin: bool = False):
        """批量导出客户数据为Excel"""
        from io import BytesIO
        from openpyxl import Workbook
        from fastapi.responses import StreamingResponse

        # 构建查询
        query = Customer.all()

        if customer_ids:
            query = query.filter(id__in=customer_ids)

        if filters:
            if filters.get("customer_status"):
                query = query.filter(customer_status=filters["customer_status"])
            if filters.get("customer_type"):
                query = query.filter(customer_type=filters["customer_type"])
            if filters.get("sales_user_id"):
                query = query.filter(sales_user_id=filters["sales_user_id"])
            if filters.get("created_at_start"):
                query = query.filter(created_at__gte=filters["created_at_start"])
            if filters.get("created_at_end"):
                query = query.filter(created_at__lte=filters["created_at_end"])

        # 权限过滤
        if not is_admin and user_id:
            query = query.filter(created_by=user_id)

        customers = await query

        # 创建 Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "客户数据"

        # 表头
        headers = ["客户编码", "客户名称", "客户类型", "客户状态", "业务员", "结算方式",
                   "账户余额", "欠款总额", "信用额度", "账期天数", "是否超账期", "会员账号",
                   "尾单时间", "成单金额", "创建时间", "创建人", "联系电话", "所属区域"]
        ws.append(headers)

        # 数据行
        status_map = {1: "正常", 2: "公共池"}
        type_map = {"terminal": "终端", "dealer": "经销商"}
        settlement_map = {1: "月结", 2: "现结", 3: "预付"}

        for c in customers:
            row = [
                c.customer_code,
                c.customer_name,
                type_map.get(c.customer_type, c.customer_type),
                status_map.get(c.customer_status, str(c.customer_status)),
                c.sales_user_name or "",
                settlement_map.get(c.settlement_method, str(c.settlement_method)),
                float(c.account_balance) if c.account_balance else 0,
                float(c.debt_total) if c.debt_total else 0,
                float(c.credit_limit) if c.credit_limit else 0,
                c.credit_days,
                "是" if c.is_overdue else "否",
                c.member_account or "",
                c.last_order_time.strftime("%Y-%m-%d") if c.last_order_time else "",
                float(c.total_order_amount) if c.total_order_amount else 0,
                c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else "",
                c.created_by or "",
                c.contact_phone or "",
                f"{c.province or ''}{c.city or ''}{c.district or ''}",
            ]
            ws.append(row)

        # 输出
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        filename = f"客户数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
        )

    # ============ 预留接口，供销售/财务模块调用 ============

    async def update_account_balance(self, customer_id: int, delta: float) -> None:
        """增量更新客户账户余额 - 预留接口，供财务模块调用（并发安全）"""
        affected = await Customer.filter(id=customer_id).update(
            account_balance=F('account_balance') + Decimal(str(delta))
        )
        if affected == 0:
            raise ValueError("客户不存在")

    async def update_debt_total(self, customer_id: int, delta: float) -> None:
        """增量更新客户欠款总额 - 预留接口，供财务模块调用（并发安全）"""
        affected = await Customer.filter(id=customer_id).update(
            debt_total=F('debt_total') + Decimal(str(delta))
        )
        if affected == 0:
            raise ValueError("客户不存在")

    async def update_last_order_time(self, customer_id: int, order_time: datetime) -> None:
        """更新客户尾单时间 - 预留接口，供销售模块调用（同时触发超账期检查）"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")
        customer.last_order_time = order_time
        await customer.save(update_fields=["last_order_time"])
        # 更新尾单时间后自动检查超账期
        await self.check_and_update_overdue(customer_id)

    async def update_total_order_amount(self, customer_id: int, delta: float) -> None:
        """增量更新客户成单金额 - 预留接口，供销售模块调用（并发安全）"""
        affected = await Customer.filter(id=customer_id).update(
            total_order_amount=F('total_order_amount') + Decimal(str(delta))
        )
        if affected == 0:
            raise ValueError("客户不存在")

    # ============ 公共池自动转换预留方法 ============

    async def check_and_convert_to_pool(self) -> dict:
        """
        检查超过6个月未成单的客户，自动转入公共池
        预留接口，供定时任务模块调用，当前不自动执行
        """
        cutoff_date = datetime.now() - timedelta(days=180)

        # 查询正常状态、尾单时间超过6个月的客户
        overdue_customers = await Customer.filter(
            customer_status=1,
            last_order_time__lt=cutoff_date,
            last_order_time__not_isnull=True,
        )

        converted_count = 0
        for customer in overdue_customers:
            customer.customer_status = 2
            customer.sales_user_id = None
            customer.sales_user_name = None
            await customer.save(update_fields=["customer_status", "sales_user_id", "sales_user_name"])
            converted_count += 1

        return {
            "converted_count": converted_count,
            "message": f"已将 {converted_count} 个超期客户转入公共池"
        }

    async def search_customers(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        根据关键词搜索客户（用于下拉选择等）

        Args:
            keyword: 搜索关键词
            limit: 返回数量，最多5条

        Returns:
            客户列表，包含 id/name/code 字段
        """
        customers = await Customer.filter(
            Q(customer_name__icontains=keyword) | Q(customer_code__icontains=keyword)
        ).limit(min(limit, 5)).all()
        return [
            {
                "id": c.id,
                "name": c.customer_name,
                "code": c.customer_code
            }
            for c in customers
        ]


class CustomerDiscountService:
    """客户折扣服务"""

    async def create_discount(self, discount_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建客户折扣"""
        customer_id = discount_data.get("customer_id")
        brand_id = discount_data.get("brand_id")

        if not customer_id or not brand_id:
            raise ValueError("客户ID和品牌ID不能为空")

        # 检查客户是否存在
        customer = await Customer.get_or_none(id=int(customer_id))
        if not customer:
            raise ValueError("客户不存在")

        # 检查是否已存在
        existing = await CustomerDiscount.filter(
            customer_id=int(customer_id), brand_id=int(brand_id)
        ).first()
        if existing:
            raise ValueError("该客户和品牌的折扣配置已存在")

        # 获取品牌名称
        from services.product_service_mysql import brand_service
        brand_name = await brand_service.get_brand_name(int(brand_id))

        discount = await CustomerDiscount.create(
            customer_id=int(customer_id),
            brand_id=int(brand_id),
            brand_name=brand_name,
            discount_value=discount_data.get("discount_value", 1.0),
            is_active=discount_data.get("is_active", True),
        )

        return discount.to_dict()

    async def update_discount(self, discount_id: int, discount_data: Dict[str, Any]) -> bool:
        """更新客户折扣"""
        discount = await CustomerDiscount.get_or_none(id=discount_id)
        if not discount:
            raise ValueError("客户折扣不存在")

        if "discount_value" in discount_data:
            discount.discount_value = discount_data["discount_value"]
        if "is_active" in discount_data:
            discount.is_active = discount_data["is_active"]

        await discount.save()
        return True

    async def delete_discount(self, discount_id: int) -> bool:
        """删除客户折扣"""
        discount = await CustomerDiscount.get_or_none(id=discount_id)
        if not discount:
            raise ValueError("客户折扣不存在")

        await discount.delete()
        return True

    async def list_discounts(
        self,
        page: int = 1,
        page_size: int = 20,
        customer_id: Optional[int] = None,
        brand_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取客户折扣列表"""
        query = CustomerDiscount.all()

        if customer_id:
            query = query.filter(customer_id=customer_id)
        if brand_id:
            query = query.filter(brand_id=brand_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)

        total = await query.count()
        discounts = await query.offset((page - 1) * page_size).limit(page_size)

        return [d.to_dict() for d in discounts], total

    async def get_discount_by_id(self, discount_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取折扣"""
        discount = await CustomerDiscount.get_or_none(id=discount_id)
        if not discount:
            return None
        return discount.to_dict()

    async def get_discount_by_customer_and_brand(
        self, customer_id: int, brand_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取指定客户和品牌的折扣"""
        discount = await CustomerDiscount.filter(
            customer_id=customer_id, brand_id=brand_id
        ).first()
        if not discount:
            return None
        return discount.to_dict()

    async def toggle_discount_status(self, discount_id: int, is_active: bool) -> bool:
        """切换折扣状态"""
        discount = await CustomerDiscount.get_or_none(id=discount_id)
        if not discount:
            raise ValueError("客户折扣不存在")

        discount.is_active = is_active
        await discount.save()
        return True


# 创建服务实例
customer_service = CustomerService()
customer_discount_service = CustomerDiscountService()