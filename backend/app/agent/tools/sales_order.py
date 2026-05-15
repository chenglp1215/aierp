from typing import Any, Dict, Optional
import logging

from app.agent.tools.base import BaseTool, ToolResult
from services.sales_order_service_mysql import sales_order_service_mysql as sales_order_service
from services.inventory_service_mysql import warehouse_service
from models.sales_order import SalesOrderCreate, SalesOrderUpdate

logger = logging.getLogger(__name__)


class SalesOrderSearchTool(BaseTool):
    name = "sales_order_search"
    cn_name = "搜索订单"
    description = "搜索销售订单。当用户询问订单情况、查看订单列表、搜索特定订单时使用。"
    permission_code = "order.view"
    parameters = {
        "type": "object",
        "properties": {
            "order_no": {
                "type": "string",
                "description": "订单号筛选",
                "example": "SO202401010001"
            },
            "status": {
                "type": "string",
                "description": "订单状态筛选：pending(待确认)、confirmed(已确认)、shipped(已发货)、completed(已完成)、cancelled(已取消)",
                "example": "pending"
            },
            "customer_id": {
                "type": "string",
                "description": "客户ID",
                "example": "60f1b2c3d4e5f6a7b8c9d0e1"
            },
            "customer_name": {
                "type": "string",
                "description": "客户名称",
                "example": "张三"
            },
            "warehouse_id": {
                "type": "string",
                "description": "仓库ID",
                "example": "60f1b2c3d4e5f6a7b8c9d0e1"
            },
            "warehouse_name": {
                "type": "string",
                "description": "仓库名称",
                "example": "西安仓"
            },
            "page": {
                "type": "integer",
                "description": "页码，默认1",
                "default": 1,
                "example": 1
            },
            "product_name": {
                "type": "string",
                "description": "商品名称",
                "example": "商品A"
            },
            "page_size": {
                "type": "integer",
                "description": "每页数量，默认20",
                "default": 20,
                "example": 20
            }
        },
        "required": []
    }

    async def execute(
        self,
        order_no: Optional[str] = None,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        warehouse_name: Optional[str] = None,
        product_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Sales order search: order_no={order_no}, status={status}, warehouse_id={warehouse_id}, warehouse_name={warehouse_name}, product_name={product_name}, customer_id={customer_id}, customer_name={customer_name}")
        
            query_params = {
                "page": page,
                "page_size": page_size,
            }
            if status:
                query_params["status"] = status
            if customer_id:
                query_params["customer_id"] = customer_id
            if customer_name:
                query_params["customer_name"] = customer_name
            if warehouse_id:
                query_params["warehouse_id"] = warehouse_id
            if warehouse_name:
                query_params["warehouse_name"] = warehouse_name
            if product_name:
                query_params["items__product_name"] = [product_name]
            if order_no:
                query_params["order_no"] = order_no

            result = await sales_order_service.list_orders(
                **query_params
            )

            items = result.get("items", [])
            if not items:
                return ToolResult(
                    success=True,
                    content="未找到订单记录",
                    metadata={"total": 0}
                )

            content_lines = [f"共找到 {result.get('total', 0)} 条订单记录："]
            for order in items[:10]:
                content_lines.append(
                    f"[订单号:{order.get('order_no', 'N/A')}] "
                    f"[ID:{order.get('id', 'N/A')}] "
                    f"客户: {order.get('customer_name', 'N/A')} | "
                    f"金额: ¥{order.get('final_amount', 0)} | "
                    f"状态: {order.get('status', 'N/A')} | "
                    f"付款: {order.get('payment_status', 'N/A')}"
                )

            return ToolResult(
                success=True,
                content="\n".join(content_lines),
                metadata={"total": result.get("total", 0)}
            )

        except Exception as e:
            logger.error(f"Sales order search failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class SalesOrderCreateTool(BaseTool):
    name = "sales_order_create"
    cn_name = "创建订单"
    description = "创建新的销售订单。当用户要求新建订单、下单、创建销售订单时使用。"
    permission_code = "order.create"
    parameters = {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "客户ID（必填）",
                "example": "60f1b2c3d4e5f6a7b8c9d0e1"
            },
            "customer_name": {
                "type": "string",
                "description": "客户名称（必填）",
                "example": "深圳市某某公司"
            },
            "warehouse_code": {
                "type": "string",
                "description": "仓库编码（delivery_type为inventory时必填）",
                "example": "WH20260420535610"
            },
            "delivery_type": {
                "type": "string",
                "description": "发货方式：inventory(库存发货)、direct(采购直发)，默认inventory",
                "default": "inventory",
                "example": "inventory"
            },
            "pickup_type": {
                "type": "string",
                "description": "提货方式：self_pickup(自取)、express(快递)，默认express",
                "default": "express",
                "example": "express"
            },
            "express_type": {
                "type": "string",
                "description": "快递类型：sf(顺丰)、yto(圆通)、zto(中通)、jd(京东)、ems(EMS)、other(其他)",
                "example": "sf"
            },
            "express_fee": {
                "type": "number",
                "description": "快递费用，默认0",
                "default": 0,
                "example": 12
            },
            "items": {
                "type": "array",
                "description": "订单商品列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "description": "商品ID", "example": "60f1b2c3d4e5f6a7b8c9d0e3"},
                        "product_name": {"type": "string", "description": "商品名称", "example": "iPhone 15"},
                        "product_code": {"type": "string", "description": "商品编码", "example": "IPHONE15-001"},
                        "quantity": {"type": "number", "description": "数量", "example": 2},
                        "unit_price": {"type": "number", "description": "单价", "example": 6999},
                        "subtotal": {"type": "number", "description": "小计金额", "example": 13998}
                    }
                }
            },
            "discount_ratio": {
                "type": "number",
                "description": "折扣比例(0-100)，默认100表示无折扣",
                "default": 100,
                "example": 100
            },
            "notes": {
                "type": "string",
                "description": "订单备注",
                "example": "请尽快发货"
            }
        },
        "required": ["customer_id", "customer_name", "items"]
    }

    async def execute(
        self,
        customer_id: str,
        customer_name: str,
        items: list,
        warehouse_code: Optional[str] = None, 
        delivery_type: str = "inventory",
        pickup_type: str = "express",
        express_type: Optional[str] = None,
        express_fee: float = 0,
        discount_ratio: float = 100,
        notes: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Sales order create: customer={customer_name}, items_count={len(items)}")

            from models.sales_order import PickupType, ExpressType

            pickup_type_enum = PickupType(pickup_type) if pickup_type else PickupType.EXPRESS
            express_type_enum = ExpressType(express_type) if express_type else None
            warehouse_name = None
            warehouse_id = None
            if warehouse_code is None and delivery_type == "inventory":
                raise Exception("仓库编码不能为空")
            if warehouse_code:
                warehouse = await warehouse_service.get_warehouse_by_code(warehouse_code)
                if not warehouse:
                    raise Exception(f"仓库编码 {warehouse_code} 不存在")    
                warehouse_name = warehouse.get("name")
                warehouse_id = warehouse.get("id")

            order_data = SalesOrderCreate(
                customer_id=customer_id,
                customer_name=customer_name,
                warehouse_id=warehouse_id,
                warehouse_name=warehouse_name,
                delivery_type=delivery_type,
                pickup_type=pickup_type_enum,
                express_type=express_type_enum,
                express_fee=express_fee,
                items=items,
                discount_ratio=discount_ratio,
                remarks=notes
            )

            order_no, db_id = await sales_order_service.create_order(order_data)

            return ToolResult(
                success=True,
                content=f"订单创建成功！订单号: {order_no}",
                metadata={"order_no": order_no, "db_id": db_id}
            )

        except Exception as e:
            logger.error(f"Sales order create failed: {e}")
            return ToolResult(success=False, content="", error=str(e))


class SalesOrderDetailTool(BaseTool):
    name = "sales_order_detail"
    cn_name = "订单详情管理"
    description = "管理订单详情。当用户要求修改订单信息、确认订单、发货、完成订单、取消订单、更新付款状态时使用。"
    permission_code = "order.edit"
    parameters = {
        "type": "object",
        "properties": {
            "order_no": {
                "type": "string",
                "description": "订单编号（必填）",
                "example": "SO20260416001"
            },
            "action": {
                "type": "string",
                "description": "操作类型：update_info(更新订单信息)、confirm(确认订单)、ship(发货)、complete(完成订单)、cancel(取消订单)、update_payment(更新付款状态)",
                "example": "update_info"
            },
            "customer_id": {
                "type": "string",
                "description": "客户ID",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            },
            "customer_name": {
                "type": "string",
                "description": "客户名称",
                "example": "深圳市新客户公司"
            },
            "contact_phone": {
                "type": "string",
                "description": "联系电话",
                "example": "13900139000"
            },
            "delivery_address": {
                "type": "string",
                "description": "交货地址",
                "example": "深圳市南山区科技园"
            },
            "warehouse_id": {   
                "type": "string",
                "description": "仓库ID",
                "example": "60f1b2c3d4e5f6a7b8c9d0e2"
            },
            "delivery_type": {
                "type": "string",
                "description": "发货方式：inventory(库存发货)、direct(采购直发)",
                "example": "inventory"
            },
            "pickup_type": {
                "type": "string",
                "description": "提货方式：self_pickup(自取)、express(快递)",
                "example": "express"
            },
            "express_type": {
                "type": "string",
                "description": "快递类型：sf(顺丰)、yto(圆通)、zto(中通)、jd(京东)、ems(EMS)、other(其他)",
                "example": "sf"
            },
            "express_no": {
                "type": "string",
                "description": "快递单号",
                "example": "SF1234567890"
            },
            "express_fee": {
                "type": "number",
                "description": "快递费用",
                "example": 15
            },
            "discount_ratio": {
                "type": "number",
                "description": "折扣比例(0-100)",
                "example": 95
            },
            "remarks": {
                "type": "string",
                "description": "订单备注",
                "example": "备注信息"
            },
            "payment_status": {
                "type": "string",
                "description": "付款状态：paid(已付款)、unpaid(未付款)、partial(部分付款)",
                "example": "paid"
            }
        },
        "required": ["order_no", "action"]
    }

    async def execute(
        self,
        order_no: str,
        action: str,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        contact_phone: Optional[str] = None,
        delivery_address: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        delivery_type: Optional[str] = None,
        pickup_type: Optional[str] = None,
        express_type: Optional[str] = None,
        express_no: Optional[str] = None,
        express_fee: Optional[float] = None,
        discount_ratio: Optional[float] = None,
        remarks: Optional[str] = None,
        payment_status: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        try:
            logger.info(f"Sales order detail: order_no={order_no}, action={action}")

            if action == "update_info":
                return await self._update_order_info(
                    order_no, customer_id, customer_name, contact_phone,
                    delivery_address, warehouse_id, delivery_type, pickup_type,
                    express_type, express_no, express_fee, discount_ratio, remarks
                )
            elif action in ["confirm", "ship", "complete", "cancel"]:
                return await self._update_order_status(order_no, action)
            elif action == "update_payment":
                return await self._update_payment_status(order_no, payment_status)
            else:
                return ToolResult(
                    success=False,
                    content=f"无效的操作类型: {action}，可选: update_info/confirm/ship/complete/cancel/update_payment"
                )

        except Exception as e:
            logger.error(f"Sales order detail failed: {e}")
            return ToolResult(success=False, content="", error=str(e))

    async def _update_order_info(
        self,
        order_no: str,
        customer_id: Optional[str],
        customer_name: Optional[str],
        contact_phone: Optional[str],
        delivery_address: Optional[str],
        warehouse_id: Optional[str], 
        delivery_type: Optional[str],
        pickup_type: Optional[str],
        express_type: Optional[str],
        express_no: Optional[str],
        express_fee: Optional[float],
        discount_ratio: Optional[float],
        remarks: Optional[str]
    ) -> ToolResult:
        from models.sales_order import DeliveryType, PickupType, ExpressType

        update_data = SalesOrderUpdate()
        if customer_id is not None:
            update_data.customer_id = customer_id
        if customer_name is not None:
            update_data.customer_name = customer_name
        if contact_phone is not None:
            update_data.contact_phone = contact_phone
        if delivery_address is not None:
            update_data.delivery_address = delivery_address
        if warehouse_id is not None:
            update_data.warehouse_id = warehouse_id
            update_data.warehouse_name = await warehouse_service.get_by_id(warehouse_id).get("name")
        if delivery_type is not None:
            update_data.delivery_type = DeliveryType(delivery_type)
        if pickup_type is not None:
            update_data.pickup_type = PickupType(pickup_type)
        if express_type is not None:
            update_data.express_type = ExpressType(express_type)
        if express_no is not None:
            update_data.express_no = express_no
        if express_fee is not None:
            update_data.express_fee = express_fee
        if discount_ratio is not None:
            update_data.discount_ratio = discount_ratio
        if remarks is not None:
            update_data.remarks = remarks

        success = await sales_order_service.update_order(order_no, update_data)

        if success:
            return ToolResult(success=True, content="订单信息更新成功")
        else:
            return ToolResult(success=False, content="订单信息更新失败")

    async def _update_order_status(self, order_no: str, action: str) -> ToolResult:
        from models.sales_order import OrderStatus

        action_map = {
            "confirm": OrderStatus.CONFIRMED,
            "ship": OrderStatus.SHIPPED,
            "complete": OrderStatus.COMPLETED,
            "cancel": OrderStatus.CANCELLED
        }

        status = action_map[action]
        success = await sales_order_service.update_status_by_order_no(order_no, status)

        if success:
            return ToolResult(success=True, content=f"订单状态已更新为: {status.value}")
        else:
            return ToolResult(success=False, content="订单状态更新失败")

    async def _update_payment_status(self, order_no: str, payment_status: str) -> ToolResult:
        from models.sales_order import PaymentStatus

        status_map = {
            "paid": PaymentStatus.PAID,
            "unpaid": PaymentStatus.UNPAID,
            "partial": PaymentStatus.PARTIAL
        }

        if payment_status not in status_map:
            return ToolResult(
                success=False,
                content=f"无效的付款状态: {payment_status}，可选: paid/unpaid/partial"
            )

        success = await sales_order_service.update_payment_status_by_order_no(
            order_no, status_map[payment_status]
        )

        if success:
            return ToolResult(success=True, content=f"付款状态已更新为: {payment_status}")
        else:
            return ToolResult(success=False, content="付款状态更新失败")


def register_sales_order_tools():
    from app.agent import agent_manager

    agent_manager.register_tool(SalesOrderSearchTool())
    agent_manager.register_tool(SalesOrderCreateTool())
    agent_manager.register_tool(SalesOrderDetailTool())
    logger.info("Sales order tools registered")
