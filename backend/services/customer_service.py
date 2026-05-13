"""
客户管理 - 服务层
全新设计的客户服务，提供完整的CRUD操作
"""
from typing import Optional, Dict, Any, List, Tuple
import uuid
from datetime import datetime

from .base_service import BaseService
from models.customer import (
    CustomerBase,
    CustomerDiscount,
    CustomerType,
    CustomerStatus
)

from validators.customer_validator import (
    CUSTOMER_CREATE_CONFIG,
    CUSTOMER_UPDATE_CONFIG,
    INVOICE_INFO_CREATE_CONFIG,
    INVOICE_INFO_UPDATE_CONFIG,
    SHIPPING_ADDRESS_CREATE_CONFIG,
    SHIPPING_ADDRESS_UPDATE_CONFIG,
    CUSTOMER_DISCOUNT_CREATE_CONFIG,
    CUSTOMER_DISCOUNT_UPDATE_CONFIG,
)

class CustomerService(BaseService):
    """客户服务类"""

    def __init__(self):
        super().__init__("customers")
        self.model = CustomerBase

    def _generate_customer_code(self) -> str:
        """生成客户编码"""
        import random
        import string
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"CUST{date_str}{random_str}"

    def _generate_id(self, prefix: str = "ID") -> str:
        """生成ID"""
        return f"{prefix}{uuid.uuid4().hex[:12].upper()}"

    def _ensure_single_default(self, customer_data) -> Dict:
        """确保只有一个默认项"""
        if invoice_infos := customer_data.get("invoice_infos", []):
            default_count = 0
            for info in invoice_infos:
                if default_count == 0 and info.get("is_default"):
                    default_count += 1
                    info["is_default"] = True   
                else:
                    info["is_default"] = False
        if shipping_addresses := customer_data.get("shipping_addresses", []):
            default_count = 0
            for address in shipping_addresses:
                if default_count == 0 and address.get("is_default"):
                    default_count += 1
                    address["is_default"] = True   
                else:
                    address["is_default"] = False
        return customer_data

    async def format(self, customer: Dict) -> Dict:
        """格式化客户数据"""
        return customer

    async def format_list(self, customers: List[Dict]) -> List[Dict]:
        """格式化客户列表"""
        return [await self.format(customer) for customer in customers]

    # ============ 验证方法 ============
    def validate_customer_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证客户创建数据"""
        return self.validate_data(data, CUSTOMER_CREATE_CONFIG)

    def validate_customer_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证客户更新数据"""
        return self.validate_data(data, CUSTOMER_UPDATE_CONFIG)

    # ============ 客户CRUD ============

    async def create_customer(self, customer_data: Dict[str, Any], current_user: Dict[str, Any]) -> CustomerBase:
        """创建客户"""
        is_valid, errors = self.validate_customer_create(customer_data)
        if not is_valid:
            raise ValueError(errors)
        data = customer_data.copy()
        data["customer_code"] = self._generate_customer_code()
        data["sales_user_id"] = current_user.get("id")
        data["sales_user_name"] = current_user.get("full_name") or current_user.get("username")
        data = self._ensure_single_default(data)
        customer_id = await self.create(data)
        return await self.get_by_id(customer_id)

    async def update_customer(self, customer_id: str, customer_data: Dict[str, Any]) -> bool:
        """更新客户"""
        is_valid, errors = self.validate_customer_update(customer_data)
        if not is_valid:
            raise ValueError(errors)
        data = customer_data.copy()
        print("--------------更新客户数据:", data)
        data = self._ensure_single_default(data)
        return await self.update(customer_id, data)


    async def delete_customer(self, customer_id: str) -> bool:
        """删除客户"""
        return await self.delete(customer_id)

    async def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        sales_user_id: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取客户列表"""
        filters = {}

        if status:
            filters["status"] = status
        if customer_type:
            filters["customer_type"] = customer_type
        if sales_user_id:
            filters["sales_user_id"] = sales_user_id
        if keyword:
            filters["$or"] = [
                {"customer_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
            ]
        result = await self.find_many(filters, limit=page_size, skip=(page - 1) * page_size, sort={"created_at": -1})
        total = await self.count(filters)
        return result, total

    async def get_customer_stats(self) -> Dict[str, Any]:
        """获取客户统计"""
        total = await self.count({})
        terminal_count = await self.count({"customer_type": CustomerType.TERMINAL.value})
        dealer_count = await self.count({"customer_type": CustomerType.DEALER.value})
        return {
            "total": total,
            "terminal_count": terminal_count,
            "dealer_count": dealer_count,
        }

    async def update_status(self, customer_id: str, status: CustomerStatus) -> bool:
        """更新客户状态"""
        return await self.update(customer_id, {"status": status.value})

    async def transfer_customer(self, customer_id: str, new_sales_user_id: str) -> bool:
        """转移客户给另一个销售"""
        from services.auth_service import AuthService

        auth_service = AuthService()
        new_user = await auth_service.get_user_by_id(new_sales_user_id)
        if not new_user:
            return False
        update_data = {
            "sales_user_id": new_sales_user_id,
            "sales_user_name": new_user.get("full_name") or new_user.get("username")
        }
        return await self.update(customer_id, update_data)

    # ============ 开票信息管理 ============

    async def add_invoice_info(
        self, customer_id: str, invoice_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """添加开票信息"""
        from bson import ObjectId

        customer = await self.get_by_id(customer_id)
        if not customer:
            return None

        invoice = invoice_data
        invoice["id"] = self._generate_id("INV")

        if invoice.get("is_default"):
            await self.collection.update_one(
                {"_id": customer["_id"]},
                {"$set": {"invoice_infos.$[].is_default": False}}
            )

        result = await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$push": {"invoice_infos": invoice}}
        )

        if result.modified_count > 0:
            return invoice
        return None

    async def update_invoice_info(
        self, customer_id: str, invoice_id: str, invoice_data: Dict[str, Any]
    ) -> bool:
        """更新开票信息"""
        from bson import ObjectId

        customer = await self.get_by_id(customer_id)
        if not customer:
            return False

        invoice = invoice_data
        if not invoice:
            return True

        if invoice.get("is_default"):
            await self.collection.update_one(
                {"_id": customer["_id"]},
                {"$set": {"invoice_infos.$[].is_default": False}}
            )

        update_fields = {}
        for key, value in invoice.items():
            update_fields[f"invoice_infos.$.{key}"] = value

        result = await self.collection.update_one(
            {"_id": customer["_id"], "invoice_infos.id": invoice_id},
            {"$set": update_fields}
        )

        return result.modified_count > 0 or result.matched_count > 0

    async def delete_invoice_info(self, customer_id: str, invoice_id: str) -> bool:
        """删除开票信息"""
        customer = await self.get_by_id(customer_id)
        if not customer:
            return False

        result = await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$pull": {"invoice_infos": {"id": invoice_id}}}
        )

        return result.modified_count > 0
    

    async def set_default_invoice_info(self, customer_id: str, invoice_id: str) -> bool:
        """设置默认开票信息"""
        customer = await self.get_by_id(customer_id)
        if not customer:
            return False

        await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$set": {"invoice_infos.$[].is_default": False}}
        )

        result = await self.collection.update_one(
            {"_id": customer["_id"], "invoice_infos.id": invoice_id},
            {"$set": {"invoice_infos.$.is_default": True}}
        )

        return result.modified_count > 0

    # ============ 收货地址管理 ============

    async def add_shipping_address(
        self, customer_id: str, address_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """添加收货地址"""
        from bson import ObjectId

        customer = await self.get_by_id(customer_id)
        if not customer:
            return None

        address = address_data
        address["id"] = self._generate_id("ADDR")

        if address.get("is_default"):
            await self.collection.update_one(
                {"_id": customer["_id"]},
                {"$set": {"shipping_addresses.$[].is_default": False}}
            )

        result = await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$push": {"shipping_addresses": address}}
        )

        if result.modified_count > 0:
            return address
        return None

    async def update_shipping_address(
        self, customer_id: str, address_id: str, address_data: Dict[str, Any]
    ) -> bool:
        """更新收货地址"""
        from bson import ObjectId

        customer = await self.get_by_id(customer_id)
        if not customer:
            return False

        address = address_data
        if not address:
            return True

        if address.get("is_default"):
            await self.collection.update_one(
                {"_id": customer["_id"]},
                {"$set": {"shipping_addresses.$[].is_default": False}}
            )

        update_fields = {}
        for key, value in address.items():
            update_fields[f"shipping_addresses.$.{key}"] = value

        result = await self.collection.update_one(
            {"_id": customer["_id"], "shipping_addresses.id": address_id},
            {"$set": update_fields}
        )

        return result.modified_count > 0 or result.matched_count > 0

    async def delete_shipping_address(self, customer_id: str, address_id: str) -> bool:
        """删除收货地址"""
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return False

        result = await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$pull": {"shipping_addresses": {"id": address_id}}}
        )

        return result.modified_count > 0

    async def set_default_shipping_address(self, customer_id: str, address_id: str) -> bool:
        """设置默认收货地址"""
        from bson import ObjectId

        customer = await self.get_by_id(customer_id)
        if not customer:
            return False

        await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$set": {"shipping_addresses.$[].is_default": False}}
        )

        result = await self.collection.update_one(
            {"_id": customer["_id"], "shipping_addresses.id": address_id},
            {"$set": {"shipping_addresses.$.is_default": True}}
        )

        return result.modified_count > 0

    # ============ 联系人信息管理 ============

    async def update_contact_info(
        self, customer_id: str, contact_data: Dict[str, Any]
    ) -> bool:
        """更新联系人信息"""
        from bson import ObjectId

        customer = await self.get_by_id(customer_id)
        if not customer:
            return False

        contact = contact_data
        if not contact:
            return True

        update_fields = {}
        for key, value in contact.items():
            update_fields[f"contact_info.{key}"] = value

        result = await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$set": update_fields}
        )

        return result.modified_count > 0 or result.matched_count > 0


class CustomerDiscountService(BaseService):
    """客户折扣服务类"""

    def __init__(self):
        super().__init__("customer_discounts")
        self.model = CustomerDiscount

    def _generate_id(self, prefix: str = "DIS") -> str:
        """生成ID"""
        import uuid
        return f"{prefix}{uuid.uuid4().hex[:12].upper()}"

    async def format(self, discount: Dict[str, Any]) -> Dict[str, Any]:
        """格式化折扣数据"""
        from services.product_service import brand_service
        brand_id = discount.get("brand_id")
        if brand := await brand_service.get_by_id(brand_id):
            discount["brand_name"] = brand["name"]
        else:
            discount["brand_name"] = None
        return discount

    async def format_list(self, discounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化折扣列表"""
        from services.product_service import brand_service
        brand_ids = [discount.get("brand_id") for discount in discounts]
        brand_name_map = {brand["id"]: brand["name"] for brand in await brand_service.get_by_ids(brand_ids)}
        for discount in discounts:
            brand_id = discount.get("brand_id")
            if brand_id in brand_name_map:
                discount["brand_name"] = brand_name_map.get(discount["brand_id"])
            else:
                discount["brand_name"] = None
        return discounts

    def validate_discount_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证折扣创建数据"""
        return self.validate_data(data, CUSTOMER_DISCOUNT_CREATE_CONFIG)

    def validate_discount_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证折扣更新数据"""
        return self.validate_data(data, CUSTOMER_DISCOUNT_UPDATE_CONFIG)

    async def create_discount(
        self, discount_data: Dict[str, Any]
    ) -> CustomerDiscount:
        """创建客户折扣"""
        is_valid, errors = self.validate_discount_create(discount_data)
        if not is_valid:
            raise ValueError(errors)
        data = discount_data.copy()
        data["id"] = self._generate_id("DIS")
        customer_id = data.get("customer_id")
        brand_id = data.get("brand_id")
        filters = {
            "customer_id": customer_id,
            "brand_id": brand_id
        }
        exists = await self.find_one(filters)
        if exists is not None:
            raise ValueError("该客户和品牌的折扣配置已存在")
        discount_id = await self.create(data)
        return await self.get_by_id(discount_id)

    async def update_discount(
        self, discount_id: str, discount_data: Dict[str, Any]
    ) -> bool:
        """更新客户折扣"""
        is_valid, errors = self.validate_discount_update(discount_data)
        if not is_valid:
            raise ValueError(errors)
        data = discount_data.copy()
        if not data:
            return True
        return await self.update(discount_id, data)

    async def delete_discount(self, discount_id: str) -> bool:
        """删除折扣"""
        return await self.delete(discount_id)

    async def list_discounts(
        self,
        page: int = 1,
        page_size: int = 20,
        customer_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取客户折扣列表"""
        filters = {}

        if customer_id:
            filters["customer_id"] = customer_id
        if brand_id:
            filters["brand_id"] = brand_id
        if is_active is not None:
            filters["is_active"] = is_active

        discounts = await self.find_many(filters, limit=page_size, skip=(page - 1) * page_size, sort={"created_at": -1})
        total = await self.collection.count_documents(filters)
        discounts = await self.format_list(discounts)
        return discounts, total

    async def get_discount_by_customer_and_brand(
        self, customer_id: str, brand_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定客户和品牌的折扣"""
        discount = await self.format(await self.find_one({
            "customer_id": customer_id,
            "brand_id": brand_id
        }))
        return discount

    async def toggle_discount_status(
        self, discount_id: str, is_active: bool
    ) -> bool:
        """切换折扣状态"""
        return await self.update(discount_id, {"is_active": is_active})


customer_discount_service = CustomerDiscountService()
customer_service = CustomerService()
