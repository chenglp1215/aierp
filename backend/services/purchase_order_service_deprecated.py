"""
采购单管理 - 服务层
支持手动创建和从销售单自动生成采购单
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import random
import string
import logging

from bson import ObjectId

from .base_service import BaseService
from models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseStatus,
    InStatus,
    PayStatus,
)
from validators.purchase_order_validator import (
    PURCHASE_ORDER_CREATE_CONFIG,
    PURCHASE_ORDER_UPDATE_CONFIG,
)
from .order_status_flow_service import order_status_flow_service

logger = logging.getLogger(__name__)


class PurchaseOrderService(BaseService):
    """采购单服务类"""

    def __init__(self):
        super().__init__("purchaseOrders")

    async def _get_brand_purchaser_map(self, brand_ids: set) -> Dict[str, str]:
        """批量查询品牌的采购人ID，返回 {brand_id: purchaser_id}"""
        purchaser_map = {}
        valid_ids = []
        for bid in brand_ids:
            try:
                valid_ids.append(ObjectId(bid))
            except Exception:
                pass
        if not valid_ids:
            return purchaser_map
        try:
            brands = await self.db["brands"].find(
                {"_id": {"$in": valid_ids}}
            ).to_list(length=None)
            for b in brands:
                pid = b.get("purchaser_id")
                if pid:
                    purchaser_map[str(b["_id"])] = pid
        except Exception as e:
            logger.error(f"批量查询品牌采购人失败: {e}")
        return purchaser_map

    async def _enrich_items_brand_info(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """富化商品明细的品牌信息：如果品牌ID缺失，从商品规格中查询"""
        if not items:
            return items

        # 收集需要查询的规格ID
        spec_ids = set()
        for item in items:
            spec_id = item.get("spec_id")
            if spec_id and not item.get("brand_id"):
                try:
                    spec_ids.add(ObjectId(spec_id))
                except Exception:
                    pass

        if not spec_ids:
            return items

        # 批量查询商品规格
        spec_map = {}
        try:
            specs = await self.db["product_specs"].find(
                {"_id": {"$in": list(spec_ids)}}
            ).to_list(length=None)
            for spec in specs:
                spec_map[str(spec["_id"])] = spec
        except Exception as e:
            logger.error(f"批量查询商品规格失败: {e}")
            return items

        # 收集需要查询的商品ID
        product_ids = set()
        for spec in spec_map.values():
            pid = spec.get("product_id")
            if pid:
                try:
                    product_ids.add(ObjectId(pid))
                except Exception:
                    pass

        if not product_ids:
            return items

        # 批量查询商品
        product_map = {}
        try:
            products = await self.db["products"].find(
                {"_id": {"$in": list(product_ids)}}
            ).to_list(length=None)
            for p in products:
                product_map[str(p["_id"])] = p
        except Exception as e:
            logger.error(f"批量查询商品失败: {e}")
            return items

        # 收集需要查询的品牌ID
        brand_ids = set()
        for product in product_map.values():
            bid = product.get("brand_id")
            if bid:
                try:
                    brand_ids.add(ObjectId(bid))
                except Exception:
                    pass

        if not brand_ids:
            return items

        # 批量查询品牌
        brand_map = {}
        try:
            brands = await self.db["brands"].find(
                {"_id": {"$in": list(brand_ids)}}
            ).to_list(length=None)
            for b in brands:
                brand_map[str(b["_id"])] = b.get("name", "")
        except Exception as e:
            logger.error(f"批量查询品牌失败: {e}")
            return items

        # 填充品牌信息到商品明细
        for item in items:
            if item.get("brand_id"):
                continue  # 已有品牌信息，跳过

            spec_id = item.get("spec_id")
            if spec_id and spec_id in spec_map:
                spec = spec_map[spec_id]
                product_id = spec.get("product_id", "")
                if product_id and product_id in product_map:
                    product = product_map[product_id]
                    bid = product.get("brand_id", "")
                    if bid and bid in brand_map:
                        item["brand_id"] = bid
                        item["brand_name"] = brand_map[bid]

        return items

    async def _auto_select_supplier(self, brand_id: str) -> Optional[Dict[str, Any]]:
        """根据品牌自动选择供应商：如果有唯一供应商或有优先供应商，则返回该供应商"""
        if not brand_id:
            return None

        try:
            # 查询该品牌的所有供应商
            suppliers = await self.db["suppliers"].find({
                "supplied_brands.brand_id": brand_id,
                "is_active": True
            }).to_list(length=None)

            if not suppliers:
                return None

            # 如果只有一个供应商，直接返回
            if len(suppliers) == 1:
                supplier = suppliers[0]
                return {
                    "id": str(supplier["_id"]),
                    "name": supplier.get("name", "")
                }

            # 如果有多个供应商，查找优先供应商
            priority_suppliers = []
            for supplier in suppliers:
                for sb in supplier.get("supplied_brands", []):
                    if sb.get("brand_id") == brand_id and sb.get("is_priority"):
                        priority_suppliers.append({
                            "id": str(supplier["_id"]),
                            "name": supplier.get("name", "")
                        })
                        break

            # 如果有优先供应商，返回第一个
            if priority_suppliers:
                return priority_suppliers[0]

            # 如果没有优先供应商，返回第一个供应商
            supplier = suppliers[0]
            return {
                "id": str(supplier["_id"]),
                "name": supplier.get("name", "")
            }
        except Exception as e:
            logger.error(f"自动选择供应商失败: {e}")
            return None

    async def _get_supplier_brand_discount(self, supplier_id: str, brand_id: str) -> float:
        """获取供应商对指定品牌的折扣率"""
        if not supplier_id or not brand_id:
            return 1.0

        try:
            supplier = await self.db["suppliers"].find_one(
                {"_id": ObjectId(supplier_id)}
            )
            if supplier:
                for sb in supplier.get("supplied_brands", []):
                    if sb.get("brand_id") == brand_id:
                        return sb.get("discount", 1.0)
        except Exception as e:
            logger.error(f"查询供应商折扣失败: {e}")

        return 1.0

    async def _enrich_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """富化单个采购单：填充品牌名称、商品名称、供应商名称、仓库名称"""
        if not order:
            return order

        # 富化供应商名称
        supplier_id = order.get("supplier_id")
        if supplier_id:
            try:
                supplier = await self.db["suppliers"].find_one(
                    {"_id": ObjectId(supplier_id)}
                )
                if supplier:
                    order["supplier_name"] = supplier.get("name", "")
            except Exception as e:
                logger.error(f"富化供应商名称失败: {e}")

        # 富化品牌名称
        brand_id = order.get("brand_id")
        if brand_id:
            try:
                brand = await self.db["brands"].find_one(
                    {"_id": ObjectId(brand_id)}
                )
                if brand:
                    order["brand_name"] = brand.get("name", "")
            except Exception as e:
                logger.error(f"富化品牌名称失败: {e}")

        # 富化商品明细
        items = order.get("items", [])
        if items:
            spec_ids = set()
            warehouse_ids = set()
            for item in items:
                if item.get("spec_id"):
                    try:
                        spec_ids.add(ObjectId(item["spec_id"]))
                    except Exception:
                        pass
                if item.get("warehouse_id"):
                    try:
                        warehouse_ids.add(ObjectId(item["warehouse_id"]))
                    except Exception:
                        pass

            # 批量查询商品规格
            spec_map = {}
            if spec_ids:
                try:
                    specs = await self.db["product_specs"].find(
                        {"_id": {"$in": list(spec_ids)}}
                    ).to_list(length=None)
                    for spec in specs:
                        spec_map[str(spec["_id"])] = spec
                except Exception as e:
                    logger.error(f"批量查询商品规格失败: {e}")

            # 批量查询商品
            product_ids = set()
            for spec in spec_map.values():
                pid = spec.get("product_id")
                if pid:
                    try:
                        product_ids.add(ObjectId(pid))
                    except Exception:
                        pass

            product_map = {}
            if product_ids:
                try:
                    products = await self.db["products"].find(
                        {"_id": {"$in": list(product_ids)}}
                    ).to_list(length=None)
                    for p in products:
                        product_map[str(p["_id"])] = p
                except Exception as e:
                    logger.error(f"批量查询商品失败: {e}")

            # 批量查询仓库
            warehouse_map = {}
            if warehouse_ids:
                try:
                    warehouses = await self.db["warehouses"].find(
                        {"_id": {"$in": list(warehouse_ids)}}
                    ).to_list(length=None)
                    for w in warehouses:
                        warehouse_map[str(w["_id"])] = w
                except Exception as e:
                    logger.error(f"批量查询仓库失败: {e}")

            # 填充到明细行
            for item in items:
                spec_id = item.get("spec_id")
                if spec_id and spec_id in spec_map:
                    spec = spec_map[spec_id]
                    item["spec_code"] = spec.get("spec_code", item.get("spec_code", ""))
                    product_id = spec.get("product_id", "")
                    if product_id and product_id in product_map:
                        product = product_map[product_id]
                        item["product_name"] = product.get("name", item.get("product_name", ""))
                        item["product_code"] = product.get("product_code", item.get("product_code", ""))

                warehouse_id = item.get("warehouse_id")
                if warehouse_id and warehouse_id in warehouse_map:
                    item["warehouse_name"] = warehouse_map[warehouse_id].get("name", "")

        return order

    async def _enrich_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量富化采购单列表"""
        if not orders:
            return orders

        # 收集所有需要查询的 ID
        supplier_ids = set()
        brand_ids = set()
        spec_ids = set()
        warehouse_ids = set()
        for order in orders:
            sid = order.get("supplier_id")
            if sid:
                supplier_ids.add(sid)
            bid = order.get("brand_id")
            if bid:
                brand_ids.add(bid)
            for item in order.get("items", []):
                spid = item.get("spec_id")
                if spid:
                    spec_ids.add(spid)
                wid = item.get("warehouse_id")
                if wid:
                    warehouse_ids.add(wid)

        # 批量查询供应商
        supplier_map = {}
        if supplier_ids:
            try:
                obj_ids = [ObjectId(sid) for sid in supplier_ids if sid]
                if obj_ids:
                    suppliers = await self.db["suppliers"].find(
                        {"_id": {"$in": obj_ids}}
                    ).to_list(length=None)
                    for s in suppliers:
                        supplier_map[str(s["_id"])] = s.get("name", "")
            except Exception as e:
                logger.error(f"批量查询供应商失败: {e}")

        # 批量查询品牌
        brand_map = {}
        if brand_ids:
            try:
                obj_ids = [ObjectId(bid) for bid in brand_ids if bid]
                if obj_ids:
                    brands = await self.db["brands"].find(
                        {"_id": {"$in": obj_ids}}
                    ).to_list(length=None)
                    for b in brands:
                        brand_map[str(b["_id"])] = b.get("name", "")
            except Exception as e:
                logger.error(f"批量查询品牌失败: {e}")

        # 批量查询商品规格
        spec_map = {}
        if spec_ids:
            try:
                obj_ids = [ObjectId(sid) for sid in spec_ids if sid]
                if obj_ids:
                    specs = await self.db["product_specs"].find(
                        {"_id": {"$in": obj_ids}}
                    ).to_list(length=None)
                    for s in specs:
                        spec_map[str(s["_id"])] = s
            except Exception as e:
                logger.error(f"批量查询商品规格失败: {e}")

        # 从规格中收集 product_id
        product_ids = set()
        for spec in spec_map.values():
            pid = spec.get("product_id")
            if pid:
                product_ids.add(pid)

        product_map = {}
        if product_ids:
            try:
                obj_ids = [ObjectId(pid) for pid in product_ids if pid]
                if obj_ids:
                    products = await self.db["products"].find(
                        {"_id": {"$in": obj_ids}}
                    ).to_list(length=None)
                    for p in products:
                        product_map[str(p["_id"])] = p
            except Exception as e:
                logger.error(f"批量查询商品失败: {e}")

        # 批量查询仓库
        warehouse_map = {}
        if warehouse_ids:
            try:
                obj_ids = [ObjectId(wid) for wid in warehouse_ids if wid]
                if obj_ids:
                    warehouses = await self.db["warehouses"].find(
                        {"_id": {"$in": obj_ids}}
                    ).to_list(length=None)
                    for w in warehouses:
                        warehouse_map[str(w["_id"])] = w.get("name", "")
            except Exception as e:
                logger.error(f"批量查询仓库失败: {e}")

        # 填充到采购单
        for order in orders:
            sid = order.get("supplier_id")
            if sid and sid in supplier_map:
                order["supplier_name"] = supplier_map[sid]

            bid = order.get("brand_id")
            if bid and bid in brand_map:
                order["brand_name"] = brand_map[bid]

            for item in order.get("items", []):
                spid = item.get("spec_id")
                if spid and spid in spec_map:
                    spec = spec_map[spid]
                    item["spec_code"] = spec.get("spec_code", item.get("spec_code", ""))
                    pid = spec.get("product_id", "")
                    if pid and pid in product_map:
                        product = product_map[pid]
                        item["product_name"] = product.get("name", item.get("product_name", ""))
                        item["product_code"] = product.get("product_code", item.get("product_code", ""))

                wid = item.get("warehouse_id")
                if wid and wid in warehouse_map:
                    item["warehouse_name"] = warehouse_map[wid]

        return orders

    def _generate_purchase_no(self) -> str:
        """生成采购单编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"PO{date_str}{random_str}"

    def _calculate_amounts(self, items: list, freight_amt: float = 0.0) -> Dict[str, float]:
        """计算采购单金额"""
        total_amt = sum(item.get("amt", 0) for item in items)
        return {
            "total_amt": round(total_amt, 2),
            "freight_amt": round(freight_amt, 2)
        }

    def _calculate_item_amounts(self, item: dict) -> Dict[str, float]:
        """计算商品明细金额"""
        qty = item.get("purchase_qty", 0)
        price = item.get("purchase_price", 0)
        discount = item.get("discount", 1.0)
        discounted_price = price * discount
        amt = qty * discounted_price
        return {
            "amt": round(amt, 2)
        }

    # ============ 验证方法 ============

    def validate_purchase_order_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证采购单创建数据"""
        return self.validate_data(data, PURCHASE_ORDER_CREATE_CONFIG)

    def validate_purchase_order_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证采购单更新数据"""
        return self.validate_data(data, PURCHASE_ORDER_UPDATE_CONFIG)

    async def create_purchase_order(self, order_data: PurchaseOrderCreate, current_user: dict = None) -> tuple:
        """创建采购单，返回(purchase_no, db_id)"""
        data = order_data.model_dump()

        # 生成采购单号
        data["purchase_no"] = self._generate_purchase_no()

        # 获取品牌ID
        brand_id = data.get("brand_id")

        # 如果没有指定供应商，根据品牌自动选择供应商
        supplier_id = data.get("supplier_id")
        if not supplier_id and brand_id:
            auto_supplier = await self._auto_select_supplier(brand_id)
            if auto_supplier:
                data["supplier_id"] = auto_supplier["id"]
                data["supplier_name"] = auto_supplier["name"]
                supplier_id = auto_supplier["id"]

        # 计算商品明细金额（基于供应商折扣）
        items = data.get("items", [])
        for item in items:
            # 获取商品规格价格
            spec_id = item.get("spec_id")
            spec_price = item.get("purchase_price", 0)
            if spec_id:
                try:
                    spec = await self.db["product_specs"].find_one(
                        {"_id": ObjectId(spec_id)}
                    )
                    if spec:
                        spec_price = spec.get("price", spec_price)
                except Exception as e:
                    logger.error(f"查询商品规格价格失败: {e}")

            # 获取供应商对品牌的折扣率
            item_brand_id = item.get("brand_id") or brand_id
            discount = await self._get_supplier_brand_discount(supplier_id, item_brand_id)

            # 计算采购单价（商品规格价格 * 供应商折扣）
            purchase_price = spec_price * discount

            # 更新商品明细
            item["purchase_price"] = round(purchase_price, 2)
            item["discount"] = discount
            item["brand_id"] = item_brand_id

            # 计算本行金额
            item_amounts = self._calculate_item_amounts(item)
            item.update(item_amounts)

        # 计算订单总金额（物料金额）
        amounts = self._calculate_amounts(items)
        data.update(amounts)

        # 设置默认状态
        data["status"] = {
            "purchase_status": PurchaseStatus.DRAFT.value,
            "in_status": InStatus.NONE.value,
            "pay_status": PayStatus.NONE.value
        }

        # 获取操作人名称
        operator = "system"
        if current_user:
            operator = current_user.get("username", current_user.get("full_name", "system"))

        # 设置创建时间
        data["create_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 设置创建人ID
        if current_user and "id" in current_user:
            data["creator_id"] = current_user["id"]
        else:
            data["creator_id"] = "system"

        # 设置税率默认值
        if "tax_rate" not in data or data["tax_rate"] is None:
            data["tax_rate"] = 0.13

        # 富化供应商名称
        supplier_id = data.get("supplier_id")
        if supplier_id:
            try:
                supplier = await self.db["suppliers"].find_one(
                    {"_id": ObjectId(supplier_id)}
                )
                if supplier:
                    data["supplier_name"] = supplier.get("name", "")
            except Exception as e:
                logger.error(f"保存时查询供应商名称失败: {e}")

        # 富化品牌名称
        brand_id = data.get("brand_id")
        if brand_id:
            try:
                brand = await self.db["brands"].find_one(
                    {"_id": ObjectId(brand_id)}
                )
                if brand:
                    data["brand_name"] = brand.get("name", "")
            except Exception as e:
                logger.error(f"保存时查询品牌名称失败: {e}")

        # 富化商品明细的品牌名称和仓库名称
        for item in items:
            # 富化品牌名称
            item_brand_id = item.get("brand_id")
            if item_brand_id:
                try:
                    brand = await self.db["brands"].find_one(
                        {"_id": ObjectId(item_brand_id)}
                    )
                    if brand:
                        item["brand_name"] = brand.get("name", "")
                except Exception as e:
                    logger.error(f"保存时查询商品品牌名称失败: {e}")

            # 富化仓库名称
            warehouse_id = item.get("warehouse_id")
            if warehouse_id:
                try:
                    warehouse = await self.db["warehouses"].find_one(
                        {"_id": ObjectId(warehouse_id)}
                    )
                    if warehouse:
                        item["warehouse_name"] = warehouse.get("name", "")
                except Exception as e:
                    logger.error(f"保存时查询仓库名称失败: {e}")

        # 设置累计统计字段默认值
        data["total_in_qty"] = 0
        data["total_paid_amt"] = 0.0
        data["total_return_qty"] = 0
        data["total_return_amt"] = 0.0

        # 设置商品明细的默认值
        for item in items:
            item["in_qty"] = 0
            item["return_qty"] = 0

        # 保存到数据库
        data["id"] = await self.create(data)
        if "_id" in data:
            data.pop("_id")

        # 创建初始流转记录
        await order_status_flow_service.create_flow_record(
            order_no=data["purchase_no"],
            field="purchase_status",
            old_value=None,
            new_value=PurchaseStatus.DRAFT.value,
            operator=operator,
            remark="采购单创建"
        )

        return data["purchase_no"], data["id"]

    async def update_purchase_order(self, purchase_no: str, order_data: PurchaseOrderUpdate, current_user: dict = None) -> bool:
        """更新采购单"""
        data = order_data.model_dump(exclude_unset=True)

        # 获取当前采购单数据以获取freight_amt
        current_order = await self.find_one({"purchase_no": purchase_no})
        current_freight_amt = current_order.get("freight_amt", 0.0) if current_order else 0.0

        # 如果更新了商品明细或运费，重新计算金额
        if "items" in data or "freight_amt" in data:
            items = data.get("items", current_order.get("items", []) if current_order else [])
            freight_amt = data.get("freight_amt", current_freight_amt)

            for item in items:
                item_amounts = self._calculate_item_amounts(item)
                item.update(item_amounts)

            amounts = self._calculate_amounts(items, freight_amt)
            data.update(amounts)

        return await self.update_by_purchase_no(purchase_no, data)

    async def update_by_purchase_no(self, purchase_no: str, data: Dict[str, Any]) -> bool:
        """根据采购单号更新采购单"""
        result = await self.collection.update_one(
            {"purchase_no": purchase_no},
            {"$set": {**data, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    async def get_purchase_order_by_no(self, purchase_no: str) -> Optional[Dict[str, Any]]:
        """根据采购单号获取采购单"""
        order = await self.find_one({"purchase_no": purchase_no})
        if order:
            order = await self._enrich_order(order)
        return order

    async def list_purchase_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        purchase_type: Optional[str] = None,
        brand_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        purchase_no: Optional[str] = None,
        source_sale_order_no: Optional[str] = None,
    ) -> Dict[str, Any]:
        """分页查询采购单列表"""
        filters = {}

        if status:
            filters["status.purchase_status"] = status
        if purchase_type:
            filters["purchase_type"] = purchase_type
        if brand_id:
            filters["brand_id"] = brand_id
        if supplier_id:
            filters["supplier_id"] = supplier_id
        if purchase_no:
            filters["purchase_no"] = purchase_no
        if source_sale_order_no:
            filters["source_sale_order_no"] = source_sale_order_no

        result = await self.list(page, page_size, filters, "create_time", -1)

        # 富化列表数据
        if result.get("items"):
            result["items"] = await self._enrich_orders(result["items"])

        return result

    async def search_purchase_orders(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """快速搜索采购单（用于下拉选择）"""
        filters = {
            "$or": [
                {"purchase_no": {"$regex": keyword, "$options": "i"}},
                {"supplier_name": {"$regex": keyword, "$options": "i"}},
                {"brand_name": {"$regex": keyword, "$options": "i"}}
            ]
        }
        result = await self.list(1, limit, filters, "create_time", -1)
        return result.get("items", [])

    async def update_purchase_status_by_no(self, purchase_no: str, status: PurchaseStatus, operator: str = "system") -> bool:
        """根据采购单号更新采购主状态"""
        order = await self.find_one({"purchase_no": purchase_no})
        if not order:
            return False

        old_status = order.get("status", {}).get("purchase_status", "")
        new_status = status.value

        if old_status == new_status:
            return True

        result = await self.collection.update_one(
            {"purchase_no": purchase_no},
            {"$set": {"status.purchase_status": new_status, "updated_at": datetime.now()}}
        )

        if result.modified_count > 0:
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no,
                field="purchase_status",
                old_value=old_status,
                new_value=new_status,
                operator=operator
            )
            return True
        return False

    async def update_in_status_by_no(self, purchase_no: str, in_status: InStatus, operator: str = "system") -> bool:
        """根据采购单号更新入库状态"""
        order = await self.find_one({"purchase_no": purchase_no})
        if not order:
            return False

        old_value = order.get("status", {}).get("in_status", "")
        new_value = in_status.value
        if old_value == new_value:
            return True

        update_data = {"status.in_status": new_value}
        result = await self.update_by_purchase_no(purchase_no, update_data)
        if result:
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no, field="in_status",
                old_value=old_value, new_value=new_value, operator=operator
            )
        return result

    async def update_pay_status_by_no(self, purchase_no: str, pay_status: PayStatus, operator: str = "system") -> bool:
        """根据采购单号更新付款状态"""
        order = await self.find_one({"purchase_no": purchase_no})
        if not order:
            return False

        old_value = order.get("status", {}).get("pay_status", "")
        new_value = pay_status.value
        if old_value == new_value:
            return True

        update_data = {"status.pay_status": new_value}
        result = await self.update_by_purchase_no(purchase_no, update_data)
        if result:
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no, field="pay_status",
                old_value=old_value, new_value=new_value, operator=operator
            )
        return result

    async def delete_purchase_order_by_no(self, purchase_no: str) -> bool:
        """根据采购单号删除采购单"""
        result = await self.collection.delete_one({"purchase_no": purchase_no})
        return result.deleted_count > 0

    async def _update_sales_order_after_recall(self, purchase_order: Dict[str, Any], operator: str = "system") -> bool:
        """撤回采购单后更新销售单状态和商品下推状态"""
        source_sale_order_no = purchase_order.get("source_sale_order_no")
        if not source_sale_order_no:
            logger.info(f"采购单 {purchase_order.get('purchase_no')} 没有关联销售单，跳过更新")
            return True

        try:
            # 获取销售单（使用销售订单服务的集合名称）
            sales_order = await self.db["sales_orders"].find_one(
                {"order_no": source_sale_order_no}
            )
            if not sales_order:
                logger.info(f"销售单 {source_sale_order_no} 不存在，跳过更新")
                return True

            # 获取采购单中的商品明细行号
            purchase_items = purchase_order.get("items", [])
            source_row_nos = set()
            for item in purchase_items:
                row_no = item.get("source_sale_row_no")
                if row_no:
                    # 确保 row_no 是整数类型（数据库中可能存储为字符串）
                    try:
                        row_no_int = int(row_no)
                        source_row_nos.add(row_no_int)
                    except (ValueError, TypeError):
                        logger.warning(f"采购单商品 source_sale_row_no {row_no} 无法转换为整数，跳过")

            logger.info(f"采购单 {purchase_order.get('purchase_no')} 关联的销售单行号: {source_row_nos}")
            logger.info(f"采购单商品明细: {[(item.get('row_no'), item.get('source_sale_row_no')) for item in purchase_items]}")

            # 更新销售单商品的下推状态
            sales_items = sales_order.get("items", [])
            logger.info(f"销售单商品明细: {[(item.get('row_no'), item.get('pushed')) for item in sales_items]}")

            updated_items = []
            updated_count = 0
            for item in sales_items:
                row_no = item.get("row_no")
                # 确保 row_no 是整数类型（数据库中可能存储为字符串）
                row_no_int = None
                if row_no is not None:
                    try:
                        row_no_int = int(row_no)
                    except (ValueError, TypeError):
                        logger.warning(f"销售单商品行号 {row_no} 无法转换为整数，跳过更新")
                        updated_items.append(item)
                        continue
                if row_no_int and row_no_int in source_row_nos:
                    logger.info(f"更新销售单商品行号 {row_no_int}: pushed True -> False")
                    item["pushed"] = False
                    updated_count += 1
                updated_items.append(item)

            logger.info(f"更新了 {updated_count} 个销售单商品的下推状态")

            # 计算销售单的下推状态
            pushed_count = sum(1 for item in updated_items if item.get("pushed"))
            total_count = len(updated_items)

            # 更新销售单状态
            if pushed_count == 0:
                new_order_status = "audited"  # 全部未下推，回到已审核
            elif pushed_count < total_count:
                new_order_status = "partially_pushed_to_purchase"  # 部分下推
            else:
                new_order_status = "pushed_to_purchase"  # 全部下推

            logger.info(f"销售单 {source_sale_order_no} 新状态: {new_order_status} (pushed: {pushed_count}/{total_count})")

            # 更新销售单（使用销售订单服务的集合名称）
            result = await self.db["sales_orders"].update_one(
                {"order_no": source_sale_order_no},
                {"$set": {
                    "items": updated_items,
                    "status.order_status": new_order_status,
                    "updated_at": datetime.now()
                }}
            )

            logger.info(f"更新销售单结果: matched={result.matched_count}, modified={result.modified_count}")

            # 创建流转记录
            await order_status_flow_service.create_flow_record(
                order_no=source_sale_order_no,
                field="order_status",
                old_value=sales_order.get("status", {}).get("order_status", ""),
                new_value=new_order_status,
                operator=operator,
                remark=f"采购单 {purchase_order.get('purchase_no')} 撤回"
            )

            return True
        except Exception as e:
            logger.error(f"更新销售单状态失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def recall_purchase_order(self, purchase_no: str, operator: str = "system") -> bool:
        """撤回采购单（删除采购单，更新销售单状态）"""
        # 获取采购单
        purchase_order = await self.find_one({"purchase_no": purchase_no})
        if not purchase_order:
            logger.error(f"采购单 {purchase_no} 不存在")
            return False

        logger.info(f"开始撤回采购单 {purchase_no}, 状态: {purchase_order.get('status', {})}")
        logger.info(f"采购单来源销售单: {purchase_order.get('source_sale_order_no')}")

        # 检查状态，只有草稿或已审核状态可以撤回
        current_status = purchase_order.get("status", {}).get("purchase_status", "")
        if current_status not in [PurchaseStatus.DRAFT.value, PurchaseStatus.AUDITED.value]:
            logger.error(f"采购单 {purchase_no} 状态 {current_status} 不允许撤回")
            return False

        # 更新销售单状态
        update_success = await self._update_sales_order_after_recall(purchase_order, operator)
        if not update_success:
            logger.error(f"采购单 {purchase_no} 撤回失败：更新销售单状态失败")
            return False

        # 删除采购单
        result = await self.collection.delete_one({"purchase_no": purchase_no})

        if result.deleted_count > 0:
            # 创建流转记录
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no,
                field="purchase_status",
                old_value=current_status,
                new_value=PurchaseStatus.CANCELLED.value,
                operator=operator,
                remark="采购单撤回（删除）"
            )
            return True
        return False

    async def approve_purchase_order(self, purchase_no: str, operator: str = "system") -> bool:
        """审核通过采购单（草稿 -> 已审核）"""
        order = await self.find_one({"purchase_no": purchase_no})
        if not order:
            return False

        current_status = order.get("status", {}).get("purchase_status", "")
        if current_status != PurchaseStatus.DRAFT.value:
            return False

        result = await self.collection.update_one(
            {"purchase_no": purchase_no},
            {"$set": {"status.purchase_status": PurchaseStatus.AUDITED.value, "updated_at": datetime.now()}}
        )

        if result.modified_count > 0:
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no,
                field="purchase_status",
                old_value=current_status,
                new_value=PurchaseStatus.AUDITED.value,
                operator=operator,
                remark="采购单审核通过"
            )
            return True
        return False

    async def close_purchase_order(self, purchase_no: str, operator: str = "system") -> bool:
        """结案采购单（已审核 -> 已结案）"""
        order = await self.find_one({"purchase_no": purchase_no})
        if not order:
            return False

        current_status = order.get("status", {}).get("purchase_status", "")
        if current_status != PurchaseStatus.AUDITED.value:
            return False

        result = await self.collection.update_one(
            {"purchase_no": purchase_no},
            {"$set": {"status.purchase_status": PurchaseStatus.CLOSED.value, "updated_at": datetime.now()}}
        )

        if result.modified_count > 0:
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no,
                field="purchase_status",
                old_value=current_status,
                new_value=PurchaseStatus.CLOSED.value,
                operator=operator,
                remark="采购单结案"
            )
            return True
        return False

    async def reaudit_purchase_order(self, purchase_no: str, operator: str = "system") -> bool:
        """重审采购单（已审核 -> 草稿）"""
        order = await self.find_one({"purchase_no": purchase_no})
        if not order:
            return False

        current_status = order.get("status", {}).get("purchase_status", "")
        if current_status != PurchaseStatus.AUDITED.value:
            return False

        result = await self.collection.update_one(
            {"purchase_no": purchase_no},
            {"$set": {"status.purchase_status": PurchaseStatus.DRAFT.value, "updated_at": datetime.now()}}
        )

        if result.modified_count > 0:
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no,
                field="purchase_status",
                old_value=current_status,
                new_value=PurchaseStatus.DRAFT.value,
                operator=operator,
                remark="采购单重审（撤回到草稿）"
            )
            return True
        return False

    async def void_purchase_order(self, purchase_no: str, operator: str = "system") -> bool:
        """作废采购单（已审核 -> 已作废）"""
        order = await self.find_one({"purchase_no": purchase_no})
        if not order:
            return False

        current_status = order.get("status", {}).get("purchase_status", "")
        if current_status != PurchaseStatus.AUDITED.value:
            return False

        result = await self.collection.update_one(
            {"purchase_no": purchase_no},
            {"$set": {"status.purchase_status": PurchaseStatus.CANCELLED.value, "updated_at": datetime.now()}}
        )

        if result.modified_count > 0:
            await order_status_flow_service.create_flow_record(
                order_no=purchase_no,
                field="purchase_status",
                old_value=current_status,
                new_value=PurchaseStatus.CANCELLED.value,
                operator=operator,
                remark="采购单作废"
            )
            return True
        return False

    async def generate_from_sales_order(self, sales_order: Dict[str, Any], current_user: dict = None) -> List[Dict[str, Any]]:
        """
        从销售单自动生成采购单
        规则：
        1. 按 shipping_method 拆分直运商品和仓发物流商品
        2. 直运商品：按 brand_id 分组，每品牌生成一张直运采购单
        3. 仓发商品：校验库存，只保留库存不足商品，按 brand_id 分组生成仓库采购单
        """
        generated_orders = []
        items = sales_order.get("items", [])
        order_no = sales_order.get("order_no", "")
        order_id = sales_order.get("id", "")

        # 富化商品明细的品牌信息（如果缺失）
        enriched_items = await self._enrich_items_brand_info(items)

        # 按发货方式拆分
        direct_items = []  # 直运商品
        warehouse_items = []  # 仓发物流商品

        for item in enriched_items:
            shipping_method = item.get("shipping_method", "")
            if shipping_method == "直运":
                direct_items.append(item)
            else:
                warehouse_items.append(item)

        # 批量查询品牌的采购人
        all_brand_ids = set()
        for item in enriched_items:
            bid = item.get("brand_id")
            if bid:
                all_brand_ids.add(bid)
        brand_purchaser_map = await self._get_brand_purchaser_map(all_brand_ids)

        # 处理直运商品：按 brand_id 分组
        direct_by_brand = {}
        for item in direct_items:
            brand_id = item.get("brand_id")
            if not brand_id:
                logger.warning(f"商品 {item.get('spec_id')} 缺少品牌ID，跳过采购单生成")
                continue
            if brand_id not in direct_by_brand:
                direct_by_brand[brand_id] = []
            direct_by_brand[brand_id].append(item)

        for brand_id, brand_items in direct_by_brand.items():
            purchase_items = []
            for idx, item in enumerate(brand_items, 1):
                purchase_items.append({
                    "row_no": idx,
                    "product_id": item.get("product_id", ""),
                    "spec_id": item.get("spec_id"),
                    "brand_id": item.get("brand_id"),
                    "brand_name": item.get("brand_name"),
                    "purchase_qty": item.get("qty", 0),
                    "in_qty": 0,
                    "return_qty": 0,
                    "purchase_price": item.get("price", 0),
                    "discount": item.get("discount", 1.0),
                    "amt": item.get("amt", 0),
                    "shipping_method": "直运",
                    "source_sale_row_no": int(item.get("row_no")) if item.get("row_no") is not None else None,
                    "warehouse_id": item.get("warehouse_id")
                })

            # 创建直运采购单，优先使用品牌的采购人，回退到销售员
            # supplier_id 设为 None，让系统自动选择供应商
            purchase_user_id = brand_purchaser_map.get(brand_id) or ""
            create_data = PurchaseOrderCreate(
                purchase_type="direct",
                source_sale_order_no=order_no,
                source_sale_order_id=order_id,
                brand_id=brand_id,
                supplier_id=None,  # 设为 None，让系统自动选择供应商
                purchase_user_id=purchase_user_id,
                receive_info={
                    "type": "customer",
                    "customer_addr": sales_order.get("deliver_info", {}).get("addr"),
                    "province": sales_order.get("deliver_info", {}).get("province"),
                    "city": sales_order.get("deliver_info", {}).get("city"),
                    "contact_person": sales_order.get("deliver_info", {}).get("person_name"),
                    "contact_tel": sales_order.get("deliver_info", {}).get("person_tel")
                },
                expect_arrive_date=sales_order.get("expect_deliver_date"),
                settle_type=sales_order.get("settle_type", "月结"),
                remark=f"由销售单{order_no}自动生成-直运采购",
                items=purchase_items
            )

            purchase_no, db_id = await self.create_purchase_order(create_data, current_user)
            generated_orders.append({"purchase_no": purchase_no, "id": db_id, "purchase_type": "direct"})

        # 处理仓发商品：按 brand_id 分组
        warehouse_by_brand = {}
        for item in warehouse_items:
            brand_id = item.get("brand_id")
            if not brand_id:
                logger.warning(f"商品 {item.get('spec_id')} 缺少品牌ID，跳过采购单生成")
                continue
            if brand_id not in warehouse_by_brand:
                warehouse_by_brand[brand_id] = []
            warehouse_by_brand[brand_id].append(item)

        for brand_id, brand_items in warehouse_by_brand.items():
            purchase_items = []
            for idx, item in enumerate(brand_items, 1):
                purchase_items.append({
                    "row_no": idx,
                    "product_id": item.get("product_id", ""),
                    "spec_id": item.get("spec_id"),
                    "brand_id": item.get("brand_id"),
                    "brand_name": item.get("brand_name"),
                    "purchase_qty": item.get("qty", 0),
                    "in_qty": 0,
                    "return_qty": 0,
                    "purchase_price": item.get("price", 0),
                    "discount": item.get("discount", 1.0),
                    "amt": item.get("amt", 0),
                    "shipping_method": item.get("shipping_method"),
                    "source_sale_row_no": int(item.get("row_no")) if item.get("row_no") is not None else None,
                    "warehouse_id": item.get("warehouse_id")
                })

            # 创建仓库采购单，优先使用品牌的采购人，回退到销售员
            # supplier_id 设为 None，让系统自动选择供应商
            purchase_user_id = brand_purchaser_map.get(brand_id) or ""
            create_data = PurchaseOrderCreate(
                purchase_type="warehouse",
                source_sale_order_no=order_no,
                source_sale_order_id=order_id,
                brand_id=brand_id,
                supplier_id=None,  # 设为 None，让系统自动选择供应商
                purchase_user_id=purchase_user_id,
                receive_info={
                    "type": "warehouse",
                    "warehouse_id": brand_items[0].get("warehouse_id")
                },
                expect_arrive_date=sales_order.get("expect_deliver_date"),
                settle_type=sales_order.get("settle_type", "月结"),
                remark=f"由销售单{order_no}自动生成-仓库采购",
                items=purchase_items
            )

            purchase_no, db_id = await self.create_purchase_order(create_data, current_user)
            generated_orders.append({"purchase_no": purchase_no, "id": db_id, "purchase_type": "warehouse"})

        return generated_orders

    async def generate_from_selected_items(self, sales_order: Dict[str, Any], selected_items: List[Dict[str, Any]], current_user: dict = None) -> List[Dict[str, Any]]:
        """
        从销售单中选中的商品生成采购单
        selected_items: 选中的商品列表（已从订单中筛选）
        按 shipping_method 拆分后按 brand_id 分组，每组一张采购单
        """
        generated_orders = []
        order_no = sales_order.get("order_no", "")
        order_id = sales_order.get("id", "")

        # 富化商品明细的品牌信息（如果缺失）
        enriched_items = await self._enrich_items_brand_info(selected_items)

        direct_items = [item for item in enriched_items if item.get("shipping_method") == "直运"]
        warehouse_items = [item for item in enriched_items if item.get("shipping_method") != "直运"]

        # 批量查询品牌的采购人
        all_brand_ids = set()
        for item in enriched_items:
            bid = item.get("brand_id")
            if bid:
                all_brand_ids.add(bid)
        brand_purchaser_map = await self._get_brand_purchaser_map(all_brand_ids)

        # 直运商品按 brand_id 分组
        direct_by_brand = {}
        for item in direct_items:
            brand_id = item.get("brand_id")
            if not brand_id:
                logger.warning(f"商品 {item.get('spec_id')} 缺少品牌ID，跳过采购单生成")
                continue
            if brand_id not in direct_by_brand:
                direct_by_brand[brand_id] = []
            direct_by_brand[brand_id].append(item)

        for brand_id, brand_items in direct_by_brand.items():
            purchase_items = []
            for idx, item in enumerate(brand_items, 1):
                purchase_items.append({
                    "row_no": idx,
                    "product_id": item.get("product_id", ""),
                    "spec_id": item.get("spec_id"),
                    "brand_id": item.get("brand_id"),
                    "brand_name": item.get("brand_name"),
                    "purchase_qty": item.get("qty", 0),
                    "in_qty": 0,
                    "return_qty": 0,
                    "purchase_price": item.get("price", 0),
                    "discount": item.get("discount", 1.0),
                    "amt": item.get("amt", 0),
                    "shipping_method": "直运",
                    "source_sale_row_no": int(item.get("row_no")) if item.get("row_no") is not None else None,
                    "warehouse_id": item.get("warehouse_id")
                })

            # 优先使用品牌的采购人，回退到销售员
            # supplier_id 设为 None，让系统自动选择供应商
            purchase_user_id = brand_purchaser_map.get(brand_id) or ""
            create_data = PurchaseOrderCreate(
                purchase_type="direct",
                source_sale_order_no=order_no,
                source_sale_order_id=order_id,
                brand_id=brand_id,
                supplier_id=None,  # 设为 None，让系统自动选择供应商
                purchase_user_id=purchase_user_id,
                receive_info={
                    "type": "customer",
                    "customer_addr": sales_order.get("deliver_info", {}).get("addr"),
                    "province": sales_order.get("deliver_info", {}).get("province"),
                    "city": sales_order.get("deliver_info", {}).get("city"),
                    "contact_person": sales_order.get("deliver_info", {}).get("person_name"),
                    "contact_tel": sales_order.get("deliver_info", {}).get("person_tel")
                },
                expect_arrive_date=sales_order.get("expect_deliver_date"),
                settle_type=sales_order.get("settle_type", "月结"),
                remark=f"由销售单{order_no}自动生成-直运采购",
                items=purchase_items
            )

            purchase_no, db_id = await self.create_purchase_order(create_data, current_user)
            generated_orders.append({"purchase_no": purchase_no, "id": db_id, "purchase_type": "direct"})

        # 仓发商品按 brand_id 分组
        warehouse_by_brand = {}
        for item in warehouse_items:
            brand_id = item.get("brand_id")
            if not brand_id:
                logger.warning(f"商品 {item.get('spec_id')} 缺少品牌ID，跳过采购单生成")
                continue
            if brand_id not in warehouse_by_brand:
                warehouse_by_brand[brand_id] = []
            warehouse_by_brand[brand_id].append(item)

        for brand_id, brand_items in warehouse_by_brand.items():
            purchase_items = []
            for idx, item in enumerate(brand_items, 1):
                purchase_items.append({
                    "row_no": idx,
                    "product_id": item.get("product_id", ""),
                    "spec_id": item.get("spec_id"),
                    "brand_id": item.get("brand_id"),
                    "brand_name": item.get("brand_name"),
                    "purchase_qty": item.get("qty", 0),
                    "in_qty": 0,
                    "return_qty": 0,
                    "purchase_price": item.get("price", 0),
                    "discount": item.get("discount", 1.0),
                    "amt": item.get("amt", 0),
                    "shipping_method": item.get("shipping_method"),
                    "source_sale_row_no": int(item.get("row_no")) if item.get("row_no") is not None else None,
                    "warehouse_id": item.get("warehouse_id")
                })

            # 优先使用品牌的采购人，回退到销售员
            # supplier_id 设为 None，让系统自动选择供应商
            purchase_user_id = brand_purchaser_map.get(brand_id) or ""
            create_data = PurchaseOrderCreate(
                purchase_type="warehouse",
                source_sale_order_no=order_no,
                source_sale_order_id=order_id,
                brand_id=brand_id,
                supplier_id=None,  # 设为 None，让系统自动选择供应商
                purchase_user_id=purchase_user_id,
                receive_info={
                    "type": "warehouse",
                    "warehouse_id": brand_items[0].get("warehouse_id")
                },
                expect_arrive_date=sales_order.get("expect_deliver_date"),
                settle_type=sales_order.get("settle_type", "月结"),
                remark=f"由销售单{order_no}自动生成-仓库采购",
                items=purchase_items
            )

            purchase_no, db_id = await self.create_purchase_order(create_data, current_user)
            generated_orders.append({"purchase_no": purchase_no, "id": db_id, "purchase_type": "warehouse"})

        return generated_orders

    async def preview_from_sales_order(self, sales_order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        预览从销售单生成的采购单（不实际创建）
        复用 generate_from_sales_order 的拆分分组逻辑，返回 PurchaseOrderCreate 结构数据
        """
        items = sales_order.get("items", [])
        order_no = sales_order.get("order_no", "")
        order_id = sales_order.get("id", "")

        # 富化商品明细的品牌信息（如果缺失）
        enriched_items = await self._enrich_items_brand_info(items)

        # 按发货方式拆分
        direct_items = []
        warehouse_items = []
        for item in enriched_items:
            shipping_method = item.get("shipping_method", "")
            if shipping_method == "直运":
                direct_items.append(item)
            else:
                warehouse_items.append(item)

        preview_orders = []

        # 批量查询品牌的采购人
        all_brand_ids = set()
        for item in enriched_items:
            bid = item.get("brand_id")
            if bid:
                all_brand_ids.add(bid)
        brand_purchaser_map = await self._get_brand_purchaser_map(all_brand_ids)

        # 直运商品：按 brand_id 分组
        direct_by_brand = {}
        for item in direct_items:
            brand_id = item.get("brand_id")
            if not brand_id:
                logger.warning(f"商品 {item.get('spec_id')} 缺少品牌ID，跳过采购单生成")
                continue
            if brand_id not in direct_by_brand:
                direct_by_brand[brand_id] = []
            direct_by_brand[brand_id].append(item)

        for brand_id, brand_items in direct_by_brand.items():
            purchase_items = []
            for idx, item in enumerate(brand_items, 1):
                purchase_items.append({
                    "row_no": idx,
                    "product_id": item.get("product_id", ""),
                    "spec_id": item.get("spec_id"),
                    "brand_id": item.get("brand_id"),
                    "brand_name": item.get("brand_name"),
                    "purchase_qty": item.get("qty", 0),
                    "in_qty": 0,
                    "return_qty": 0,
                    "purchase_price": item.get("price", 0),
                    "discount": item.get("discount", 1.0),
                    "amt": item.get("amt", 0),
                    "shipping_method": "直运",
                    "source_sale_row_no": int(item.get("row_no")) if item.get("row_no") is not None else None,
                    "warehouse_id": item.get("warehouse_id")
                })

            # 获取自动选择的供应商
            auto_supplier = await self._auto_select_supplier(brand_id)
            supplier_id = auto_supplier["id"] if auto_supplier else ""
            supplier_name = auto_supplier["name"] if auto_supplier else ""

            preview_orders.append({
                "purchase_type": "direct",
                "source_sale_order_no": order_no,
                "source_sale_order_id": order_id,
                "brand_id": brand_id,
                "brand_name": brand_items[0].get("brand_name", ""),
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "purchase_user_id": brand_purchaser_map.get(brand_id) or "",
                "receive_info": {
                    "type": "customer",
                    "customer_addr": sales_order.get("deliver_info", {}).get("addr"),
                    "province": sales_order.get("deliver_info", {}).get("province"),
                    "city": sales_order.get("deliver_info", {}).get("city"),
                    "contact_person": sales_order.get("deliver_info", {}).get("person_name"),
                    "contact_tel": sales_order.get("deliver_info", {}).get("person_tel")
                },
                "expect_arrive_date": sales_order.get("expect_deliver_date"),
                "settle_type": sales_order.get("settle_type", "月结"),
                "remark": f"由销售单{order_no}自动生成-直运采购",
                "items": purchase_items
            })

        # 仓发商品：按 brand_id 分组
        warehouse_by_brand = {}
        for item in warehouse_items:
            brand_id = item.get("brand_id")
            if not brand_id:
                logger.warning(f"商品 {item.get('spec_id')} 缺少品牌ID，跳过采购单生成")
                continue
            if brand_id not in warehouse_by_brand:
                warehouse_by_brand[brand_id] = []
            warehouse_by_brand[brand_id].append(item)

        for brand_id, brand_items in warehouse_by_brand.items():
            purchase_items = []
            for idx, item in enumerate(brand_items, 1):
                purchase_items.append({
                    "row_no": idx,
                    "product_id": item.get("product_id", ""),
                    "spec_id": item.get("spec_id"),
                    "brand_id": item.get("brand_id"),
                    "brand_name": item.get("brand_name"),
                    "purchase_qty": item.get("qty", 0),
                    "in_qty": 0,
                    "return_qty": 0,
                    "purchase_price": item.get("price", 0),
                    "discount": item.get("discount", 1.0),
                    "amt": item.get("amt", 0),
                    "shipping_method": item.get("shipping_method"),
                    "source_sale_row_no": int(item.get("row_no")) if item.get("row_no") is not None else None,
                    "warehouse_id": item.get("warehouse_id")
                })

            # 获取自动选择的供应商
            auto_supplier = await self._auto_select_supplier(brand_id)
            supplier_id = auto_supplier["id"] if auto_supplier else ""
            supplier_name = auto_supplier["name"] if auto_supplier else ""

            preview_orders.append({
                "purchase_type": "warehouse",
                "source_sale_order_no": order_no,
                "source_sale_order_id": order_id,
                "brand_id": brand_id,
                "brand_name": brand_items[0].get("brand_name", ""),
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "purchase_user_id": brand_purchaser_map.get(brand_id) or "",
                "receive_info": {
                    "type": "warehouse",
                    "warehouse_id": brand_items[0].get("warehouse_id")
                },
                "expect_arrive_date": sales_order.get("expect_deliver_date"),
                "settle_type": sales_order.get("settle_type", "月结"),
                "remark": f"由销售单{order_no}自动生成-仓库采购",
                "items": purchase_items
            })

        return preview_orders


purchase_order_service = PurchaseOrderService()
