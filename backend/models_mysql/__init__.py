"""
MySQL ORM 模型（Tortoise ORM）
"""
from .auth import User, Role, Permission, UserStatus, RoleStatus, PermissionType
from .product import Brand, Category, Product, ProductSpec
from .customer import Customer, InvoiceInfo, ShippingAddress, CustomerDiscount, CustomerResearchGroup
from .warehouse import Warehouse, Stock, InboundBatch, OutboundBatch, WarehouseLocation
from .sales_order import (
    SalesOrder, SalesOrderItem, SalesDeliverInfo,
    OrderStatus, DeliveryStatus, ReceiveStatus, InvoiceStatus, ShippingMethod, PushStatus
)
from .purchase_order import (
    PurchaseOrder, PurchaseOrderItem,
    PurchaseType, PurchaseStatus, InStatus, PayStatus
)
from .pending_outbound import PendingOutboundOrder, PendingOutboundStatus, OutboundType, LogisticsStatus, DeliveryType
from .order_status_flow import OrderStatusFlow
from .supplier import Supplier, SupplierBankAccount, SupplierBrand

from .ai import (
    LlmModel, LlmConfig, LlmModelType, LlmModelStatus,
    KnowledgeBase, KnowledgeBaseType,
    McpServer, McpServerType, McpServerStatus,
    Skill, SkillCategory,
    Agent
)

from .import_task import ImportTask

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
    "Warehouse",
    "Stock",
    "InboundBatch",
    "OutboundBatch",
    "WarehouseLocation",
    # 销售订单
    "SalesOrder",
    "SalesOrderItem",
    "SalesDeliverInfo",
    "OrderStatus",
    "DeliveryStatus",
    "ReceiveStatus",
    "InvoiceStatus",
    "ShippingMethod",
    "PushStatus",
    # 采购单
    "PurchaseOrder",
    "PurchaseOrderItem",
    "PurchaseType",
    "PurchaseStatus",
    "InStatus",
    "PayStatus",
    # 待出库单
    "PendingOutboundOrder",
    "PendingOutboundStatus",
    "OutboundType",
    "LogisticsStatus",
    "DeliveryType",
    # 状态流转
    "OrderStatusFlow",
    # 供应商
    "Supplier",
    "SupplierBankAccount",
    "SupplierBrand",
    # AI 智能配置
    "LlmModel",
    "LlmConfig",
    "LlmModelType",
    "LlmModelStatus",
    "KnowledgeBase",
    "KnowledgeBaseType",
    "McpServer",
    "McpServerType",
    "McpServerStatus",
    "Skill",
    "SkillCategory",
    "Agent",
    # 导入任务
    "ImportTask",
]