"""
MySQL ORM 模型（Tortoise ORM）
"""
from .auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType
from .product import Brand, Category, Product, ProductSpec
from .customer import Customer, InvoiceInfo, ShippingAddress, CustomerDiscount
from .stock_check import StockCheckBatch, StockCheckRecord
from .warehouse import Warehouse, Stock, InboundBatch, OutboundBatch
from .sales_order import (
    SalesOrder, SalesOrderItem, SalesDeliverInfo,
    OrderStatus, DeliveryStatus, ReceiveStatus, InvoiceStatus, ShippingMethod
)
from .purchase_order import (
    PurchaseOrder, PurchaseOrderItem,
    PurchaseType, PurchaseStatus, InStatus, PayStatus
)
from .order_status_flow import OrderStatusFlow

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
    "StockCheckBatch",
    "StockCheckRecord",
    "Warehouse",
    "Stock",
    "InboundBatch",
    "OutboundBatch",
    # 销售订单
    "SalesOrder",
    "SalesOrderItem",
    "SalesDeliverInfo",
    "OrderStatus",
    "DeliveryStatus",
    "ReceiveStatus",
    "InvoiceStatus",
    "ShippingMethod",
    # 采购单
    "PurchaseOrder",
    "PurchaseOrderItem",
    "PurchaseType",
    "PurchaseStatus",
    "InStatus",
    "PayStatus",
    # 状态流转
    "OrderStatusFlow",
]