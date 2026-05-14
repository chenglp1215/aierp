"""
销售订单管理 - 业务逻辑
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from bson import ObjectId
from services.base_service import BaseService
from services.product_service_mysql import product_service, product_spec_service, brand_service
from services.customer_service_mysql import customer_service
from validators.sales_order_validator import (
    SALES_ORDER_CREATE_CONFIG,
    SALES_ORDER_UPDATE_CONFIG,
    ORDER_STATUS_UPDATE_CONFIG,
    DELIVERY_STATUS_UPDATE_CONFIG,
    RECEIVE_STATUS_UPDATE_CONFIG,
    INVOICE_STATUS_UPDATE_CONFIG,
)
from models.sales_order import OrderStatus, DeliveryStatus, ReceiveStatus, InvoiceStatus

logger = logging.getLogger(__name__)


class SalesOrderService(BaseService):
    def __init__(self):
        super().__init__("sales_orders")

    # ============ 校验方法 ============

    def validate_sales_order_create(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict]]:
        return self.validate_data(data, SALES_ORDER_CREATE_CONFIG)

    def validate_sales_order_update(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict]]:
        return self.validate_data(data, SALES_ORDER_UPDATE_CONFIG)

    def validate_order_status_update(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict]]:
        return self.validate_data(data, ORDER_STATUS_UPDATE_CONFIG)

    def validate_delivery_status_update(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict]]:
        return self.validate_data(data, DELIVERY_STATUS_UPDATE_CONFIG)

    def validate_receive_status_update(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict]]:
        return self.validate_data(data, RECEIVE_STATUS_UPDATE_CONFIG)

    def validate_invoice_status_update(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict]]:
        return self.validate_data(data, INVOICE_STATUS_UPDATE_CONFIG)

    # ============ 格式化方法 ============

    async def format(self, order: Dict[str, Any]) -> Dict[str, Any]:
        if "_id" in order:
            order["id"] = str(order["_id"])
            del order["_id"]
        return order

    async def format_list(self, orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [await self.format(order) for order in orders]

    # ============ 订单号生成 ============

    async def generate_order_no(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"SO{today}"
        query = {"order_no": {"$regex": f"^{prefix}"}}
        count = await self.count(query)
        sequence = count + 1
        return f"{prefix}{sequence:04d}"

    # ============ 订单金额计算 ============

    def _calculate_order_totals(
        self, items: List[Dict[str, Any]], tax_rate: float, total_discount_amt: float
    ) -> Dict[str, float]:
        total_amt = 0.0
        for item in items:
            qty = item.get("qty", 0)
            price = item.get("price", 0)
            discount = item.get("discount", 1.0)
            discounted_price = round(price * discount, 2)
            amt = round(qty * discounted_price, 2)
            item["discounted_price"] = discounted_price
            item["amt"] = amt
            total_amt += amt

        tax_amt = round(total_amt * tax_rate, 2)
        total_tax_amt = round(total_amt + tax_amt, 2)
        return {
            "total_amt": round(total_amt, 2),
            "tax_amt": tax_amt,
            "total_tax_amt": total_tax_amt,
            "total_discount_amt": total_discount_amt,
        }

    # ============ 订单明细校验 ============

    def _validate_order_items(self, items: List[Dict[str, Any]]) -> None:
        if not items:
            raise ValueError("订单明细不能为空")
        for item in items:
            product_code = item.get("product_code", "")
            if not product_code:
                raise ValueError("商品编码不能为空")
            if not item.get("qty") or item["qty"] <= 0:
                raise ValueError(f"商品 {product_code} 的数量必须大于0")
            if item.get("price", 0) < 0:
                raise ValueError(f"商品 {product_code} 的单价不能为负数")
            if not (0 <= item.get("discount", 1) <= 1):
                raise ValueError(f"商品 {product_code} 的折扣率必须在0-1之间")

    # ============ 商品信息富化 ============

    async def _enrich_items_with_product_info(self, items: List[Dict[str, Any]]) -> None:
        if not items:
            return
        product_spec_pairs = [
            (item.get("product_code"), item.get("spec_code"))
            for item in items if item.get("product_code")
        ]
        if not product_spec_pairs:
            return
        product_codes = list({pair[0] for pair in product_spec_pairs if pair[0]})
        spec_codes = list({pair[1] for pair in product_spec_pairs if pair[1]})
        product_map = {p["product_code"]: p for p in await product_service.get_product_by_codes(product_codes)}
        spec_map = {s["spec_code"]: s for s in await product_spec_service.get_spec_by_codes(spec_codes)}
        for item in items:
            product_code = item.get("product_code")
            spec_code = item.get("spec_code")
            if not product_code:
                raise ValueError("商品编码不能为空")
            product_info = product_map.get(product_code) or {}
            item["product_name"] = product_info.get("name", "")
            item["brand_id"] = product_info.get("brand_id", "")
            item["brand_name"] = product_info.get("brand_name", "")
            if spec_code:
                spec_info = spec_map.get(spec_code) or {}
                item["spec_name"] = spec_info.get("name", "")


    async def _get_doc_no(self, doc_type: str, doc_id: str) -> Optional[str]:
        try:
            if doc_type == "outbound_order":
                from services.outbound_order_service import outbound_order_service
                doc = await outbound_order_service.get_by_id(doc_id)
                return doc.get("order_no") if doc else None
            elif doc_type == "purchase_order":
                from services.purchase_order_service import purchase_order_service
                doc = await purchase_order_service.get_by_id(doc_id)
                return doc.get("order_no") if doc else None
        except Exception as e:
            logger.warning(f"获取关联单据号失败: {doc_type}/{doc_id}, {e}")
        return None

    # ============ 构建订单数据 ============

    async def _build_order_data(
        self, data: Dict[str, Any], current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        creator_id = current_user.get("id", current_user.get("user_id", ""))
        username = current_user.get("username", current_user.get("full_name", ""))
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        customer = await customer_service.get_by_id(data.get("customer_id"))
        if not customer:
            raise ValueError("客户不存在")

        return {
            "order_date": data.get("order_date"),
            "customer_id": data.get("customer_id"),
            "customer_name": data.get("customer_name") or customer.get("name", ""),
            "sale_user_id": creator_id,
            "sale_user_name": username,
            "deliver_info": data.get("deliver_info"),
            "expect_deliver_date": data.get("expect_deliver_date"),
            "settle_type": data.get("settle_type"),
            "tax_rate": data.get("tax_rate", 0.13),
            "invoice_info": data.get("invoice_info"),
            "remark": data.get("remark"),
            "items": data.get("items", []),
            "creator_id": creator_id,
            "creator_name": username,
            "create_time": now_str,
            "update_time": now_str,
        }

    def _build_update_data(
        self, data: Dict[str, Any], current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        update_fields = [
            "order_date", "customer_id", "sale_user_id", "deliver_info",
            "expect_deliver_date", "settle_type", "tax_rate",
            "invoice_info", "remark",
        ]
        update_data = {}
        for field in update_fields:
            if field in data and data[field] is not None:
                update_data[field] = data[field]

        username = current_user.get("username", current_user.get("full_name", ""))
        update_data["updater_id"] = current_user.get("id", current_user.get("user_id", ""))
        update_data["updater_name"] = username
        update_data["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return update_data

    # ============ CRUD 方法 ============
    # 新建订单
    async def create_sales_order(
        self, data: Dict[str, Any], current_user: Dict[str, Any] = None, submit: bool = False
    ) -> Dict[str, Any]:
        current_user = current_user or {}
        valid, errors = self.validate_sales_order_create(data)
        if not valid:
            raise ValueError(errors)
        self._validate_order_items(data.get("items", []))
        order_data = await self._build_order_data(data, current_user)
        await self._enrich_items_with_product_info(order_data["items"])
        order_data["order_no"] = await self.generate_order_no()

        tax_rate = order_data.get("tax_rate", 0.13)
        totals = self._calculate_order_totals(
            order_data["items"], tax_rate, order_data.get("total_discount_amt", 0.0)
        )

        order_data.update(totals)

        from models.sales_order import OrderStatusInfo
        order_data["status"] = OrderStatusInfo().model_dump()
        db_id = await self.create(order_data)

        if submit:
            await self.update_status_by_no(order_data["order_no"], "order_status", "audited", current_user.get("username", ""))
            logger.info(f"销售订单创建并提交成功: {order_data['order_no']}")
            return {"order_no": order_data["order_no"], "id": db_id}
        else:
            logger.info(f"销售订单创建成功: {order_data['order_no']}")
            return {"order_no": order_data["order_no"], "id": db_id}

    
    def _can_transition_status(self, status_key: str, current: str, target: str) -> bool:
        transitions = {
            "order_status": {
                "draft": ["audited", "cancelled"],
                "audited": ["partially_pushed_to_purchase", "pushed_to_purchase", "closed", "cancelled"],
                "partially_pushed_to_purchase": ["pushed_to_purchase", "closed", "cancelled"],
                "pushed_to_purchase": ["closed", "cancelled"],
                "closed": [],
                "cancelled": [],
            },
        }
        return target in transitions.get(status_key, {}).get(current, [])

    # 更新订单状态
    async def update_status_by_no(
        self, order_no: str, status_key, new_status, operator: str = "system"
    ) -> bool:
        new_status_value = new_status.value if hasattr(new_status, 'value') else new_status
        if order := await self.find_one({"order_no": order_no}):
            old_status_value = order.get("status", {}).get(status_key, "draft")
            if not self._can_transition_status(status_key, old_status_value, new_status_value):
                raise ValueError( f"订单状态不允许从 {old_status_value} 变更为 {new_status_value}")
            update_data = {f"status.{status_key}": new_status_value}
            if success := await self.update(order["id"], update_data):
                await self._record_status_flow(order_no, status_key, old_status_value, new_status_value, operator)
                logger.info(f"订单状态更新成功: {order_no} {old_status_value} -> {new_status_value}")
                return True
            else:
                return False
        return False
    
    def _apply_item_updates(
        self, update_data: Dict[str, Any], original_data: Dict[str, Any]
    ) -> None:
        new_items = original_data.get("items")
        if new_items is None:
            return
        self._validate_order_items(new_items)
        items = []
        for idx, item in enumerate(new_items):
            if "row_no" not in item or not item["row_no"]:
                item["row_no"] = idx + 1
            items.append(item)
        update_data["items"] = items

    # 更新订单信息
    async def update_sales_order(
        self, order_no: str, data: Dict[str, Any], current_user: Dict[str, Any] = None
    ) -> bool:
        valid, errors = self.validate_sales_order_update(data)
        if not valid:
            raise ValueError(errors)
        current_user = current_user or {}
        order = await self.find_one({"order_no": order_no})
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        status = order.get("status", {})
        order_status = status.get("order_status", "draft")
        if order_status not in ["draft", "cancelled"]:
            raise ValueError("只能修改草稿或已取消的订单")

        update_data = self._build_update_data(data, current_user)
        self._apply_item_updates(update_data, data)
        if "items" in update_data:
            await self._enrich_items_with_product_info(update_data["items"])

        success = await self.update(order["id"], update_data)
        if success:
            logger.info(f"销售订单更新成功: {order_no}")
        return success

    async def delete_sales_order_by_no(self, order_no: str) -> bool:
        existing_order = await self.find_one({"order_no": order_no})
        if not existing_order:
            raise ValueError(f"订单不存在: {order_no}")
        status = existing_order.get("status", {})
        order_status = status.get("order_status", "draft")
        if order_status not in ["draft", "cancelled"]:
            raise ValueError("只能删除草稿或已取消的订单")
        deleted = await self.delete(existing_order["id"])
        if deleted:
            logger.info(f"销售订单删除成功: {order_no}")
        return deleted


    async def detail_by_no(self, order_no: str) -> Optional[Dict[str, Any]]:
        order = await self.get_sales_order_by_no(order_no)
        if not order:
            raise ValueError(f"订单不存在: {order_no}")
        # 预留关联采购订单字段
        order["purchase_orders"] = []
        return order
    # ============ 列表查询 ============

    async def list_sales_orders(
        self, 
        page: int = 1,
        page_size: int = 20,
        order_status: str = None,
        customer_id: str = None, 
        order_no: str = None,
        keyword: str = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = self._build_list_query(order_status, customer_id, order_no, keyword)
        skip = (page - 1) * page_size
        orders = await self.find_many(query, limit=page_size, skip=skip)
        total = await self.count(query)
        formatted_orders = await self.format_list(orders)
        return formatted_orders, total

    def _build_list_query(
        self, order_status: str = None, customer_id: str = None, order_no: str = None, keyword: str = None,
    ) -> Dict[str, Any]:
        query = {}
        if order_status:
            query["status.order_status"] = order_status
        if customer_id:
            query["customer_id"] = customer_id
        if order_no:
            query["order_no"] = {"$regex": order_no, "$options": "i"}
        if keyword:
            query["$or"] = [
                {"order_no": {"$regex": keyword, "$options": "i"}},
                {"customer_name": {"$regex": keyword, "$options": "i"}},
                {"items.product_name": {"$regex": keyword, "$options": "i"}},
                {"items.spec_code": {"$regex": keyword, "$options": "i"}}
            ]
        return query

    # ============ 详情查看 ============
    async def get_sales_order_by_no(self, order_no: str) -> Optional[Dict[str, Any]]:
        order_data = await self.find_one({"order_no": order_no})
        if order_data:
            order_data = await self.format(order_data)
        return order_data
    
    # ============ 状态流转记录 ============

    async def _record_status_flow(
        self, order_no: str, status_key: str, old_value: str, new_value: str, operator: str,
    ) -> None:
        from services.order_status_flow_service import order_status_flow_service
        await order_status_flow_service.create_flow_record(
            order_no=order_no, field=status_key, old_value=old_value,
            new_value=new_value, operator=operator,
        )

    # ============ 下推采购 ============

    async def push_to_purchase_by_no(
        self, order_no: str, selected_row_nos: List[int], current_user: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        order = await self.find_one({"order_no": order_no})
        if not order:
            raise ValueError(f"销售订单不存在: {order_no}")
        self._validate_order_for_purchase(order)
        selected_items = self._filter_selected_items(order, selected_row_nos)
        supplier_groups = self._group_items_by_supplier(selected_items)
        purchase_orders = await self._create_purchase_orders(
            order, supplier_groups, current_user
        )
        await self._update_order_after_purchase(order, selected_row_nos)
        return purchase_orders

    def _validate_order_for_purchase(self, order: Dict[str, Any]) -> None:
        status = order.get("status", {})
        order_status = status.get("order_status", "")
        valid_statuses = ["audited", "partially_pushed_to_purchase"]
        if order_status not in valid_statuses:
            raise ValueError("只有已审核或部分下推采购的订单才能下推采购")

    def _filter_selected_items(
        self, order: Dict[str, Any], selected_row_nos: List[int]
    ) -> List[Dict[str, Any]]:
        all_items = order.get("items", [])
        selected_items = [item for item in all_items if item.get("row_no") in selected_row_nos]
        if not selected_items:
            raise ValueError("未找到选中的商品明细")
        for item in selected_items:
            if item.get("pushed"):
                raise ValueError(f"商品行号 {item.get('row_no')} 已经下推过采购")
        return selected_items

    def _group_items_by_supplier(
        self, items: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        supplier_groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in items:
            supplier_id = item.get("supplier_id", "default")
            if supplier_id not in supplier_groups:
                supplier_groups[supplier_id] = []
            supplier_groups[supplier_id].append(item)
        return supplier_groups

    async def _create_purchase_orders(
        self, order: Dict[str, Any],
        supplier_groups: Dict[str, List[Dict[str, Any]]],
        current_user: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        from services.purchase_order_service import purchase_order_service
        purchase_orders = []
        for supplier_id, items in supplier_groups.items():
            purchase_order_data = self._build_purchase_order_data(
                order, supplier_id, items, current_user
            )
            purchase_order_id = await purchase_order_service.create_from_sales_order(purchase_order_data)
            purchase_orders.append({
                "purchase_order_id": purchase_order_id,
                "supplier_id": supplier_id,
                "items_count": len(items),
            })
        return purchase_orders

    def _build_purchase_order_data(
        self, order: Dict[str, Any], supplier_id: str,
        items: List[Dict[str, Any]], current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        purchase_items = []
        for idx, item in enumerate(items):
            purchase_items.append({
                "row_no": idx + 1,
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name"),
                "spec_id": item.get("spec_id"),
                "qty": item.get("qty", 0),
                "price": item.get("price", 0),
                "amt": item.get("amt", 0),
                "warehouse_id": item.get("warehouse_id"),
                "sales_order_no": order.get("order_no"),
                "sales_order_item_row_no": item.get("row_no"),
            })

        total_amt = sum(item.get("amt", 0) for item in purchase_items)
        tax_rate = order.get("tax_rate", 0.13)
        tax_amt = round(total_amt * tax_rate, 2)

        return {
            "supplier_id": supplier_id,
            "purchase_type": "normal",
            "order_date": order.get("order_date"),
            "expect_receive_date": order.get("expect_deliver_date"),
            "settle_type": order.get("settle_type", "月结"),
            "total_amt": round(total_amt, 2),
            "tax_rate": tax_rate,
            "tax_amt": tax_amt,
            "total_tax_amt": round(total_amt + tax_amt, 2),
            "remark": f"由销售订单 {order.get('order_no')} 下推生成",
            "items": purchase_items,
            "sales_order_no": order.get("order_no"),
            "customer_id": order.get("customer_id"),
        }

    async def _update_order_after_purchase(
        self, order: Dict[str, Any], selected_row_nos: List[int]
    ) -> None:
        all_items = order.get("items", [])
        all_pushed = all(
            item.get("pushed") or item.get("row_no") in selected_row_nos
            for item in all_items
        )
        new_status = "pushed_to_purchase" if all_pushed else "partially_pushed_to_purchase"
        update_items = []
        for item in all_items:
            if item.get("row_no") in selected_row_nos:
                item["pushed"] = True
            update_items.append(item)

        db_id = order["_id"]
        await self.update(str(db_id), {
            "status.order_status": new_status,
            "items": update_items,
        })
        logger.info(f"销售订单下推采购状态更新: {order.get('order_no')} -> {new_status}")


sales_order_service = SalesOrderService()
