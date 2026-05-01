"""
客户管理 - 服务层
全新设计的客户服务，提供完整的CRUD操作
"""
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from .base_service import BaseService
from models.customer_v2 import (
    Customer,
    CustomerCreate,
    CustomerUpdate,
    CustomerType,
    CustomerStatus,
    InvoiceInfoCreate,
    InvoiceInfoUpdate,
    ShippingAddressCreate,
    ShippingAddressUpdate,
    ContactInfoUpdate,
)
from validators.customer_validator_v2 import (
    CUSTOMER_CREATE_CONFIG,
    CUSTOMER_UPDATE_CONFIG,
    INVOICE_INFO_CREATE_CONFIG,
    INVOICE_INFO_UPDATE_CONFIG,
    SHIPPING_ADDRESS_CREATE_CONFIG,
    SHIPPING_ADDRESS_UPDATE_CONFIG,
    CONTACT_INFO_UPDATE_CONFIG,
)


class CustomerService(BaseService):
    """客户服务类"""

    def __init__(self):
        super().__init__("customers_v2")

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

    def _ensure_single_default(self, items: List[Dict], target_id: str) -> None:
        """确保只有一个默认项"""
        for item in items:
            item["is_default"] = (item.get("id") == target_id)

    # ============ 验证方法 ============

    def validate_customer_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证客户创建数据"""
        return self.validate_data(data, CUSTOMER_CREATE_CONFIG)

    def validate_customer_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证客户更新数据"""
        return self.validate_data(data, CUSTOMER_UPDATE_CONFIG)

    def validate_invoice_info_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证开票信息创建"""
        return self.validate_data(data, INVOICE_INFO_CREATE_CONFIG)

    def validate_invoice_info_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证开票信息更新"""
        return self.validate_data(data, INVOICE_INFO_UPDATE_CONFIG)

    def validate_shipping_address_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证收货地址创建"""
        return self.validate_data(data, SHIPPING_ADDRESS_CREATE_CONFIG)

    def validate_shipping_address_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证收货地址更新"""
        return self.validate_data(data, SHIPPING_ADDRESS_UPDATE_CONFIG)

    def validate_contact_info_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证联系人信息更新"""
        return self.validate_data(data, CONTACT_INFO_UPDATE_CONFIG)

    # ============ 客户CRUD ============

    async def create_customer(self, customer_data: CustomerCreate, current_user: Dict[str, Any]) -> Customer:
        """创建客户"""
        data = customer_data.model_dump()
        data["customer_code"] = self._generate_customer_code()
        data["status"] = CustomerStatus.NORMAL.value

        data["sales_user_id"] = current_user.get("id")
        data["sales_user_name"] = current_user.get("full_name") or current_user.get("username")

        # 处理开票信息
        invoice_infos = data.get("invoice_infos", [])
        for inv in invoice_infos:
            inv["id"] = self._generate_id("INV")
        if invoice_infos and any(inv.get("is_default") for inv in invoice_infos):
            self._ensure_single_default(invoice_infos, invoice_infos[0]["id"])
            invoice_infos[0]["is_default"] = True

        # 处理收货地址
        shipping_addresses = data.get("shipping_addresses", [])
        for addr in shipping_addresses:
            addr["id"] = self._generate_id("ADDR")
        if shipping_addresses and any(addr.get("is_default") for addr in shipping_addresses):
            self._ensure_single_default(shipping_addresses, shipping_addresses[0]["id"])
            shipping_addresses[0]["is_default"] = True

        # 处理联系人信息
        if "contact_info" in data and data["contact_info"]:
            contact_info = data["contact_info"]
        else:
            contact_info = {"contact_person": None, "contact_phone": None, "contact_email": None}
        data["contact_info"] = contact_info

        return await self.create(data)

    async def update_customer(self, customer_id: str, customer_data: CustomerUpdate) -> bool:
        """更新客户"""
        data = customer_data.model_dump(exclude_unset=True)

        if "contact_info" in data and data["contact_info"]:
            data["contact_info"] = data["contact_info"]

        return await self.update(customer_id, data)

    async def get_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取客户"""
        return await super().get_by_id(customer_id)

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
    ) -> Dict[str, Any]:
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
                {"contact_info.contact_phone": {"$regex": keyword, "$options": "i"}},
                {"contact_info.contact_email": {"$regex": keyword, "$options": "i"}},
            ]

        result = await self.list(page, page_size, filters, "created_at", -1)

        for item in result.get("items", []):
            contact_info = item.get("contact_info", {}) or {}
            item["contact_person"] = contact_info.get("contact_person")
            item["contact_phone"] = contact_info.get("contact_phone")
            item.pop("contact_info", None)

            item["invoice_count"] = len(item.get("invoice_infos", []) or [])
            item["shipping_address_count"] = len(item.get("shipping_addresses", []) or [])

            shipping_addresses = item.get("shipping_addresses", []) or []
            default_addr = next((addr for addr in shipping_addresses if addr.get("is_default")), None)
            item["default_shipping_address"] = default_addr

            item.pop("invoice_infos", None)
            item.pop("shipping_addresses", None)

        return result

    async def search_customers(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索客户（用于下拉选择）"""
        filters = {
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"customer_code": {"$regex": keyword, "$options": "i"}},
                {"contact_info.contact_phone": {"$regex": keyword, "$options": "i"}},
            ]
        }
        cursor = self.collection.find(filters).limit(limit)
        items = await cursor.to_list(length=limit)
        for item in items:
            item["id"] = str(item.pop("_id"))
        return items

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
        self, customer_id: str, invoice_data: InvoiceInfoCreate
    ) -> Optional[Dict[str, Any]]:
        """添加开票信息"""
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return None

        invoice = invoice_data.model_dump()
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
        self, customer_id: str, invoice_id: str, invoice_data: InvoiceInfoUpdate
    ) -> bool:
        """更新开票信息"""
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return False

        invoice = invoice_data.model_dump(exclude_unset=True)
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
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return False

        result = await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$pull": {"invoice_infos": {"id": invoice_id}}}
        )

        return result.modified_count > 0

    async def set_default_invoice_info(self, customer_id: str, invoice_id: str) -> bool:
        """设置默认开票信息"""
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
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
        self, customer_id: str, address_data: ShippingAddressCreate
    ) -> Optional[Dict[str, Any]]:
        """添加收货地址"""
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return None

        address = address_data.model_dump()
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
        self, customer_id: str, address_id: str, address_data: ShippingAddressUpdate
    ) -> bool:
        """更新收货地址"""
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return False

        address = address_data.model_dump(exclude_unset=True)
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

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
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
        self, customer_id: str, contact_data: ContactInfoUpdate
    ) -> bool:
        """更新联系人信息"""
        from bson import ObjectId

        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return False

        contact = contact_data.model_dump(exclude_unset=True)
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

    # ============ 销售人管理 ============

    async def get_sales_users(self, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取销售员列表"""
        from services.auth_service import AuthService
        from models.auth import UserStatus

        filters = {"status": UserStatus.ACTIVE.value}
        if keyword:
            filters["$or"] = [
                {"username": {"$regex": keyword, "$options": "i"}},
                {"full_name": {"$regex": keyword, "$options": "i"}},
            ]

        auth_service = AuthService()
        result = await auth_service.list_users(1, 100, keyword=keyword if keyword else None)
        return result.get("items", [])


customer_service = CustomerService()
