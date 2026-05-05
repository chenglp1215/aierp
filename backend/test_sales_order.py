"""
销售订单模块测试
"""
import asyncio
from datetime import datetime
from models.sales_order import (
    SalesOrderCreate,
    SalesOrderUpdate,
    OrderStatus,
    DeliveryStatus,
    ReceiveStatus,
    InvoiceStatus,
    SettleType,
    ShippingMethod,
    DeliverInfo,
    InvoiceInfo,
    OrderStatusInfo,
    SalesOrderItem
)
from services.sales_order_service import sales_order_service


async def test_create_order():
    """测试创建销售订单"""
    print("测试创建销售订单...")
    
    # 创建订单数据
    order_data = {
        "order_date": "2025-01-01",
        "customer_id": "507f1f77bcf86cd799439012",
        "sale_user_id": "507f1f77bcf86cd799439013",
        "deliver_info": {
            "addr": "详细地址",
            "province": "省",
            "city": "市",
            "person_name": "收货人",
            "person_tel": "联系电话"
        },
        "expect_deliver_date": "2025-01-10",
        "settle_type": "月结",
        "invoice_info": {
            "invoice_title": "公司全称",
            "tax_number": "纳税人识别号",
            "bank_name": "开户行",
            "bank_account": "银行账号"
        },
        "remark": "急单",
        "items": [
            {
                "row_no": 1,
                "product_id": "507f1f77bcf86cd799439012",
                "spec_id": "507f1f77bcf86cd799439013",
                "qty": 2,
                "price": 5000,
                "discount": 0.8,
                "warehouse_id": "507f1f77bcf86cd799439020",
                "shipping_method": "直运"
            }
        ]
    }
    
    # 验证数据
    is_valid, errors = sales_order_service.validate_sales_order_create(order_data)
    if not is_valid:
        print(f"数据验证失败: {errors}")
        return False
    
    # 创建订单
    try:
        order = SalesOrderCreate(**order_data)
        order_no, db_id = await sales_order_service.create_sales_order(order)
        print(f"订单创建成功: {order_no}, ID: {db_id}")
        return True
    except Exception as e:
        print(f"订单创建失败: {e}")
        return False


async def test_get_order():
    """测试获取销售订单"""
    print("测试获取销售订单...")
    
    # 获取订单
    try:
        order = await sales_order_service.get_sales_order_by_no("SO202501010001")
        if order:
            print(f"获取订单成功: {order['order_no']}")
            return True
        else:
            print("订单不存在")
            return False
    except Exception as e:
        print(f"获取订单失败: {e}")
        return False


async def test_update_order():
    """测试更新销售订单"""
    print("测试更新销售订单...")
    
    # 更新订单数据
    update_data = {
        "remark": "更新后的备注"
    }
    
    # 验证数据
    is_valid, errors = sales_order_service.validate_sales_order_update(update_data)
    if not is_valid:
        print(f"数据验证失败: {errors}")
        return False
    
    # 更新订单
    try:
        order_update = SalesOrderUpdate(**update_data)
        success = await sales_order_service.update_sales_order("SO202501010001", order_update)
        if success:
            print("订单更新成功")
            return True
        else:
            print("订单更新失败")
            return False
    except Exception as e:
        print(f"订单更新失败: {e}")
        return False


async def test_update_status():
    """测试更新订单状态"""
    print("测试更新订单状态...")
    
    # 更新订单状态
    try:
        success = await sales_order_service.update_order_status_by_no("SO202501010001", OrderStatus.AUDITED)
        if success:
            print("订单状态更新成功")
            return True
        else:
            print("订单状态更新失败")
            return False
    except Exception as e:
        print(f"订单状态更新失败: {e}")
        return False


async def test_list_orders():
    """测试获取订单列表"""
    print("测试获取订单列表...")
    
    # 获取订单列表
    try:
        result = await sales_order_service.list_sales_orders(page=1, page_size=10)
        print(f"获取订单列表成功，共 {result['total']} 条记录")
        return True
    except Exception as e:
        print(f"获取订单列表失败: {e}")
        return False


async def test_delete_order():
    """测试删除销售订单"""
    print("测试删除销售订单...")
    
    # 删除订单
    try:
        success = await sales_order_service.delete_sales_order_by_no("SO202501010001")
        if success:
            print("订单删除成功")
            return True
        else:
            print("订单删除失败")
            return False
    except Exception as e:
        print(f"订单删除失败: {e}")
        return False


async def main():
    """运行所有测试"""
    print("开始销售订单模块测试...")
    print("=" * 50)
    
    # 运行测试
    results = []
    
    # 创建订单测试
    results.append(await test_create_order())
    
    # 获取订单测试
    results.append(await test_get_order())
    
    # 更新订单测试
    results.append(await test_update_order())
    
    # 更新状态测试
    results.append(await test_update_status())
    
    # 获取列表测试
    results.append(await test_list_orders())
    
    # 删除订单测试
    results.append(await test_delete_order())
    
    print("=" * 50)
    print(f"测试完成: {sum(results)}/{len(results)} 通过")
    
    return all(results)


if __name__ == "__main__":
    asyncio.run(main())