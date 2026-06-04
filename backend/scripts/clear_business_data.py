"""
清理业务数据脚本

清理范围：所有业务数据（产品、分类、品牌、订单、采购、库存、客户、供应商）
保留：用户、角色、权限等系统基础数据，AI 配置数据
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from urllib.parse import quote_plus
from tortoise import Tortoise
from config.settings import settings


async def init_db():
    """初始化数据库连接"""
    encoded_password = quote_plus(settings.MYSQL_PASSWORD)
    db_url = (
        f"mysql://{settings.MYSQL_USER}:{encoded_password}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
        f"?minsize=1&maxsize=5&connect_timeout=5"
    )
    await Tortoise.init(
        db_url=db_url,
        modules={"models": [
            "models_mysql.auth",
            "models_mysql.product",
            "models_mysql.customer",
            "models_mysql.warehouse",
            "models_mysql.sales_order",
            "models_mysql.purchase_order",
            "models_mysql.pending_outbound",
            "models_mysql.order_status_flow",
            "models_mysql.supplier",
            "models_mysql.ai",
        ]},
    )


async def count_records():
    """统计各表记录数"""
    from models_mysql.product import Brand, Category, Product, ProductSpec
    from models_mysql.sales_order import SalesOrder, SalesOrderItem, SalesOrderCostItem, SalesDeliverInfo, SalesInvoiceInfo
    from models_mysql.purchase_order import PurchaseOrder, PurchaseOrderItem
    from models_mysql.warehouse import Stock, Warehouse, WarehouseLocation, InboundBatch, OutboundBatch
    from models_mysql.customer import Customer, CustomerResearchGroup, InvoiceInfo, ShippingAddress, CustomerDiscount
    from models_mysql.supplier import Supplier, SupplierBankAccount, SupplierBrand
    from models_mysql.pending_outbound import PendingOutboundOrder
    from models_mysql.order_status_flow import OrderStatusFlow

    tables = [
        ("brands", Brand),
        ("categories", Category),
        ("products", Product),
        ("product_specs", ProductSpec),
        ("sales_orders", SalesOrder),
        ("sales_order_items", SalesOrderItem),
        ("sales_order_cost_items", SalesOrderCostItem),
        ("sales_deliver_infos", SalesDeliverInfo),
        ("sales_invoice_infos", SalesInvoiceInfo),
        ("pending_outbound_orders", PendingOutboundOrder),
        ("order_status_flows", OrderStatusFlow),
        ("purchase_orders", PurchaseOrder),
        ("purchase_order_items", PurchaseOrderItem),
        ("stocks", Stock),
        ("warehouses", Warehouse),
        ("warehouse_locations", WarehouseLocation),
        ("inbound_batches", InboundBatch),
        ("outbound_batches", OutboundBatch),
        ("customers", Customer),
        ("customer_research_group", CustomerResearchGroup),
        ("invoice_infos", InvoiceInfo),
        ("shipping_addresses", ShippingAddress),
        ("customer_discounts", CustomerDiscount),
        ("suppliers", Supplier),
        ("supplier_bank_accounts", SupplierBankAccount),
        ("supplier_brands", SupplierBrand),
    ]

    print("\n=== 当前数据统计 ===")
    total = 0
    for name, model in tables:
        count = await model.all().count()
        total += count
        print(f"  {name}: {count} 条")
    print(f"  总计: {total} 条\n")
    return total


async def clear_all_business_data():
    """清理所有业务数据"""
    from models_mysql.product import Brand, Category, Product, ProductSpec
    from models_mysql.sales_order import SalesOrder, SalesOrderItem, SalesOrderCostItem, SalesDeliverInfo, SalesInvoiceInfo
    from models_mysql.purchase_order import PurchaseOrder, PurchaseOrderItem
    from models_mysql.warehouse import Stock, Warehouse, WarehouseLocation, InboundBatch, OutboundBatch
    from models_mysql.customer import Customer, CustomerResearchGroup, InvoiceInfo, ShippingAddress, CustomerDiscount
    from models_mysql.supplier import Supplier, SupplierBankAccount, SupplierBrand
    from models_mysql.pending_outbound import PendingOutboundOrder
    from models_mysql.order_status_flow import OrderStatusFlow

    print("开始清理业务数据...")

    # 按依赖关系从叶子到根清理
    # 第1层
    print("  [1/8] 清理 order_status_flows...")
    await OrderStatusFlow.all().delete()
    print("  [1/8] 清理 outbound_batches...")
    await OutboundBatch.all().delete()
    print("  [1/8] 清理 sales_invoice_infos...")
    await SalesInvoiceInfo.all().delete()

    # 第2层
    print("  [2/8] 清理 inbound_batches...")
    await InboundBatch.all().delete()
    print("  [2/8] 清理 pending_outbound_orders...")
    await PendingOutboundOrder.all().delete()
    print("  [2/8] 清理 sales_deliver_infos...")
    await SalesDeliverInfo.all().delete()
    print("  [2/8] 清理 sales_order_cost_items...")
    await SalesOrderCostItem.all().delete()
    print("  [2/8] 清理 sales_order_items...")
    await SalesOrderItem.all().delete()
    print("  [2/8] 清理 purchase_order_items...")
    await PurchaseOrderItem.all().delete()
    print("  [2/8] 清理 stocks...")
    await Stock.all().delete()
    print("  [2/8] 清理 warehouse_locations...")
    await WarehouseLocation.all().delete()

    # 第3层
    print("  [3/8] 清理 sales_orders...")
    await SalesOrder.all().delete()
    print("  [3/8] 清理 purchase_orders...")
    await PurchaseOrder.all().delete()
    print("  [3/8] 清理 warehouses...")
    await Warehouse.all().delete()

    # 第4层
    print("  [4/8] 清理 customer_research_group...")
    await CustomerResearchGroup.all().delete()
    print("  [4/8] 清理 invoice_infos...")
    await InvoiceInfo.all().delete()
    print("  [4/8] 清理 shipping_addresses...")
    await ShippingAddress.all().delete()
    print("  [4/8] 清理 customer_discounts...")
    await CustomerDiscount.all().delete()
    print("  [4/8] 清理 supplier_bank_accounts...")
    await SupplierBankAccount.all().delete()
    print("  [4/8] 清理 supplier_brands...")
    await SupplierBrand.all().delete()

    # 第5层
    print("  [5/8] 清理 customers...")
    await Customer.all().delete()
    print("  [5/8] 清理 suppliers...")
    await Supplier.all().delete()

    # 第6层
    print("  [6/8] 清理 product_specs...")
    await ProductSpec.all().delete()

    # 第7层
    print("  [7/8] 清理 products...")
    await Product.all().delete()

    # 第8层：根表
    print("  [8/8] 清理 brands...")
    await Brand.all().delete()
    print("  [8/8] 清理 categories（按层级清理）...")
    # 分类有自引用，按层级清理叶子节点
    while await Category.all().count() > 0:
        leaf_ids = []
        all_categories = await Category.all()
        for cat in all_categories:
            children = await Category.filter(parent_id=cat.id).count()
            if children == 0:
                leaf_ids.append(cat.id)
        if leaf_ids:
            await Category.filter(id__in=leaf_ids).delete()
        else:
            await Category.all().delete()
            break

    print("\n业务数据清理完成！")


async def main():
    print("=" * 50)
    print("AIERP 业务数据清理脚本")
    print("=" * 50)

    await init_db()

    total_before = await count_records()

    if total_before == 0:
        print("数据库中没有业务数据，无需清理。")
        await Tortoise.close_connections()
        return

    confirm = input(f"\n确认要清理以上 {total_before} 条业务数据吗？(yes/no): ")
    if confirm.lower() != "yes":
        print("已取消清理操作。")
        await Tortoise.close_connections()
        return

    await clear_all_business_data()

    print("\n=== 清理后数据统计 ===")
    total_after = await count_records()

    print(f"\n清理完成！共删除 {total_before - total_after} 条记录。")

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
