# Customer 模块 MySQL 迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 customer 模块从 MongoDB 迁移到 MySQL，使用 Tortoise ORM 实现数据模型和服务层，保持 API 接口格式完全兼容。

**Architecture:** 拆分 MongoDB 嵌套文档为 4 张独立 MySQL 表（customers, invoice_infos, shipping_addresses, customer_discounts），使用外键关联。服务层参考 product_service_mysql.py 模式实现。

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL

---

## 1. 数据模型创建

**Files:**
- Create: `backend/models_mysql/customer.py`
- Modify: `backend/models_mysql/__init__.py`

### Task 1.1: 创建 Customer 模型

- [ ] **Step 1: 创建 customer.py 文件并定义 Customer 模型**

```python
"""
客户管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class Customer(Model):
    """客户模型"""
    id = fields.IntField(pk=True, description="客户ID")
    customer_code = fields.CharField(max_length=50, unique=True, description="客户编码")
    name = fields.CharField(max_length=200, description="客户名称")
    customer_type = fields.CharField(max_length=20, description="客户类型: terminal/dealer")
    research_group = fields.CharField(max_length=200, null=True, description="课题组信息")
    contact_person = fields.CharField(max_length=100, null=True, description="联系人")
    contact_phone = fields.CharField(max_length=20, null=True, description="联系电话")
    contact_email = fields.CharField(max_length=100, null=True, description="电子邮箱")
    sales_user_id = fields.IntField(null=True, description="销售人ID")
    sales_user_name = fields.CharField(max_length=100, null=True, description="销售人名称")
    status = fields.CharField(max_length=20, default="normal", description="客户状态: normal/inactive/blacklisted")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "customers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer_code}: {self.name}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "customer_code": self.customer_code,
            "name": self.name,
            "customer_type": self.customer_type,
            "research_group": self.research_group,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "sales_user_id": self.sales_user_id,
            "sales_user_name": self.sales_user_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 添加 InvoiceInfo 模型到 customer.py**

在 Customer 模型后添加：

```python
class InvoiceInfo(Model):
    """开票信息模型"""
    id = fields.IntField(pk=True, description="开票信息ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="invoice_infos", on_delete=fields.CASCADE, description="客户"
    )
    invoice_title = fields.CharField(max_length=200, description="开票抬头")
    invoice_type = fields.CharField(max_length=50, description="开票类型")
    tax_number = fields.CharField(max_length=50, description="税务编码")
    bank_name = fields.CharField(max_length=200, description="银行开户行")
    bank_account = fields.CharField(max_length=50, description="银行账号")
    is_default = fields.BooleanField(default=False, description="是否默认")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "invoice_infos"
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.invoice_title}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "invoice_title": self.invoice_title,
            "invoice_type": self.invoice_type,
            "tax_number": self.tax_number,
            "bank_name": self.bank_name,
            "bank_account": self.bank_account,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 3: 添加 ShippingAddress 模型到 customer.py**

在 InvoiceInfo 模型后添加：

```python
class ShippingAddress(Model):
    """收货地址模型"""
    id = fields.IntField(pk=True, description="收货地址ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="shipping_addresses", on_delete=fields.CASCADE, description="客户"
    )
    recipient_name = fields.CharField(max_length=100, description="收货人")
    recipient_phone = fields.CharField(max_length=20, description="收货电话")
    province = fields.CharField(max_length=100, description="省份")
    province_code = fields.CharField(max_length=20, null=True, description="省份代码")
    city = fields.CharField(max_length=100, description="城市")
    city_code = fields.CharField(max_length=20, null=True, description="城市代码")
    district = fields.CharField(max_length=100, null=True, description="区县")
    address = fields.CharField(max_length=500, description="详细地址")
    is_default = fields.BooleanField(default=False, description="是否默认")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "shipping_addresses"
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.recipient_name} - {self.address}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "recipient_name": self.recipient_name,
            "recipient_phone": self.recipient_phone,
            "province": self.province,
            "province_code": self.province_code,
            "city": self.city,
            "city_code": self.city_code,
            "district": self.district,
            "address": self.address,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 4: 添加 CustomerDiscount 模型到 customer.py**

在 ShippingAddress 模型后添加：

```python
class CustomerDiscount(Model):
    """客户折扣模型"""
    id = fields.IntField(pk=True, description="折扣ID")
    customer: fields.ForeignKeyRelation[Customer] = fields.ForeignKeyField(
        "models.Customer", related_name="discounts", on_delete=fields.CASCADE, description="客户"
    )
    brand_id = fields.IntField(description="品牌ID")
    brand_name = fields.CharField(max_length=100, null=True, description="品牌名称")
    discount_value = fields.FloatField(description="折扣值")
    is_active = fields.BooleanField(default=True, description="是否生效")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "customer_discounts"
        ordering = ["-created_at"]
        unique_together = ("customer", "brand_id")

    def __str__(self):
        return f"Customer {self.customer_id} - Brand {self.brand_id}: {self.discount_value}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "brand_id": self.brand_id,
            "brand_name": self.brand_name,
            "discount_value": self.discount_value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 5: 在 __init__.py 中注册新模型**

