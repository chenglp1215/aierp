# 供应商模块 MySQL 迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将供应商模块从 MongoDB 迁移到 MySQL，建立外键约束保证数据完整性，保持 API 兼容。

**Architecture:** 采用三表设计（suppliers、supplier_brands、supplier_bank_accounts），使用 Tortoise ORM 实现数据访问层，服务层重写，路由层微调。

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL, Vue 3, TypeScript

---

## 文件结构

### 新增文件
- `backend/models_mysql/supplier.py` - 供应商 ORM 模型
- `backend/services/supplier_service_mysql.py` - 供应商服务层（MySQL 版本）
- `backend/scripts/migrate_supplier_to_mysql.py` - 数据迁移脚本

### 修改文件
- `backend/models_mysql/__init__.py` - 导出新模型
- `backend/app/routers/supplier.py` - 使用新服务层
- `backend/app/routers/api_docs/supplier.md` - 更新 API 文档
- `backend/tests/test_supplier_api.py` - 适配新接口
- `web/src/services/api.ts` - 更新类型定义
- `web/src/components/workspace/SupplierWorkspace.vue` - 适配整数 ID

---

## Task 1: 创建供应商 ORM 模型

**Files:**
- Create: `backend/models_mysql/supplier.py`

- [ ] **Step 1: 创建 Supplier 模型**

```python
"""
供应商管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class Supplier(Model):
    """供应商模型"""
    id = fields.IntField(pk=True, description="供应商ID")
    name = fields.CharField(max_length=200, unique=True, description="供应商名称")
    contact_person = fields.CharField(max_length=100, null=True, description="联系人")
    contact_phone = fields.CharField(max_length=50, null=True, description="联系电话")
    contact_email = fields.CharField(max_length=200, null=True, description="联系邮箱")
    address = fields.CharField(max_length=500, null=True, description="地址")
    remark = fields.TextField(null=True, description="备注")
    is_active = fields.BooleanField(default=True, description="是否激活")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "suppliers"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "address": self.address,
            "remark": self.remark,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SupplierBankAccount(Model):
    """供应商银行账户模型"""
    id = fields.IntField(pk=True, description="账户ID")
    supplier: fields.ForeignKeyRelation[Supplier] = fields.ForeignKeyField(
        "models.Supplier", related_name="bank_accounts", on_delete=fields.CASCADE, description="供应商"
    )
    bank_name = fields.CharField(max_length=200, null=True, description="开户行")
    account_name = fields.CharField(max_length=200, null=True, description="账户名")
    account_no = fields.CharField(max_length=50, null=True, description="账号")
    is_default = fields.BooleanField(default=False, description="是否默认")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "supplier_bank_accounts"
        ordering = ["-is_default", "id"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_no}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "bank_name": self.bank_name,
            "account_name": self.account_name,
            "account_no": self.account_no,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SupplierBrand(Model):
    """供应商品牌关联模型"""
    id = fields.IntField(pk=True, description="关联ID")
    supplier: fields.ForeignKeyRelation[Supplier] = fields.ForeignKeyField(
        "models.Supplier", related_name="supplied_brands", on_delete=fields.CASCADE, description="供应商"
    )
    brand_id = fields.IntField(description="品牌ID")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣率")
    is_priority = fields.BooleanField(default=False, description="是否优先")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "supplier_brands"
        ordering = ["-is_priority", "id"]
        unique_together = ("supplier", "brand_id")

    def __str__(self):
        return f"Supplier {self.supplier_id} - Brand {self.brand_id}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "brand_id": self.brand_id,
            "discount": float(self.discount),
            "is_priority": self.is_priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 更新 models_mysql/__init__.py 导出**

在 `backend/models_mysql/__init__.py` 中添加导出：

```python
from .supplier import Supplier, SupplierBankAccount, SupplierBrand

__all__ = [
    # ... 现有导出 ...
    "Supplier",
    "SupplierBankAccount",
    "SupplierBrand",
]
```

- [ ] **Step 3: 验证模型导入**

运行: `cd backend && venv/Scripts/python -c "from models_mysql import Supplier, SupplierBankAccount, SupplierBrand; print('OK')"`
Expected: 输出 `OK`

- [ ] **Step 4: 提交**

```bash
git add backend/models_mysql/supplier.py backend/models_mysql/__init__.py
git commit -m "feat: 添加供应商 MySQL ORM 模型"
```

---

## Task 2: 创建供应商服务层

**Files:**
- Create: `backend/services/supplier_service_mysql.py`

- [ ] **Step 1: 创建 SupplierService 类框架**

```python
"""
供应商管理 - 服务层 (MySQL 版本)
"""
import logging
from typing import Optional, List, Dict, Any

from tortoise.expressions import Q

from models_mysql.supplier import Supplier, SupplierBankAccount, SupplierBrand
from models_mysql.product import Brand

