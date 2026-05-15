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
        else:
            # 确保返回 bank_account 字段（即使为 None）
            result["bank_account"] = None

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

    async def get_supplier_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取供应商"""
        supplier = await Supplier.get_or_none(name=name)
        if not supplier:
            return None
        return await self.get_supplier_by_id(supplier.id)

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
            # 获取银行账户
            bank_accounts = await SupplierBankAccount.filter(supplier_id=supplier.id).all()
            if bank_accounts:
                item["bank_account"] = {
                    "bank_name": bank_accounts[0].bank_name,
                    "account_name": bank_accounts[0].account_name,
                    "account_no": bank_accounts[0].account_no,
                }
            else:
                item["bank_account"] = None
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


supplier_service = SupplierService()