修改 `backend/models_mysql/__init__.py`：

```python
"""
MySQL ORM 模型（Tortoise ORM）
"""
from .auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType
from .product import Brand, Category, Product, ProductSpec
from .customer import Customer, InvoiceInfo, ShippingAddress, CustomerDiscount

__all__ = [
    "User",
    "Role",
    "Permission",
    "UserStatus",
    "RoleStatus",
    "PermissionType",
    "Brand",
    "Category",
    "Product",
    "ProductSpec",
    "Customer",
    "InvoiceInfo",
    "ShippingAddress",
    "CustomerDiscount",
]
```

- [ ] **Step 6: 提交模型创建**

```bash
git add backend/models_mysql/customer.py backend/models_mysql/__init__.py
git commit -m "feat(customer): 添加 Customer 模块 Tortoise ORM 模型定义

- 新增 Customer 模型（客户主表）
- 新增 InvoiceInfo 模型（开票信息表）
- 新增 ShippingAddress 模型（收货地址表）
- 新增 CustomerDiscount 模型（客户折扣表）
- 使用外键关联，支持级联删除

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## 2. 服务层实现

**Files:**
- Create: `backend/services/customer_service_mysql.py`

### Task 2.1: 创建服务层文件和 CustomerService 类

- [ ] **Step 1: 创建 customer_service_mysql.py 文件头部和导入**

```python
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
```

- [ ] **Step 2: 添加 CustomerDiscountService 类**

在 CustomerService 类后添加：

```python
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
```

- [ ] **Step 3: 提交服务层创建**

```bash
git add backend/services/customer_service_mysql.py
git commit -m "feat(customer): 添加 Customer 模块 MySQL 服务层实现

- 实现 CustomerService 类（CRUD、列表、统计、状态更新、转移）
- 实现 CustomerDiscountService 类（CRUD、查询、状态切换）
- 支持创建时一并添加开票信息和收货地址
- 支持更新时整体替换开票信息和收货地址

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## 3. 路由层适配

**Files:**
- Modify: `backend/app/routers/customer.py`

### Task 3.1: 修改路由层使用 MySQL 服务

- [ ] **Step 1: 修改导入语句**

将 `backend/app/routers/customer.py` 文件顶部的导入从：

```python
from services.customer_service import customer_service, customer_discount_service
```

改为：

```python
from services.customer_service_mysql import customer_service, customer_discount_service
```

- [ ] **Step 2: 添加 to_int_id 辅助函数**

在文件顶部添加：

```python
def to_int_id(id_str: str) -> int:
    """将字符串 ID 转换为整数 ID"""
    try:
        return int(id_str)
    except (ValueError, TypeError):
        raise ValueError("无效的ID格式")
```

- [ ] **Step 3: 更新所有接口中的 ID 转换**

修改所有使用 `customer_id` 的地方，添加 `to_int_id()` 转换：

- `get_customer`: `customer_id` → `to_int_id(customer_id)`
- `update_customer`: `customer_id` → `to_int_id(customer_id)`
- `delete_customer`: `customer_id` → `to_int_id(customer_id)`
- `update_customer_status`: `customer_id` → `to_int_id(customer_id)`
- `transfer_customer`: `customer_id` → `to_int_id(customer_id)`
- `get_customer_discount`: `discount_id` → `to_int_id(discount_id)`
- `update_customer_discount`: `discount_id` → `to_int_id(discount_id)`
- `delete_customer_discount`: `discount_id` → `to_int_id(discount_id)`
- `toggle_discount_status`: `discount_id` → `to_int_id(discount_id)`
- `get_discount_by_customer_and_brand`: `customer_id` → `to_int_id(customer_id)`, `brand_id` → `to_int_id(brand_id)`