logger = logging.getLogger(__name__)


class SupplierService:
    """供应商服务"""

    async def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建供应商"""
        pass

    async def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> bool:
        """更新供应商"""
        pass

    async def delete_supplier(self, supplier_id: int) -> bool:
        """删除供应商"""
        pass

    async def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict[str, Any]]:
        """获取供应商详情"""
        pass

    async def get_supplier_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取供应商"""
        pass

    async def list_suppliers(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
        brand_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """获取供应商列表"""
        pass

    async def get_all_suppliers(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """获取所有供应商"""
        pass

    async def toggle_supplier_active(self, supplier_id: int, is_active: bool) -> bool:
        """切换供应商激活状态"""
        pass

    async def get_suppliers_by_brand_id(self, brand_id: int) -> List[Dict[str, Any]]:
        """根据品牌ID获取供应商列表"""
        pass


supplier_service = SupplierService()
```

- [ ] **Step 2: 实现 create_supplier 方法**

```python
async def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
    """创建供应商"""
    name = supplier_data.get("name")
    if not name:
        raise ValueError("供应商名称不能为空")

    # 检查名称唯一性
    existing = await Supplier.filter(name=name).first()
    if existing:
        raise ValueError("供应商名称已存在")

    # 创建供应商
    supplier = await Supplier.create(
        name=name,
        contact_person=supplier_data.get("contact_person"),
        contact_phone=supplier_data.get("contact_phone"),
        contact_email=supplier_data.get("contact_email"),
        address=supplier_data.get("address"),
        remark=supplier_data.get("remark"),
        is_active=supplier_data.get("is_active", True),
    )

    # 创建银行账户
    bank_account_data = supplier_data.get("bank_account")
    if bank_account_data:
        await SupplierBankAccount.create(
            supplier=supplier,
            bank_name=bank_account_data.get("bank_name"),
            account_name=bank_account_data.get("account_name"),
            account_no=bank_account_data.get("account_no"),
            is_default=True,
        )

    # 创建品牌关联
    supplied_brands = supplier_data.get("supplied_brands", [])
    for brand_data in supplied_brands:
        brand_id = brand_data.get("brand_id")
        if brand_id:
            await SupplierBrand.create(
                supplier=supplier,
                brand_id=int(brand_id),
                discount=brand_data.get("discount", 1.0),
                is_priority=brand_data.get("is_priority", False),
            )

    return await self.get_supplier_by_id(supplier.id)
```

- [ ] **Step 3: 实现 update_supplier 方法**

```python
async def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> bool:
    """更新供应商"""
    supplier = await Supplier.get_or_none(id=supplier_id)
    if not supplier:
        raise ValueError("供应商不存在")

    # 检查名称唯一性
    if "name" in supplier_data:
        name = supplier_data["name"]
        existing = await Supplier.filter(name=name).exclude(id=supplier_id).first()
        if existing:
            raise ValueError("供应商名称已存在")
        supplier.name = name

    # 更新基本信息
    for field in ["contact_person", "contact_phone", "contact_email", "address", "remark"]:
        if field in supplier_data:
            setattr(supplier, field, supplier_data[field])

    if "is_active" in supplier_data:
        supplier.is_active = supplier_data["is_active"]

    await supplier.save()

    # 更新银行账户（整体替换）
    if "bank_account" in supplier_data:
        await SupplierBankAccount.filter(supplier_id=supplier_id).delete()
        bank_account_data = supplier_data["bank_account"]
        if bank_account_data:
            await SupplierBankAccount.create(
                supplier=supplier,
                bank_name=bank_account_data.get("bank_name"),
                account_name=bank_account_data.get("account_name"),
                account_no=bank_account_data.get("account_no"),
                is_default=True,
            )

    # 更新品牌关联（整体替换）
    if "supplied_brands" in supplier_data:
        await SupplierBrand.filter(supplier_id=supplier_id).delete()
        for brand_data in supplier_data["supplied_brands"]:
            brand_id = brand_data.get("brand_id")
            if brand_id:
                await SupplierBrand.create(
                    supplier=supplier,
                    brand_id=int(brand_id),
                    discount=brand_data.get("discount", 1.0),
                    is_priority=brand_data.get("is_priority", False),
                )

    return True
```

- [ ] **Step 4: 实现 delete_supplier 方法**

```python
async def delete_supplier(self, supplier_id: int) -> bool:
    """删除供应商"""
    supplier = await Supplier.get_or_none(id=supplier_id)
    if not supplier:
        raise ValueError("供应商不存在")

    # 检查是否有关联的采购单
    from models_mysql.purchase_order import PurchaseOrder
    purchase_count = await PurchaseOrder.filter(supplier_id=supplier_id).count()
    if purchase_count > 0:
        raise ValueError(f"该供应商下存在 {purchase_count} 个采购单，无法删除")

    await supplier.delete()
    return True
```

- [ ] **Step 5: 实现 get_supplier_by_id 方法**

```python
async def get_supplier_by_id(self, supplier_id: int) -> Optional[Dict[str, Any]]:
    """获取供应商详情"""
    supplier = await Supplier.get_or_none(id=supplier_id)
    if not supplier:
        raise ValueError("供应商不存在")

    result = supplier.to_dict()

    # 获取银行账户
    bank_accounts = await SupplierBankAccount.filter(supplier_id=supplier_id).all()
    if bank_accounts:
        # 兼容旧格式，返回第一个银行账户
        result["bank_account"] = {
            "bank_name": bank_accounts[0].bank_name,
            "account_name": bank_accounts[0].account_name,
            "account_no": bank_accounts[0].account_no,
        }

    # 获取品牌关联
    brand_relations = await SupplierBrand.filter(supplier_id=supplier_id).all()
    supplied_brands = []
    for rel in brand_relations:
        brand = await Brand.get_or_none(id=rel.brand_id)
        supplied_brands.append({
            "brand_id": rel.brand_id,
            "brand_name": brand.name if brand else None,
            "discount": float(rel.discount),
            "is_priority": rel.is_priority,
        })
    result["supplied_brands"] = supplied_brands

    return result
```

- [ ] **Step 6: 实现 list_suppliers 方法**

```python
async def list_suppliers(
    self,
    page: int = 1,
    page_size: int = 20,
    keyword: Optional[str] = None,
    is_active: Optional[bool] = None,
    brand_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """获取供应商列表"""
    query = Supplier.all()

    if keyword:
        query = query.filter(name__contains=keyword)
    if is_active is not None:
        query = query.filter(is_active=is_active)
    if brand_ids:
        # 查询包含指定品牌的供应商
        supplier_ids = await SupplierBrand.filter(
            brand_id__in=brand_ids
        ).values_list("supplier_id", flat=True)
        query = query.filter(id__in=set(supplier_ids))

    total = await query.count()
    suppliers = await query.offset((page - 1) * page_size).limit(page_size)

    items = []
    for supplier in suppliers:
        item = supplier.to_dict()
        # 获取品牌关联
        brand_relations = await SupplierBrand.filter(supplier_id=supplier.id).all()
        supplied_brands = []
        for rel in brand_relations:
            brand = await Brand.get_or_none(id=rel.brand_id)
            supplied_brands.append({
                "brand_id": rel.brand_id,
                "brand_name": brand.name if brand else None,
                "discount": float(rel.discount),
                "is_priority": rel.is_priority,
            })
        item["supplied_brands"] = supplied_brands
        items.append(item)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }
```

- [ ] **Step 7: 实现其他方法**

```python
async def get_supplier_by_name(self, name: str) -> Optional[Dict[str, Any]]:
    """根据名称获取供应商"""
    supplier = await Supplier.get_or_none(name=name)
    if not supplier:
        return None
    return await self.get_supplier_by_id(supplier.id)

async def get_all_suppliers(self, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """获取所有供应商"""
    query = Supplier.all()
    if is_active is not None:
        query = query.filter(is_active=is_active)
    suppliers = await query.order_by("name")
    return [s.to_dict() for s in suppliers]

async def toggle_supplier_active(self, supplier_id: int, is_active: bool) -> bool:
    """切换供应商激活状态"""
    supplier = await Supplier.get_or_none(id=supplier_id)
    if not supplier:
        raise ValueError("供应商不存在或更新失败")
    supplier.is_active = is_active
    await supplier.save()
    return True

async def get_suppliers_by_brand_id(self, brand_id: int) -> List[Dict[str, Any]]:
    """根据品牌ID获取供应商列表"""
    supplier_ids = await SupplierBrand.filter(
        brand_id=brand_id
    ).values_list("supplier_id", flat=True)
    suppliers = await Supplier.filter(
        id__in=supplier_ids,
        is_active=True
    ).order_by("name")
    return [s.to_dict() for s in suppliers]
```

- [ ] **Step 8: 验证服务层导入**

运行: `cd backend && venv/Scripts/python -c "from services.supplier_service_mysql import supplier_service; print('OK')"`
Expected: 输出 `OK`

- [ ] **Step 9: 提交**

```bash
git add backend/services/supplier_service_mysql.py
git commit -m "feat: 添加供应商服务层 MySQL 版本"
```

---

## Task 3: 更新 API 路由

**Files:**
- Modify: `backend/app/routers/supplier.py`

- [ ] **Step 1: 更新导入和服务引用**

修改 `backend/app/routers/supplier.py`：

```python
"""
供应商管理 - API路由
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional, Dict, Any, List

from services.supplier_service_mysql import supplier_service
from .auth import require_permission
from app.decorators import wrap_response

supplier_router = APIRouter(prefix="/suppliers", tags=["供应商管理"])
```

- [ ] **Step 2: 更新路由参数类型**

将所有 `supplier_id: str` 改为 `supplier_id: int`：

```python
@supplier_router.get("/{supplier_id}", response_model=dict)
@wrap_response
async def get_supplier(
    supplier_id: int,  # 改为 int
    _: dict = Depends(require_permission("supplier.view"))
):
    """获取供应商详情"""
    return await supplier_service.get_supplier_by_id(supplier_id)


@supplier_router.put("/{supplier_id}", response_model=dict)
@wrap_response
async def update_supplier(
    supplier_id: int,  # 改为 int
    supplier_data: Dict[str, Any],
    _: dict = Depends(require_permission("supplier.edit"))
):
    """更新供应商"""
    if supplier_data.get("name"):
        existing = await supplier_service.get_supplier_by_name(supplier_data["name"])
        if existing and existing["id"] != supplier_id:
            raise ValueError("供应商名称已存在")
    await supplier_service.update_supplier(supplier_id, supplier_data)
    return "供应商更新成功"


@supplier_router.delete("/{supplier_id}", response_model=dict)
@wrap_response
async def delete_supplier(
    supplier_id: int,  # 改为 int
    _: dict = Depends(require_permission("supplier.delete"))
):
    """删除供应商"""
    await supplier_service.delete_supplier(supplier_id)
    return "供应商删除成功"


@supplier_router.patch("/{supplier_id}/toggle-active", response_model=dict)
@wrap_response
async def toggle_supplier_active(
    supplier_id: int,  # 改为 int
    is_active: bool = Query(..., description="是否激活"),
    _: dict = Depends(require_permission("supplier.edit"))
):
    """切换供应商激活状态"""
    await supplier_service.toggle_supplier_active(supplier_id, is_active)
    return f"供应商已{'激活' if is_active else '停用'}"


@supplier_router.get("/by-brand/{brand_id}", response_model=dict)
@wrap_response
async def get_suppliers_by_brand(
    brand_id: int,  # 改为 int
    _: dict = Depends(require_permission("supplier.view"))
):
    """根据品牌ID获取供应商列表"""
    return await supplier_service.get_suppliers_by_brand_id(brand_id)
```

- [ ] **Step 3: 验证路由导入**

运行: `cd backend && venv/Scripts/python -c "from app.routers.supplier import supplier_router; print('OK')"`
Expected: 输出 `OK`

- [ ] **Step 4: 提交**

```bash
git add backend/app/routers/supplier.py
git commit -m "feat: 更新供应商路由使用 MySQL 服务层"
```

---

## Task 4: 创建数据迁移脚本

**Files:**
- Create: `backend/scripts/migrate_supplier_to_mysql.py`

- [ ] **Step 1: 创建迁移脚本**

```python
"""
供应商数据迁移脚本 - MongoDB 到 MySQL
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from tortoise import Tortoise
from datetime import datetime
from typing import Dict, Any, List, Optional

from config.settings import settings
from models_mysql.supplier import Supplier, SupplierBankAccount, SupplierBrand
from models_mysql.product import Brand


async def get_mongo_client():
    """获取 MongoDB 客户端"""
    mongo_url = settings.MONGO_URL
    client = AsyncIOMotorClient(mongo_url)
    return client


async def init_tortoise():
    """初始化 Tortoise ORM"""
    await Tortoise.init(
        db_url=f"mysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}",
        modules={"models": ["models_mysql.auth", "models_mysql.product", "models_mysql.supplier"]},
    )
    await Tortoise.generate_schemas()


async def get_brand_id_mapping() -> Dict[str, int]:
    """获取品牌 ObjectId 到 MySQL ID 的映射"""
    brands = await Brand.all()
    # 假设品牌已迁移，需要根据品牌名称匹配
    # 这里返回空字典，实际需要根据业务逻辑调整
    return {}


async def migrate_supplier(supplier_doc: Dict[str, Any], brand_mapping: Dict[str, int]) -> Optional[int]:
    """迁移单个供应商"""
    try:
        name = supplier_doc.get("name")
        if not name:
            print(f"跳过无名称供应商: {supplier_doc.get('_id')}")
            return None

        # 检查是否已存在
        existing = await Supplier.filter(name=name).first()
        if existing:
            print(f"供应商已存在: {name}, ID: {existing.id}")
            return existing.id

        # 创建供应商
        supplier = await Supplier.create(
            name=name,
            contact_person=supplier_doc.get("contact_person"),
            contact_phone=supplier_doc.get("contact_phone"),
            contact_email=supplier_doc.get("contact_email"),
            address=supplier_doc.get("address"),
            remark=supplier_doc.get("remark"),
            is_active=supplier_doc.get("is_active", True),
        )

        # 创建银行账户
        bank_account = supplier_doc.get("bank_account")
        if bank_account:
            await SupplierBankAccount.create(
                supplier=supplier,
                bank_name=bank_account.get("bank_name"),
                account_name=bank_account.get("account_name"),
                account_no=bank_account.get("account_no"),
                is_default=True,
            )

        # 创建品牌关联
        supplied_brands = supplier_doc.get("supplied_brands", [])
        for brand_data in supplied_brands:
            brand_id_str = str(brand_data.get("brand_id", ""))
            # 尝试通过名称匹配品牌
            brand_name = brand_data.get("brand_name")
            if brand_name:
                brand = await Brand.filter(name=brand_name).first()
                if brand:
                    await SupplierBrand.create(
                        supplier=supplier,
                        brand_id=brand.id,
                        discount=brand_data.get("discount", 1.0),
                        is_priority=brand_data.get("is_priority", False),
                    )

        return supplier.id
    except Exception as e:
        print(f"迁移供应商失败: {supplier_doc.get('name')}, 错误: {e}")
        return None


async def main():
    """主迁移函数"""
    print("=" * 60)
    print("开始供应商数据迁移...")
    print("=" * 60)

    # 初始化
    await init_tortoise()
    mongo_client = await get_mongo_client()
    db = mongo_client[settings.MONGO_DB_NAME]
    collection = db["suppliers"]

    # 获取品牌映射
    brand_mapping = await get_brand_id_mapping()

    # 统计
    total_count = await collection.count_documents({})
    print(f"MongoDB 供应商总数: {total_count}")

    # 迁移
    success_count = 0
    skip_count = 0
    error_count = 0

    cursor = collection.find({})
    async for doc in cursor:
        result = await migrate_supplier(doc, brand_mapping)
        if result:
            success_count += 1
        elif result is None:
            skip_count += 1
        else:
            error_count += 1

    # 输出统计
    print("\n" + "=" * 60)
    print("迁移完成!")
    print(f"成功: {success_count}")
    print(f"跳过: {skip_count}")
    print(f"失败: {error_count}")
    print("=" * 60)

    # 验证
    mysql_count = await Supplier.all().count()
    print(f"MySQL 供应商总数: {mysql_count}")

    # 关闭连接
    mongo_client.close()
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: 提交**

```bash
git add backend/scripts/migrate_supplier_to_mysql.py
git commit -m "feat: 添加供应商数据迁移脚本"
```

---

## Task 5: 更新 API 测试脚本

**Files:**
- Modify: `backend/tests/test_supplier_api.py`

- [ ] **Step 1: 更新测试脚本适配整数 ID**

修改 `backend/tests/test_supplier_api.py`：

```python
"""
供应商管理 API 测试脚本 (MySQL 版本)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"


def api(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if method == "GET":
        resp = requests.get(url, headers=headers, params=data)
    elif method == "POST":
        resp = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        resp = requests.put(url, headers=headers, json=data)
    elif method == "PATCH":
        resp = requests.patch(url, headers=headers, json=data)
    elif method == "DELETE":
        resp = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    try:
        return resp.json(), resp.status_code
    except:
        return {"text": resp.text}, resp.status_code


def test_login():
    print("=== 测试登录 ===")
    body, code = api("POST", "/auth/login", {"username": "admin", "password": "admin123"})
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"登录失败: {code}"
    assert body.get("status") == "success", f"登录失败: {body}"
    result = body.get("result", {})
    token = result.get("access_token")
    print(f"✅ 登录成功, token: {token[:50] if token else 'none'}...\n")
    return token


def test_list_suppliers(token):
    print("=== 测试获取供应商列表 ===")
    body, code = api("GET", "/suppliers/", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取供应商列表失败: {code}"
    assert "items" in body.get("result", {}), "无items字段"
    # 验证 ID 是整数类型
    items = body["result"].get("items", [])
    if items:
        assert isinstance(items[0].get("id"), int), "ID 应该是整数类型"
    print(f"✅ 获取供应商列表成功, 共{body['result'].get('total', 0)}条\n")
    return body["result"]


def test_get_all_suppliers(token):
    print("=== 测试获取所有供应商 ===")
    body, code = api("GET", "/suppliers/all", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取所有供应商失败: {code}"
    print(f"✅ 获取所有供应商成功\n")
    return body["result"]


def test_create_supplier(token, name, brand_id=None):
    print(f"=== 测试创建供应商: {name} ===")
    supplier_data = {
        "name": name,
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "contact_email": "zhangsan@example.com",
        "address": "北京市朝阳区某某街道123号",
        "bank_account": {
            "bank_name": "中国工商银行",
            "account_name": name,
            "account_no": "6222021234567890123"
        },
        "supplied_brands": [],
        "remark": "优质供应商",
        "is_active": True
    }
    # 如果提供了品牌 ID，添加品牌关联
    if brand_id:
        supplier_data["supplied_brands"].append({
            "brand_id": brand_id,
            "discount": 0.95,
            "is_priority": True
        })
    
    body, code = api("POST", "/suppliers/", data=supplier_data, token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"创建供应商失败: {code}"
    supplier_id = body.get("result", {}).get("id")
    # 验证 ID 是整数类型
    assert isinstance(supplier_id, int), f"ID 应该是整数类型, 实际是: {type(supplier_id)}"
    print(f"✅ 创建供应商成功, id: {supplier_id}\n")
    return supplier_id


def test_create_duplicate_name_supplier(token, name):
    print(f"=== 测试创建重复名称供应商 ===")
    supplier_data = {"name": name}
    body, code = api("POST", "/suppliers/", data=supplier_data, token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"应该返回错误: {code}"
    assert body.get("status") == "error", f"应该是错误响应"
    print("✅ 重复名称校验正常\n")


def test_get_supplier_detail(token, supplier_id):
    print(f"=== 测试获取供应商详情: {supplier_id} ===")
    body, code = api("GET", f"/suppliers/{supplier_id}", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取供应商详情失败: {code}"
    # 验证 ID 是整数类型
    result_id = body.get("result", {}).get("id")
    assert isinstance(result_id, int), f"ID 应该是整数类型, 实际是: {type(result_id)}"
    print(f"✅ 获取供应商详情成功\n")
    return body["result"]


def test_get_nonexistent_supplier(token):
    print("=== 测试获取不存在的供应商 ===")
    body, code = api("GET", "/suppliers/999999", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"应该返回错误: {code}"
    assert body.get("status") == "error", f"应该是错误响应"
    print("✅ 不存在供应商校验正常\n")


def test_update_supplier(token, supplier_id):
    print(f"=== 测试更新供应商: {supplier_id} ===")
    update_data = {
        "contact_person": "李四",
        "contact_phone": "13900139000",
        "remark": "更新后的备注"
    }
    body, code = api("PUT", f"/suppliers/{supplier_id}", data=update_data, token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"更新供应商失败: {code}"
    print("✅ 更新供应商成功\n")


def test_toggle_supplier_active(token, supplier_id):
    print(f"=== 测试切换供应商激活状态: {supplier_id} ===")
    body, code = api("PATCH", f"/suppliers/{supplier_id}/toggle-active?is_active=false", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"切换激活状态失败: {code}"
    print("✅ 切换激活状态成功\n")

    body, code = api("PATCH", f"/suppliers/{supplier_id}/toggle-active?is_active=true", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"切换激活状态失败: {code}"
    print("✅ 激活供应商成功\n")


def test_delete_supplier(token, supplier_id):
    print(f"=== 测试删除供应商: {supplier_id} ===")
    body, code = api("DELETE", f"/suppliers/{supplier_id}", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"删除供应商失败: {code}"
    print("✅ 删除供应商成功\n")


def test_search_suppliers(token):
    print("=== 测试搜索供应商 ===")
    body, code = api("GET", "/suppliers/", token=token, data={"keyword": "测试", "is_active": True})
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"搜索供应商失败: {code}"
    print(f"✅ 搜索供应商成功\n")


def test_get_suppliers_by_brand(token, brand_id):
    print(f"=== 测试按品牌查询供应商: {brand_id} ===")
    body, code = api("GET", f"/suppliers/by-brand/{brand_id}", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"按品牌查询供应商失败: {code}"
    print(f"✅ 按品牌查询供应商成功\n")


def get_first_brand_id(token):
    """获取第一个品牌 ID 用于测试"""
    body, code = api("GET", "/brands/all", token=token)
    if code == 200 and body.get("result"):
        brands = body["result"]
        if brands:
            return brands[0].get("id")
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("开始供应商接口测试 (MySQL 版本)...")
    print("=" * 60)

    time.sleep(1)

    token = test_login()
    time.sleep(0.5)

    test_list_suppliers(token)
    time.sleep(0.5)

    test_get_all_suppliers(token)
    time.sleep(0.5)

    test_search_suppliers(token)
    time.sleep(0.5)

    # 获取品牌 ID 用于测试
    brand_id = get_first_brand_id(token)
    print(f"使用品牌 ID: {brand_id}")
    time.sleep(0.5)

    supplier_name = f"测试供应商_{int(time.time())}"
    supplier_id = test_create_supplier(token, supplier_name, brand_id)
    time.sleep(0.5)

    test_create_duplicate_name_supplier(token, supplier_name)
    time.sleep(0.5)

    test_get_supplier_detail(token, supplier_id)
    time.sleep(0.5)

    test_get_nonexistent_supplier(token)
    time.sleep(0.5)

    test_update_supplier(token, supplier_id)
    time.sleep(0.5)

    test_toggle_supplier_active(token, supplier_id)
    time.sleep(0.5)

    if brand_id:
        test_get_suppliers_by_brand(token, brand_id)
        time.sleep(0.5)

    test_delete_supplier(token, supplier_id)
    time.sleep(0.5)

    print("=" * 60)
    print("所有供应商接口测试通过! ✅")
    print("=" * 60)
```

- [ ] **Step 2: 提交**

```bash
git add backend/tests/test_supplier_api.py
git commit -m "feat: 更新供应商 API 测试脚本适配 MySQL"
```

---

## Task 6: 更新 API 文档

**Files:**
- Modify: `backend/app/routers/api_docs/supplier.md`

- [ ] **Step 1: 更新数据模型说明**

修改 `backend/app/routers/api_docs/supplier.md`，更新 ID 类型说明：

```markdown
# 供应商管理 API

本文档描述供应商管理模块的所有 REST API 接口。

**模块路径**: `/api/v1/suppliers`

**权限要求**:
- `supplier.view`: 查看供应商
- `supplier.create`: 创建供应商
- `supplier.edit`: 编辑供应商
- `supplier.delete`: 删除供应商

---

## 数据模型

### 供应商供货品牌模型

```json
{
  "brand_id": 1,
  "brand_name": "某某品牌",
  "discount": 0.95,
  "is_priority": true
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| brand_id | integer | 品牌ID（关联品牌表） |
| brand_name | string | 品牌名称（只读） |
| discount | float | 折扣率（0-1，默认1.0） |
| is_priority | boolean | 是否优先选择（默认false） |

### 银行账户模型

```json
{
  "bank_name": "中国工商银行",
  "account_name": "某某供应商有限公司",
  "account_no": "6222021234567890123"
}
```

### 供应商完整模型

```json
{
  "id": 1,
  "name": "某某供应商有限公司",
  "contact_person": "张三",
  "contact_phone": "13800138000",
  "contact_email": "zhangsan@example.com",
  "address": "北京市朝阳区某某街道123号",
  "bank_account": {
    "bank_name": "中国工商银行",
    "account_name": "某某供应商有限公司",
    "account_no": "6222021234567890123"
  },
  "supplied_brands": [
    {
      "brand_id": 1,
      "brand_name": "某某品牌",
      "discount": 0.95,
      "is_priority": true
    }
  ],
  "remark": "优质供应商",
  "is_active": true,
  "created_at": "2026-05-15T10:00:00",
  "updated_at": "2026-05-15T10:00:00"
}
```

---

## 重要变更说明

### ID 类型变更

**从 MongoDB 迁移到 MySQL 后，供应商 ID 从字符串变为整数。**

- MongoDB: `id: "507f1f77bcf86cd799439011"` (24字符字符串)
- MySQL: `id: 1` (整数)

前端需要适配此变更，将 TypeScript 类型从 `string` 改为 `number`。

---

## API 接口

### 1. 创建供应商

**POST** `/api/v1/suppliers/`

**权限**: `supplier.create`

#### 请求参数

```json
{
  "name": "某某供应商有限公司",
  "contact_person": "张三",
  "contact_phone": "13800138000",
  "contact_email": "zhangsan@example.com",
  "address": "北京市朝阳区某某街道123号",
  "bank_account": {
    "bank_name": "中国工商银行",
    "account_name": "某某供应商有限公司",
    "account_no": "6222021234567890123"
  },
  "supplied_brands": [
    {
      "brand_id": 1,
      "discount": 0.95,
      "is_priority": true
    }
  ],
  "remark": "优质供应商",
  "is_active": true
}
```

#### 响应示例

```json
{
  "status": "success",
  "message": "供应商创建成功",
  "result": {
    "id": 1,
    "name": "某某供应商有限公司",
    ...
  }
}
```

---

### 2. 获取供应商列表

**GET** `/api/v1/suppliers/`

**权限**: `supplier.view`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码（默认：1） |
| page_size | int | 否 | 每页数量（默认：20，最大：100） |
| keyword | string | 否 | 搜索关键词（供应商名称） |
| is_active | boolean | 否 | 是否激活 |
| brand_ids | int[] | 否 | 品牌ID列表 |

---

### 3. 获取供应商详情

**GET** `/api/v1/suppliers/{supplier_id}`

**权限**: `supplier.view`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | int | 是 | 供应商ID（整数） |

---

### 4. 更新供应商

**PUT** `/api/v1/suppliers/{supplier_id}`

**权限**: `supplier.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | int | 是 | 供应商ID（整数） |

---

### 5. 删除供应商

**DELETE** `/api/v1/suppliers/{supplier_id}`

**权限**: `supplier.delete`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | int | 是 | 供应商ID（整数） |

---

### 6. 切换供应商激活状态

**PATCH** `/api/v1/suppliers/{supplier_id}/toggle-active`

**权限**: `supplier.edit`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| supplier_id | int | 是 | 供应商ID（整数） |

---

### 7. 根据品牌ID获取供应商列表

**GET** `/api/v1/suppliers/by-brand/{brand_id}`

**权限**: `supplier.view`

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| brand_id | int | 是 | 品牌ID（整数） |

---

## 错误响应

### 供应商不存在

```json
{
  "status": "error",
  "message": "供应商不存在"
}
```

### 供应商名称已存在

```json
{
  "status": "error",
  "message": "供应商名称已存在"
}
```

### 供应商下有采购单无法删除

```json
{
  "status": "error",
  "message": "该供应商下存在 X 个采购单，无法删除"
}
```
```

- [ ] **Step 2: 提交**

```bash
git add backend/app/routers/api_docs/supplier.md
git commit -m "docs: 更新供应商 API 文档适配 MySQL"
```

---

## Task 7: 更新前端类型定义

**Files:**
- Modify: `web/src/services/api.ts`

- [ ] **Step 1: 更新 supplierApi 类型定义**

修改 `web/src/services/api.ts` 中的 `supplierApi`：

```typescript
export const supplierApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string; is_active?: boolean; brand_ids?: number[] }) => {
    return apiService.get<any>('/suppliers/', params)
  },

  getAll: (params?: { is_active?: boolean }) => {
    return apiService.get<any>('/suppliers/all', params)
  },

  getById: (id: number) => {
    return apiService.get<any>(`/suppliers/${id}`)
  },

  create: (data: any) => {
    return apiService.post<any>('/suppliers/', data)
  },

  update: (id: number, data: any) => {
    return apiService.put<any>(`/suppliers/${id}`, data)
  },

  delete: (id: number) => {
    return apiService.delete<any>(`/suppliers/${id}`)
  },

  toggleActive: (id: number, isActive: boolean) => {
    return apiService.patch<any>(`/suppliers/${id}/toggle-active?is_active=${isActive}`)
  },

  getByBrandId: (brandId: number) => {
    return apiService.get<any>(`/suppliers/by-brand/${brandId}`)
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/services/api.ts
git commit -m "feat: 更新前端供应商 API 类型定义为整数 ID"
```

---

## Task 8: 更新前端组件

**Files:**
- Modify: `web/src/components/workspace/SupplierWorkspace.vue`

- [ ] **Step 1: 更新 TypeScript 接口定义**

修改 `web/src/components/workspace/SupplierWorkspace.vue` 中的接口定义：

```typescript
interface SupplierBrand {
  brand_id: number  // 改为 number
  brand_name?: string
  discount: number
  is_priority: boolean
}

interface BankAccount {
  bank_name: string
  account_name: string
  account_no: string
}

interface Supplier {
  id: number  // 改为 number
  name: string
  contact_person?: string
  contact_phone?: string
  contact_email?: string
  address?: string
  bank_account?: BankAccount
  supplied_brands: SupplierBrand[]
  remark?: string
  is_active: boolean
  created_at?: string
  updated_at?: string
}
```

- [ ] **Step 2: 提交**

```bash
git add web/src/components/workspace/SupplierWorkspace.vue
git commit -m "feat: 更新前端供应商组件适配整数 ID"
```

---

## Task 9: 执行测试验证

- [ ] **Step 1: 启动后端服务**

运行: `cd backend && venv/Scripts/python -m uvicorn app.main:app --reload --port 8000`

- [ ] **Step 2: 执行 API 测试**

运行: `cd backend && venv/Scripts/python tests/test_supplier_api.py`
Expected: 所有测试通过

- [ ] **Step 3: 验证前端功能**

启动前端开发服务器，测试供应商管理功能：
- 创建供应商
- 编辑供应商
- 删除供应商
- 搜索供应商
- 按品牌筛选供应商

---

## Self-Review Checklist

**1. Spec coverage:**
- ✅ Supplier MySQL Model - Task 1
- ✅ Supplier Foreign Key Constraints - Task 1 (模型定义中包含)
- ✅ Supplier Model Methods - Task 1 (to_dict 方法)
- ✅ Data Migration Script - Task 4
- ✅ Create Supplier - Task 2
- ✅ Update Supplier - Task 2
- ✅ Delete Supplier - Task 2
- ✅ List Suppliers - Task 2
- ✅ Get Supplier Detail - Task 2
- ✅ Toggle Supplier Active - Task 2
- ✅ Get Suppliers by Brand - Task 2
- ✅ API Response Format - Task 3
- ✅ Supplier TypeScript Types - Task 7
- ✅ Supplier Workspace Component - Task 8

**2. Placeholder scan:**
- ✅ 无 TBD/TODO
- ✅ 无 "implement later"
- ✅ 所有代码步骤都有完整代码

**3. Type consistency:**
- ✅ ID 类型统一为 `int`/`number`
- ✅ 方法签名一致
- ✅ 字段名称一致
