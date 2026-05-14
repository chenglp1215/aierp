"""
客户管理模块服务层 - MySQL 版本
"""
import random
import string
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from tortoise.expressions import Q

from models_mysql.customer import Customer, InvoiceInfo, ShippingAddress, CustomerDiscount

logger = logging.getLogger(__name__)


class CustomerService:
    """客户服务"""

    def _generate_customer_code(self) -> str:
        """生成客户编码"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"CUST{date_str}{random_str}"

    async def create_customer(self, customer_data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        """创建客户"""
        name = customer_data.get("name")
        if not name:
            raise ValueError("客户名称不能为空")

        customer_type = customer_data.get("customer_type")
        if not customer_type:
            raise ValueError("客户类型不能为空")

        # 生成客户编码
        customer_code = self._generate_customer_code()

        # 检查编码唯一性
        existing = await Customer.filter(customer_code=customer_code).first()
        if existing:
            customer_code = self._generate_customer_code()

        # 创建客户
        customer = await Customer.create(
            customer_code=customer_code,
            name=name,
            customer_type=customer_type,
            research_group=customer_data.get("research_group"),
            contact_person=customer_data.get("contact_person"),
            contact_phone=customer_data.get("contact_phone"),
            contact_email=customer_data.get("contact_email"),
            sales_user_id=current_user.get("id"),
            sales_user_name=current_user.get("full_name") or current_user.get("username"),
            status=customer_data.get("status", "normal"),
        )

        # 创建开票信息
        invoice_infos_data = customer_data.get("invoice_infos", [])
        for idx, inv_data in enumerate(invoice_infos_data):
            await InvoiceInfo.create(
                customer=customer,
                invoice_title=inv_data.get("invoice_title"),
                invoice_type=inv_data.get("invoice_type"),
                tax_number=inv_data.get("tax_number"),
                bank_name=inv_data.get("bank_name"),
                bank_account=inv_data.get("bank_account"),
                is_default=inv_data.get("is_default", idx == 0),
            )

        # 创建收货地址
        shipping_addresses_data = customer_data.get("shipping_addresses", [])
        for idx, addr_data in enumerate(shipping_addresses_data):
            await ShippingAddress.create(
                customer=customer,
                recipient_name=addr_data.get("recipient_name"),
                recipient_phone=addr_data.get("recipient_phone"),
                province=addr_data.get("province"),
                province_code=addr_data.get("province_code"),
                city=addr_data.get("city"),
                city_code=addr_data.get("city_code"),
                district=addr_data.get("district"),
                address=addr_data.get("address"),
                is_default=addr_data.get("is_default", idx == 0),
            )

        return await self.get_customer_by_id(customer.id)

    async def update_customer(self, customer_id: int, customer_data: Dict[str, Any]) -> bool:
        """更新客户"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        # 更新客户基本信息
        if "name" in customer_data:
            customer.name = customer_data["name"]
        if "customer_type" in customer_data:
            customer.customer_type = customer_data["customer_type"]
        if "research_group" in customer_data:
            customer.research_group = customer_data["research_group"]
        if "contact_person" in customer_data:
            customer.contact_person = customer_data["contact_person"]
        if "contact_phone" in customer_data:
            customer.contact_phone = customer_data["contact_phone"]
        if "contact_email" in customer_data:
            customer.contact_email = customer_data["contact_email"]
        if "status" in customer_data:
            customer.status = customer_data["status"]

        await customer.save()

        # 更新开票信息（整体替换）
        if "invoice_infos" in customer_data:
            await InvoiceInfo.filter(customer_id=customer_id).delete()
            for idx, inv_data in enumerate(customer_data["invoice_infos"]):
                await InvoiceInfo.create(
                    customer=customer,
                    invoice_title=inv_data.get("invoice_title"),
                    invoice_type=inv_data.get("invoice_type"),
                    tax_number=inv_data.get("tax_number"),
                    bank_name=inv_data.get("bank_name"),
                    bank_account=inv_data.get("bank_account"),
                    is_default=inv_data.get("is_default", idx == 0),
                )

        # 更新收货地址（整体替换）
        if "shipping_addresses" in customer_data:
            await ShippingAddress.filter(customer_id=customer_id).delete()
            for idx, addr_data in enumerate(customer_data["shipping_addresses"]):
                await ShippingAddress.create(
                    customer=customer,
                    recipient_name=addr_data.get("recipient_name"),
                    recipient_phone=addr_data.get("recipient_phone"),
                    province=addr_data.get("province"),
                    province_code=addr_data.get("province_code"),
                    city=addr_data.get("city"),
                    city_code=addr_data.get("city_code"),
                    district=addr_data.get("district"),
                    address=addr_data.get("address"),
                    is_default=addr_data.get("is_default", idx == 0),
                )

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

        # 获取关联的开票信息
        invoice_infos = await InvoiceInfo.filter(customer_id=customer_id).all()
        result["invoice_infos"] = [inv.to_dict() for inv in invoice_infos]

        # 获取关联的收货地址
        shipping_addresses = await ShippingAddress.filter(customer_id=customer_id).all()
        result["shipping_addresses"] = [addr.to_dict() for addr in shipping_addresses]

        return result

    async def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        sales_user_id: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取客户列表"""
        query = Customer.all()

        if status:
            query = query.filter(status=status)
        if customer_type:
            query = query.filter(customer_type=customer_type)
        if sales_user_id:
            query = query.filter(sales_user_id=sales_user_id)
        if keyword:
            query = query.filter(
                Q(customer_code__contains=keyword) | Q(name__contains=keyword)
            )

        total = await query.count()
        customers = await query.offset((page - 1) * page_size).limit(page_size)

        return [c.to_dict() for c in customers], total

    async def get_customer_stats(self) -> Dict[str, Any]:
        """获取客户统计"""
        total = await Customer.all().count()
        terminal_count = await Customer.filter(customer_type="terminal").count()
        dealer_count = await Customer.filter(customer_type="dealer").count()
        return {
            "total": total,
            "terminal_count": terminal_count,
            "dealer_count": dealer_count,
        }

    async def update_status(self, customer_id: int, status: str) -> bool:
        """更新客户状态"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        customer.status = status
        await customer.save()
        return True

    async def transfer_customer(self, customer_id: int, new_sales_user_id: int, new_sales_user_name: str) -> bool:
        """转移客户给另一个销售"""
        customer = await Customer.get_or_none(id=customer_id)
        if not customer:
            raise ValueError("客户不存在")

        customer.sales_user_id = new_sales_user_id
        customer.sales_user_name = new_sales_user_name
        await customer.save()
        return True


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