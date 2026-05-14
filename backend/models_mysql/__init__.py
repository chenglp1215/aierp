"""
MySQL ORM 模型（Tortoise ORM）
"""
from .auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType
from .product import Brand, Category, Product, ProductSpec
from .customer import Customer, InvoiceInfo, ShippingAddress, CustomerDiscount
from .stock_check import StockCheckBatch, StockCheckRecord
from .warehouse import Warehouse, Stock, InboundBatch, OutboundBatch

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
]