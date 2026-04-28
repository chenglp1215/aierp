from typing import Optional, Dict, Any, List
import uuid

from .base_service import BaseService
from models.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerType,
    CustomerLevel,
    Customer,
    CustomerStatus,
    ShippingAddressCreate,
    ShippingAddressUpdate
)
from validators.customer_validator import (
    CUSTOMER_CREATE_CONFIG,
    CUSTOMER_UPDATE_CONFIG,
    SHIPPING_ADDRESS_CREATE_CONFIG,
    SHIPPING_ADDRESS_UPDATE_CONFIG,
)


class CustomerService(BaseService):
    def __init__(self):
        super().__init__("customers")

    def _generate_customer_code(self) -> str:
        from datetime import datetime
        import random
        import string
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"CUST{date_str}{random_str}"

    def _generate_address_id(self) -> str:
        return f"ADDR{uuid.uuid4().hex[:12].upper()}"

    def validate_customer_create(self, customer_data: CustomerCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(customer_data.model_dump(), CUSTOMER_CREATE_CONFIG)

    def validate_customer_update(self, customer_data: CustomerUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(customer_data.model_dump(exclude_unset=True), CUSTOMER_UPDATE_CONFIG)

    async def create_customer(self, customer_data: CustomerCreate) -> Customer:
        data = customer_data.model_dump()
        data["customer_code"] = self._generate_customer_code()
        data["status"] = CustomerStatus.NORMAL.value

        shipping_addresses = data.get("shipping_addresses", [])
        for addr in shipping_addresses:
            addr["id"] = self._generate_address_id()
            if addr.get("is_default"):
                for other in shipping_addresses:
                    if other != addr:
                        other["is_default"] = False

        return await self.create(data)

    async def update_customer(self, id: str, customer_data: CustomerUpdate) -> bool:
        data = customer_data.model_dump(exclude_unset=True)
        return await self.update(id, data)

    async def get_customer_by_code(self, customer_code: str) -> Optional[Dict[str, Any]]:
        return await self.find_one({"customer_code": customer_code})

    async def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        level: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        filters = {}
        if status:
            filters["status"] = CustomerStatus(status).value
        if level:
            filters["level"] = level
        if keyword:
            filters["$or"] = [
                {"customer_code": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}},
                {"contact_person": {"$regex": keyword, "$options": "i"}},
                {"contact_phone": {"$regex": keyword, "$options": "i"}}
            ]
        return await self.list(page, page_size, filters, "created_at", -1)

    async def get_customer_stats(self) -> Dict[str, Any]:
        total = await self.count({})
        vip_count = await self.count({"level": CustomerLevel.VIP.value})
        potential_count = await self.count({"level": CustomerLevel.POTENTIAL.value})
        return {
            "total": total,
            "vip_count": vip_count,
            "potential_count": potential_count
        }

    async def update_status(self, id: str, status: CustomerStatus) -> bool:
        return await self.update(id, {"status": status.value})

    async def search_customers(self, keyword: str, limit: int = 10) -> list:
        filters = {
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"customer_code": {"$regex": keyword, "$options": "i"}}
            ]
        }
        cursor = self.collection.find(filters).limit(limit)
        items = await cursor.to_list(length=limit)
        for item in items:
            item["id"] = str(item.pop("_id"))
        return items

    def validate_shipping_address_create(self, address_data: ShippingAddressCreate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(address_data.model_dump(), SHIPPING_ADDRESS_CREATE_CONFIG)

    def validate_shipping_address_update(self, address_data: ShippingAddressUpdate) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        return self.validate_data(address_data.model_dump(exclude_unset=True), SHIPPING_ADDRESS_UPDATE_CONFIG)

    async def add_shipping_address(
        self, customer_id: str, address_data: ShippingAddressCreate
    ) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return None

        address = address_data.model_dump()
        address["id"] = self._generate_address_id()

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
        from bson import ObjectId
        customer = await self.collection.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return False

        result = await self.collection.update_one(
            {"_id": customer["_id"]},
            {"$pull": {"shipping_addresses": {"id": address_id}}}
        )

        return result.modified_count > 0

    async def set_default_shipping_address(
        self, customer_id: str, address_id: str
    ) -> bool:
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


customer_service = CustomerService()