- [ ] **Step 4: 更新 transfer_customer 接口**

修改 `transfer_customer` 函数，因为 MySQL 服务层需要传入 `new_sales_user_name`：

```python
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
    new_user = await mysql_user_service.get_user_by_id(int(new_user_id))
    if not new_user:
        raise ValueError("目标销售不存在")

    success = await customer_service.transfer_customer(
        to_int_id(customer_id),
        int(new_user_id),
        new_user.get("full_name") or new_user.get("username")
    )
    return "客户转移成功"
```

- [ ] **Step 5: 更新 check_customer_owner 函数**

修改 `check_customer_owner` 函数以适配整数 ID：

```python
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
```

- [ ] **Step 6: 提交路由层修改**

```bash
git add backend/app/routers/customer.py
git commit -m "feat(customer): 切换路由层到 MySQL 服务

- 导入 customer_service_mysql 替代 customer_service
- 添加 to_int_id 辅助函数处理 ID 转换
- 更新所有接口使用整数 ID
- 更新 transfer_customer 接口获取目标用户信息

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## 4. API 文档更新

**Files:**
- Modify: `backend/app/routers/api_docs/customer.md`

### Task 4.1: 更新 API 文档中的 ID 类型

- [ ] **Step 1: 更新响应示例中的 id 字段**

将文档中所有响应示例的 `id` 字段从字符串改为整数：

- `"id": "64a1b2c3d4e5f6a7b8c9d0e1"` → `"id": 1`
- `"id": "DIS001"` → `"id": 1`
- `"id": "inv001"` → `"id": 1`
- `"id": "addr001"` → `"id": 1`

- [ ] **Step 2: 更新数据结构说明**

在数据结构部分，将 id 字段的类型从 `string` 改为 `integer`。

- [ ] **Step 3: 提交文档更新**

```bash
git add backend/app/routers/api_docs/customer.md
git commit -m "docs(customer): 更新 API 文档中的 ID 类型为整数

- 响应示例中的 id 字段从字符串改为整数
- 数据结构说明中的 id 类型从 string 改为 integer

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## 5. 测试验证

### Task 5.1: 启动服务并验证

- [ ] **Step 1: 启动后端服务**

```bash
cd backend && venv/Scripts/python -m uvicorn app.main:app --reload
```

- [ ] **Step 2: 验证数据库表创建**

检查 MySQL 数据库中是否创建了以下表：
- customers
- invoice_infos
- shipping_addresses
- customer_discounts

- [ ] **Step 3: 测试客户 CRUD 接口**

使用 Postman 或 curl 测试：
- POST `/api/v1/customers/` - 创建客户
- GET `/api/v1/customers/` - 获取客户列表
- GET `/api/v1/customers/{id}` - 获取客户详情
- PUT `/api/v1/customers/{id}` - 更新客户
- DELETE `/api/v1/customers/{id}` - 删除客户

- [ ] **Step 4: 测试客户折扣接口**

- POST `/api/v1/customer-discounts/` - 创建折扣
- GET `/api/v1/customer-discounts/` - 获取折扣列表
- PUT `/api/v1/customer-discounts/{id}` - 更新折扣
- DELETE `/api/v1/customer-discounts/{id}` - 删除折扣

- [ ] **Step 5: 验证前端功能**

打开前端应用，测试：
- 客户管理页面的列表、创建、编辑、删除功能
- 销售订单创建时的客户选择功能

---

## 文件变更摘要

| 文件 | 操作 | 描述 |
|------|------|------|
| `backend/models_mysql/customer.py` | 新增 | Customer、InvoiceInfo、ShippingAddress、CustomerDiscount 模型 |
| `backend/models_mysql/__init__.py` | 修改 | 注册新模型 |
| `backend/services/customer_service_mysql.py` | 新增 | CustomerService、CustomerDiscountService 服务类 |
| `backend/app/routers/customer.py` | 修改 | 切换到 MySQL 服务层 |
| `backend/app/routers/api_docs/customer.md` | 修改 | 更新 ID 类型为整数 |
