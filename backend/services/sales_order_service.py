"""
销售订单管理 - 服务层
全新设计的销售订单服务，提供完整的CRUD操作
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import random
import string
import logging

from bson import ObjectId

from .base_service import BaseService
from models.sales_order import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderUpdate,
    OrderStatus,
    DeliveryStatus,
    ReceiveStatus,
    InvoiceStatus,
)
from validators.sales_order_validator import (
    SALES_ORDER_CREATE_CONFIG,
    SALES_ORDER_UPDATE_CONFIG,
)
from .order_status_flow_service import order_status_flow_service

logger = logging.getLogger(__name__)


class SalesOrderService(BaseService):
    """销售订单服务类"""

    def __init__(self):
        super().__init__("sales_orders")

    async def _enrich_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """富化单个订单：填充客户名称、商品名称、仓库名称"""
        if not order:
            return order

        # 富化客户名称
        customer_id = order.get("customer_id")
        if customer_id:
            try:
                customer = await self.db["customers_v2"].find_one(
                    {"_id": ObjectId(customer_id)}
                )
                if customer:
                    order["customer_name"] = customer.get("name", "")
            except Exception as e:
                logger.error(f"富化客户名称失败: {e}")

        # 富化商品明细
        items = order.get("items", [])
        if items:
            # 收集所有需要查询的 ID
            spec_ids = []
            warehouse_ids = []
            for item in items:
                if item.get("spec_id"):
                    try:
                        spec_ids.append(ObjectId(item["spec_id"]))
                    except Exception:
                        pass
                if item.get("warehouse_id"):
                    try:
                        warehouse_ids.append(ObjectId(item["warehouse_id"]))
                    except Exception:
                        pass

            # 批量查询商品规格
            spec_map = {}
            if spec_ids:
                try:
                    specs = await self.db["product_specs"].find(
                        {"_id": {"$in": spec_ids}}
                    ).to_list(length=None)
                    for spec in specs:
                        spec_map[str(spec["_id"])] = spec
                except Exception as e:
                    logger.error(f"批量查询商品规格失败: {e}")

            # 批量查询商品（从规格中获取 product_id）
            product_ids = []
            for spec in spec_map.values():
                pid = spec.get("product_id")
                if pid:
                    try:
                        product_ids.append(ObjectId(pid))
                    except Exception:
                        pass

            product_map = {}
            if product_ids:
                try:
                    products = await self.db["products"].find(
                        {"_id": {"$in": product_ids}}
                    ).to_list(length=None)
                    for p in products:
                        product_map[str(p["_id"])] = p
                except Exception as e:
                    logger.error(f"批量查询商品失败: {e}")

            # 从商品中收集 brand_id，批量查询品牌名称
            brand_ids = set()
            for p in product_map.values():
                bid = p.get("brand_id")
                if bid:
                    brand_ids.add(bid)

            brand_map = {}
            if brand_ids:
                try:
                    brands = await self.db["brands"].find(
                        {"_id": {"$in": [ObjectId(bid) for bid in brand_ids]}}
                    ).to_list(length=None)
                    for b in brands:
                        brand_map[str(b["_id"])] = b.get("name", "")
                except Exception as e:
                    logger.error(f"批量查询品牌失败: {e}")

            # 批量查询仓库
            warehouse_map = {}
            if warehouse_ids:
                try:
                    warehouses = await self.db["warehouses"].find(
                        {"_id": {"$in": warehouse_ids}}
                    ).to_list(length=None)
                    for w in warehouses:
                        warehouse_map[str(w["_id"])] = w
                except Exception as e:
                    logger.error(f"批量查询仓库失败: {e}")

            # 填充到明细行
            for item in items:
                # 商品名称
                spec_id = item.get("spec_id")
                if spec_id and spec_id in spec_map:
                    spec = spec_map[spec_id]
                    item["spec_code"] = spec.get("spec_code", item.get("spec_code", ""))
                    product_id = spec.get("product_id", "")
                    if product_id and product_id in product_map:
                        product = product_map[product_id]
                        item["product_name"] = product.get("name", item.get("product_name", ""))
                        item["product_code"] = product.get("product_code", item.get("product_code", ""))
                        # 品牌名称
                        bid = product.get("brand_id", "")
                        if bid and bid in brand_map:
                            item["brand_name"] = brand_map[bid]
                            item["brand_id"] = bid

                # 仓库名称
                warehouse_id = item.get("warehouse_id")
                if warehouse_id and warehouse_id in warehouse_map:
                    item["warehouse_name"] = warehouse_map[warehouse_id].get("name", "")

                # 库存信息（非直运且有仓库的商品）
                shipping_method = item.get("shipping_method", "")
                if shipping_method != "直运" and warehouse_id and spec_id:
                    try:
                        stock = await self.db["stocks"].find_one({
                            "warehouse_id": warehouse_id,
                            "spec_id": spec_id
                        })
                        if stock:
                            item["stock_quantity"] = stock.get("quantity", 0)
                            item["stock_status"] = stock.get("status", "normal")
                        else:
                            item["stock_quantity"] = 0
                            item["stock_status"] = "out_of_stock"
                    except Exception as e:
                        logger.error(f"查询库存失败: {e}")
                        item["stock_quantity"] = 0
                        item["stock_status"] = "out_of_stock"

        # 富化成本明细
        cost_details = order.get("cost_details", [])
        if cost_details:
            # 收集关联单据ID
            outbound_ids = []
            purchase_ids = []
            for cost in cost_details:
                doc_type = cost.get("associated_doc_type")
                doc_id = cost.get("associated_doc_id")
                if doc_id:
                    if doc_type == "outbound_order":
                        try:
                            outbound_ids.append(ObjectId(doc_id))
                        except Exception:
                            pass
                    elif doc_type == "purchase_order":
                        try:
                            purchase_ids.append(ObjectId(doc_id))
                        except Exception:
                            pass

            # 批量查询出库单
            outbound_map = {}
            if outbound_ids:
                try:
                    outbounds = await self.db["outbound_orders"].find(
                        {"_id": {"$in": outbound_ids}}
                    ).to_list(length=None)
                    for o in outbounds:
                        outbound_map[str(o["_id"])] = o.get("order_no", "")
                except Exception as e:
                    logger.error(f"批量查询出库单失败: {e}")

            # 批量查询采购单
            purchase_map = {}
            if purchase_ids:
                try:
                    purchases = await self.db["purchaseOrders"].find(
                        {"_id": {"$in": purchase_ids}}
                    ).to_list(length=None)
                    for p in purchases:
                        purchase_map[str(p["_id"])] = p.get("purchase_no", "")
                except Exception as e:
                    logger.error(f"批量查询采购单失败: {e}")

            # 填充成本明细的单据号
            for cost in cost_details:
                doc_type = cost.get("associated_doc_type")
                doc_id = cost.get("associated_doc_id")
                if doc_id:
                    if doc_type == "outbound_order" and doc_id in outbound_map:
                        cost["associated_doc_no"] = outbound_map[doc_id]
                    elif doc_type == "purchase_order" and doc_id in purchase_map:
                        cost["associated_doc_no"] = purchase_map[doc_id]

        return order

    async def _enrich_orders(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量富化订单列表"""
        if not orders:
            return orders

        # 收集所有客户 ID 和仓库 ID
        customer_ids = set()
        spec_ids = set()
        warehouse_ids = set()
        for order in orders:
            cid = order.get("customer_id")
            if cid:
                customer_ids.add(cid)
            for item in order.get("items", []):
                sid = item.get("spec_id")
                if sid:
                    spec_ids.add(sid)
                wid = item.get("warehouse_id")
                if wid:
                    warehouse_ids.add(wid)

        # 批量查询客户
        customer_map = {}
        if customer_ids:
            try:
                obj_ids = []
                for cid in customer_ids:
                    try:
                        obj_ids.append(ObjectId(cid))
                    except Exception:
                        pass
                if obj_ids:
                    customers = await self.db["customers_v2"].find(
                        {"_id": {"$in": obj_ids}}
                    ).to_list(length=None)
                    for c in customers:
                        customer_map[str(c["_id"])] = c.get("name", "")
            except Exception as e:
                logger.error(f"批量查询客户失败: {e}")

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

        # 从商品中收集 brand_id，批量查询品牌名称
        brand_ids = set()
        for p in product_map.values():
            bid = p.get("brand_id")
            if bid:
                brand_ids.add(bid)

        brand_map = {}
        if brand_ids:
            try:
                brands = await self.db["brands"].find(
                    {"_id": {"$in": [ObjectId(bid) for bid in brand_ids]}}
                ).to_list(length=None)
                for b in brands:
                    brand_map[str(b["_id"])] = b.get("name", "")
            except Exception as e:
                logger.error(f"批量查询品牌失败: {e}")

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

        # 填充到订单
        for order in orders:
            cid = order.get("customer_id")
            if cid and cid in customer_map:
                order["customer_name"] = customer_map[cid]

            for item in order.get("items", []):
                # 商品名称
                sid = item.get("spec_id")
                if sid and sid in spec_map:
                    spec = spec_map[sid]
                    item["spec_code"] = spec.get("spec_code", item.get("spec_code", ""))
                    pid = spec.get("product_id", "")
                    if pid and pid in product_map:
                        product = product_map[pid]
                        item["product_name"] = product.get("name", item.get("product_name", ""))
                        item["product_code"] = product.get("product_code", item.get("product_code", ""))
                        # 品牌名称
                        bid = product.get("brand_id", "")
                        if bid and bid in brand_map:
                            item["brand_name"] = brand_map[bid]
                            item["brand_id"] = bid

                # 仓库名称
                wid = item.get("warehouse_id")
                if wid and wid in warehouse_map:
                    item["warehouse_name"] = warehouse_map[wid]

            # 富化成本明细
            cost_details = order.get("cost_details", [])
            if cost_details:
                # 收集关联单据ID
                outbound_ids = []
                purchase_ids = []
                for cost in cost_details:
                    doc_type = cost.get("associated_doc_type")
                    doc_id = cost.get("associated_doc_id")
                    if doc_id:
                        if doc_type == "outbound_order":
                            try:
                                outbound_ids.append(ObjectId(doc_id))
                            except Exception:
                                pass
                        elif doc_type == "purchase_order":
                            try:
                                purchase_ids.append(ObjectId(doc_id))
                            except Exception:
                                pass

                # 批量查询出库单
                outbound_map = {}
                if outbound_ids:
                    try:
                        outbounds = await self.db["outbound_orders"].find(
                            {"_id": {"$in": outbound_ids}}
                        ).to_list(length=None)
                        for o in outbounds:
                            outbound_map[str(o["_id"])] = o.get("order_no", "")
                    except Exception as e:
                        logger.error(f"批量查询出库单失败: {e}")

                # 批量查询采购单
                purchase_map = {}
                if purchase_ids:
                    try:
                        purchases = await self.db["purchaseOrders"].find(
                            {"_id": {"$in": purchase_ids}}
                        ).to_list(length=None)
                        for p in purchases:
                            purchase_map[str(p["_id"])] = p.get("purchase_no", "")
                    except Exception as e:
                        logger.error(f"批量查询采购单失败: {e}")

                # 填充成本明细的单据号
                for cost in cost_details:
                    doc_type = cost.get("associated_doc_type")
                    doc_id = cost.get("associated_doc_id")
                    if doc_id:
                        if doc_type == "outbound_order" and doc_id in outbound_map:
                            cost["associated_doc_no"] = outbound_map[doc_id]
                        elif doc_type == "purchase_order" and doc_id in purchase_map:
                            cost["associated_doc_no"] = purchase_map[doc_id]

        return orders

    def _generate_order_no(self) -> str:
        """生成订单编号"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.digits, k=4))
        return f"SO{date_str}{random_str}"

    def _calculate_amounts(self, items: list, tax_rate: float = 0.13) -> Dict[str, float]:
        """计算订单金额

        Args:
            items: 商品明细列表
            tax_rate: 税率，默认13%（0.13）
        """
        total_amt = sum(item.get("amt", 0) for item in items)
        return {
            "total_amt": round(total_amt, 2),
            "tax_amt": round(total_amt * tax_rate, 2),
            "total_tax_amt": round(total_amt * (1 + tax_rate), 2)
        }

    def _calculate_item_amounts(self, item: dict) -> Dict[str, float]:
        """计算商品明细金额"""
        qty = item.get("qty", 0)
        price = item.get("price", 0)
        discount = item.get("discount", 1.0)
        discounted_price = price * discount
        amt = qty * discounted_price
        return {
            "discounted_price": round(discounted_price, 2),
            "amt": round(amt, 2)
        }

    # ============ 验证方法 ============

    def validate_sales_order_create(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证销售订单创建数据"""
        return self.validate_data(data, SALES_ORDER_CREATE_CONFIG)

    def validate_sales_order_update(self, data: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
        """验证销售订单更新数据"""
        return self.validate_data(data, SALES_ORDER_UPDATE_CONFIG)

    async def create_sales_order(self, order_data: SalesOrderCreate, current_user: dict = None) -> tuple:
        """创建销售订单，返回(order_no, db_id)"""
        data = order_data.model_dump()
        
        # 生成订单号
        data["order_no"] = self._generate_order_no()
        
        # 计算商品明细金额
        items = data.get("items", [])
        for item in items:
            item_amounts = self._calculate_item_amounts(item)
            item.update(item_amounts)
        
        # 计算订单总金额（使用前端传入的税率，默认13%）
        tax_rate = data.get("tax_rate", 0.13)
        amounts = self._calculate_amounts(items, tax_rate=tax_rate)
        data.update(amounts)
        
        # 设置默认状态
        data["status"] = {
            "order_status": OrderStatus.DRAFT.value,
            "delivery_status": DeliveryStatus.NONE.value,
            "receive_status": ReceiveStatus.NONE.value,
            "invoice_status": InvoiceStatus.NONE.value
        }

        # 获取操作人名称
        operator = "system"
        if current_user:
            operator = current_user.get("username", current_user.get("full_name", "system"))

        # 设置创建时间
        data["create_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 设置创建人ID（如果提供了当前用户）
        if current_user and "id" in current_user:
            data["creator_id"] = current_user["id"]
            # 自动设置销售人员为当前用户（如果前端未指定）
            if not data.get("sale_user_id"):
                data["sale_user_id"] = current_user["id"]
        else:
            data["creator_id"] = "system"

        # 富化客户名称和商品明细名称
        try:
            customer_id = data.get("customer_id")
            if customer_id:
                customer = await self.db["customers_v2"].find_one(
                    {"_id": ObjectId(customer_id)}
                )
                if customer:
                    data["customer_name"] = customer.get("name", "")
        except Exception as e:
            logger.error(f"保存时查询客户名称失败: {e}")

        # 富化商品明细的品牌名称和仓库名称
        # 收集所有商品规格ID，批量查询商品和品牌信息
        spec_ids = set()
        for item in items:
            spec_id = item.get("spec_id")
            if spec_id:
                try:
                    spec_ids.add(ObjectId(spec_id))
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

        # 收集所有商品ID，批量查询品牌信息
        product_ids = set()
        for spec in spec_map.values():
            pid = spec.get("product_id")
            if pid:
                try:
                    product_ids.add(ObjectId(pid))
                except Exception:
                    pass

        # 批量查询商品
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

        # 收集所有品牌ID，批量查询品牌名称
        brand_ids = set()
        for product in product_map.values():
            bid = product.get("brand_id")
            if bid:
                try:
                    brand_ids.add(ObjectId(bid))
                except Exception:
                    pass

        # 批量查询品牌
        brand_map = {}
        if brand_ids:
            try:
                brands = await self.db["brands"].find(
                    {"_id": {"$in": list(brand_ids)}}
                ).to_list(length=None)
                for b in brands:
                    brand_map[str(b["_id"])] = b.get("name", "")
            except Exception as e:
                logger.error(f"批量查询品牌失败: {e}")

        # 批量查询仓库名称（避免 N+1 查询）
        warehouse_ids = set()
        for item in items:
            wid = item.get("warehouse_id")
            if wid:
                try:
                    warehouse_ids.add(ObjectId(wid))
                except Exception:
                    pass
        warehouse_map = {}
        if warehouse_ids:
            try:
                warehouses = await self.db["warehouses"].find(
                    {"_id": {"$in": list(warehouse_ids)}}
                ).to_list(length=None)
                for w in warehouses:
                    warehouse_map[str(w["_id"])] = w.get("name", "")
            except Exception as e:
                logger.error(f"批量查询仓库失败: {e}")

        # 填充到商品明细
        for item in items:
            # 填充品牌信息
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

            # 填充仓库名称
            warehouse_id = item.get("warehouse_id")
            if warehouse_id and warehouse_id in warehouse_map:
                item["warehouse_name"] = warehouse_map[warehouse_id]
        
        # 设置累计统计字段默认值
        data["total_out_qty"] = 0
        data["total_received_amt"] = 0.0
        data["total_invoice_amt"] = 0.0
        data["total_return_qty"] = 0
        data["total_return_amt"] = 0.0
        
        # 设置商品明细的默认值
        for item in items:
            item["out_qty"] = 0
            item["return_qty"] = 0
            item["remain_out_qty"] = item.get("qty", 0)
        
        # 保存到数据库
        data["id"] = await self.create(data)
        if "_id" in data:
            data.pop("_id")

        # 创建初始流转记录
        await order_status_flow_service.create_flow_record(
            order_no=data["order_no"],
            field="order_status",
            old_value=None,
            new_value=OrderStatus.DRAFT.value,
            operator=operator,
            remark="订单创建"
        )

        return data["order_no"], data["id"]

    async def update_sales_order(self, order_no: str, order_data: SalesOrderUpdate, current_user: dict = None) -> bool:
        """更新销售订单"""
        data = order_data.model_dump(exclude_unset=True)
        
        # 如果更新了商品明细，重新计算金额
        if "items" in data:
            items = data["items"]
            for item in items:
                item_amounts = self._calculate_item_amounts(item)
                item.update(item_amounts)
            
            amounts = self._calculate_amounts(items)
            data.update(amounts)
        
        return await self.update_by_order_no(order_no, data)

    async def update_by_order_no(self, order_no: str, data: Dict[str, Any]) -> bool:
        """根据订单号更新订单"""
        result = await self.collection.update_one(
            {"order_no": order_no},
            {"$set": {**data, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    async def get_sales_order_by_no(self, order_no: str) -> Optional[Dict[str, Any]]:
        """根据订单编号获取订单"""
        order = await self.find_one({"order_no": order_no})
        if order:
            order = await self._enrich_order(order)
        return order

    async def list_sales_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        order_no: Optional[str] = None,
    ) -> Dict[str, Any]:
        """分页查询订单列表"""
        filters = {}

        if status:
            filters["status.order_status"] = status
        if customer_id:
            filters["customer_id"] = customer_id
        if order_no:
            filters["order_no"] = order_no

        result = await self.list(page, page_size, filters, "create_time", -1)

        # 富化客户名称、商品名称、仓库名称
        if result.get("items"):
            result["items"] = await self._enrich_orders(result["items"])

        return result

    async def update_order_status_by_no(self, order_no: str, status: OrderStatus, operator: str = "system") -> bool:
        """根据订单号更新订单状态（记录流转历史）"""
        # 获取当前订单状态
        order = await self.find_one({"order_no": order_no})
        if not order:
            return False

        old_status = order.get("status", {}).get("order_status", "")
        new_status = status.value

        # 如果状态没有变化，直接返回
        if old_status == new_status:
            return True

        # 更新状态
        result = await self.collection.update_one(
            {"order_no": order_no},
            {"$set": {"status.order_status": new_status, "updated_at": datetime.now()}}
        )

        if result.modified_count > 0:
            # 创建流转记录到独立表
            await order_status_flow_service.create_flow_record(
                order_no=order_no,
                field="order_status",
                old_value=old_status,
                new_value=new_status,
                operator=operator
            )
            return True
        return False

    async def create_and_submit_order(self, order_data: SalesOrderCreate, current_user: dict = None) -> tuple:
        """创建并提交订单（直接审核通过）"""
        # 先创建订单
        order_no, db_id = await self.create_sales_order(order_data, current_user)

        # 获取创建人名称
        operator = "system"
        if current_user:
            operator = current_user.get("username", current_user.get("full_name", "system"))

        # 更新状态为已审核
        await self.collection.update_one(
            {"order_no": order_no},
            {"$set": {"status.order_status": OrderStatus.AUDITED.value, "updated_at": datetime.now()}}
        )

        # 添加审核流转记录（创建记录已在 create_sales_order 中创建）
        await order_status_flow_service.create_flow_record(
            order_no=order_no,
            field="order_status",
            old_value=OrderStatus.DRAFT.value,
            new_value=OrderStatus.AUDITED.value,
            operator=operator,
            remark="提交审核"
        )

        return order_no, db_id

    async def update_delivery_status_by_no(self, order_no: str, delivery_status: DeliveryStatus, operator: str = "system") -> bool:
        """根据订单号更新发货状态"""
        order = await self.find_one({"order_no": order_no})
        if not order:
            return False

        old_value = order.get("status", {}).get("delivery_status", "")
        new_value = delivery_status.value
        if old_value == new_value:
            return True

        update_data = {"status.delivery_status": new_value}
        result = await self.update_by_order_no(order_no, update_data)
        if result:
            await order_status_flow_service.create_flow_record(
                order_no=order_no, field="delivery_status",
                old_value=old_value, new_value=new_value, operator=operator
            )
        return result

    async def update_receive_status_by_no(self, order_no: str, receive_status: ReceiveStatus, operator: str = "system") -> bool:
        """根据订单号更新收货状态"""
        order = await self.find_one({"order_no": order_no})
        if not order:
            return False

        old_value = order.get("status", {}).get("receive_status", "")
        new_value = receive_status.value
        if old_value == new_value:
            return True

        update_data = {"status.receive_status": new_value}
        result = await self.update_by_order_no(order_no, update_data)
        if result:
            await order_status_flow_service.create_flow_record(
                order_no=order_no, field="receive_status",
                old_value=old_value, new_value=new_value, operator=operator
            )
        return result

    async def update_invoice_status_by_no(self, order_no: str, invoice_status: InvoiceStatus, operator: str = "system") -> bool:
        """根据订单号更新开票状态"""
        order = await self.find_one({"order_no": order_no})
        if not order:
            return False

        old_value = order.get("status", {}).get("invoice_status", "")
        new_value = invoice_status.value
        if old_value == new_value:
            return True

        update_data = {"status.invoice_status": new_value}
        result = await self.update_by_order_no(order_no, update_data)
        if result:
            await order_status_flow_service.create_flow_record(
                order_no=order_no, field="invoice_status",
                old_value=old_value, new_value=new_value, operator=operator
            )
        return result

    async def push_to_purchase_by_no(self, order_no: str, selected_row_nos: List[int], current_user: dict = None) -> tuple:
        """下推采购：根据选中的商品行号生成采购单，并标记已下推"""
        order = await self.find_one({"order_no": order_no})
        if not order:
            raise ValueError("订单不存在")

        # 富化订单信息（包括品牌信息）
        order = await self._enrich_order(order)

        old_status = order.get("status", {}).get("order_status", "")
        allowed_statuses = [OrderStatus.AUDITED.value, OrderStatus.PARTIALLY_PUSHED_TO_PURCHASE.value]
        if old_status not in allowed_statuses:
            raise ValueError(f"当前状态不允许下推采购: {old_status}")

        items = order.get("items", [])
        selected_row_set = set(selected_row_nos)

        # 筛选选中的商品
        selected_items = []
        for item in items:
            row_no = item.get("row_no")
            # 确保 row_no 是整数类型（数据库中可能存储为字符串）
            try:
                row_no_int = int(row_no) if row_no is not None else None
            except (ValueError, TypeError):
                row_no_int = None
            if row_no_int and row_no_int in selected_row_set and not item.get("pushed", False):
                selected_items.append(item)

        if not selected_items:
            raise ValueError("没有可下推的商品")

        from services.purchase_order_service import purchase_order_service
        created_orders = await purchase_order_service.generate_from_selected_items(order, selected_items, current_user)

        # 标记选中商品为已下推
        operator = "system"
        if current_user:
            operator = current_user.get("username", current_user.get("full_name", "system"))

        for item in items:
            row_no = item.get("row_no")
            # 确保 row_no 是整数类型（数据库中可能存储为字符串）
            try:
                row_no_int = int(row_no) if row_no is not None else None
            except (ValueError, TypeError):
                row_no_int = None
            if row_no_int and row_no_int in selected_row_set and not item.get("pushed", False):
                item["pushed"] = True

        # 判断新状态：只考虑需要采购的商品（直运 + 非直运库存不足），库存充足的非直运商品不算
        pushable_items = []
        for item in items:
            shipping = item.get("shipping_method", "")
            if shipping == "直运":
                pushable_items.append(item)
            else:
                # 实时查询库存来判断是否需要采购
                warehouse_id = item.get("warehouse_id")
                spec_id = item.get("spec_id")
                stock_qty = 0
                if warehouse_id and spec_id:
                    try:
                        stock = await self.db["stocks"].find_one({
                            "warehouse_id": warehouse_id,
                            "spec_id": spec_id
                        })
                        if stock:
                            stock_qty = stock.get("quantity", 0)
                    except Exception:
                        pass
                if stock_qty < item.get("qty", 0):
                    pushable_items.append(item)

        all_pushed = len(pushable_items) > 0 and all(item.get("pushed", False) for item in pushable_items)
        any_pushed = any(item.get("pushed", False) for item in pushable_items)

        if all_pushed:
            new_status = OrderStatus.PUSHED_TO_PURCHASE.value
            remark = f"下推采购，所有商品已下推，生成{len(created_orders)}张采购单"
        elif any_pushed:
            new_status = OrderStatus.PARTIALLY_PUSHED_TO_PURCHASE.value
            remark = f"下推采购，部分商品已下推，生成{len(created_orders)}张采购单"
        else:
            new_status = old_status
            remark = f"下推采购，生成{len(created_orders)}张采购单"

        await self.collection.update_one(
            {"order_no": order_no},
            {"$set": {
                "items": items,
                "status.order_status": new_status,
                "updated_at": datetime.now()
            }}
        )

        await order_status_flow_service.create_flow_record(
            order_no=order_no,
            field="order_status",
            old_value=old_status,
            new_value=new_status,
            operator=operator,
            remark=remark
        )

        return created_orders

    async def delete_sales_order_by_no(self, order_no: str) -> bool:
        """根据订单号删除订单"""
        result = await self.collection.delete_one({"order_no": order_no})
        return result.deleted_count > 0


sales_order_service = SalesOrderService()