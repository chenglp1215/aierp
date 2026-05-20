"""测试销售订单状态更新功能

本测试文件测试 SalesOrderService 中的状态计算和更新逻辑：
- 下推状态计算（_calculate_push_status）
- 发货状态计算（_calculate_delivery_status）
- 选择性状态更新（update_order_status）
- 状态变更记录（OrderStatusFlow）
- 预留状态接口

运行方式:
    cd backend
    python -m pytest tests/test_order_status_update.py -v

注意: 这些测试需要数据库连接，建议使用测试数据库运行。
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

# 导入被测试的模块
from services.sales_order_service_mysql import SalesOrderService
from models_mysql.sales_order import (
    SalesOrder, SalesOrderItem,
    PushStatus, DeliveryStatus, ReceiveStatus,
    InvoiceStatus, FinanceStatus, ShippingMethod, OrderStatus
)
from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
from models_mysql.order_status_flow import OrderStatusFlow


# ============ Task 3.1: 测试下推状态计算逻辑 ============

@pytest.mark.asyncio
async def test_calculate_push_status_all_not_needed():
    """测试全部无需采购场景

    场景: 所有明细的 purchase_qty == 0
    预期: 返回 PushStatus.NOT_NEEDED
    """
    service = SalesOrderService()

    # 模拟订单明细全部 purchase_qty == 0
    mock_items = [
        MagicMock(spec=SalesOrderItem, purchase_qty=0, pushed_qty=0),
        MagicMock(spec=SalesOrderItem, purchase_qty=0, pushed_qty=0),
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_filter:
        mock_filter.return_value.all = AsyncMock(return_value=mock_items)

        result = await service._calculate_push_status(order_id=1)

        assert result == PushStatus.NOT_NEEDED, f"预期 NOT_NEEDED，实际 {result}"


@pytest.mark.asyncio
async def test_calculate_push_status_full():
    """测试全部已下推场景

    场景: 所有明细的 pushed_qty >= purchase_qty（且 purchase_qty > 0）
    预期: 返回 PushStatus.FULL
    """
    service = SalesOrderService()

    # 模拟订单明细全部已下推
    mock_items = [
        MagicMock(spec=SalesOrderItem, purchase_qty=10, pushed_qty=10),
        MagicMock(spec=SalesOrderItem, purchase_qty=5, pushed_qty=6),  # 超额下推
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_filter:
        mock_filter.return_value.all = AsyncMock(return_value=mock_items)

        result = await service._calculate_push_status(order_id=1)

        assert result == PushStatus.FULL, f"预期 FULL，实际 {result}"


@pytest.mark.asyncio
async def test_calculate_push_status_none():
    """测试全部未下推场景

    场景: 所有明细的 pushed_qty == 0（且 purchase_qty > 0）
    预期: 返回 PushStatus.NONE
    """
    service = SalesOrderService()

    # 模拟订单明细全部未下推
    mock_items = [
        MagicMock(spec=SalesOrderItem, purchase_qty=10, pushed_qty=0),
        MagicMock(spec=SalesOrderItem, purchase_qty=5, pushed_qty=0),
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_filter:
        mock_filter.return_value.all = AsyncMock(return_value=mock_items)

        result = await service._calculate_push_status(order_id=1)

        assert result == PushStatus.NONE, f"预期 NONE，实际 {result}"


@pytest.mark.asyncio
async def test_calculate_push_status_partial():
    """测试部分下推场景

    场景: 部分明细已下推，部分未下推
    预期: 返回 PushStatus.PARTIAL
    """
    service = SalesOrderService()

    # 模拟部分明细已下推，部分未下推
    mock_items = [
        MagicMock(spec=SalesOrderItem, purchase_qty=10, pushed_qty=10),  # 已下推
        MagicMock(spec=SalesOrderItem, purchase_qty=5, pushed_qty=0),    # 未下推
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_filter:
        mock_filter.return_value.all = AsyncMock(return_value=mock_items)

        result = await service._calculate_push_status(order_id=1)

        assert result == PushStatus.PARTIAL, f"预期 PARTIAL，实际 {result}"


@pytest.mark.asyncio
async def test_calculate_push_status_partial_within_item():
    """测试单行部分下推场景

    场景: 单个明细的 pushed_qty < purchase_qty
    预期: 返回 PushStatus.NONE（因为还有待下推数量）
    """
    service = SalesOrderService()

    # 模拟单行部分下推
    mock_items = [
        MagicMock(spec=SalesOrderItem, purchase_qty=10, pushed_qty=5),  # 部分下推
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_filter:
        mock_filter.return_value.all = AsyncMock(return_value=mock_items)

        result = await service._calculate_push_status(order_id=1)

        assert result == PushStatus.NONE, f"预期 NONE（有待下推），实际 {result}"


# ============ Task 3.2: 测试发货状态计算逻辑 ============

@pytest.mark.asyncio
async def test_calculate_delivery_status_no_warehouse_items():
    """测试无仓库发货明细场景

    场景: 订单没有仓库发货方式的明细（全部为直运）
    预期: 返回 DeliveryStatus.NONE
    """
    service = SalesOrderService()

    # 模拟没有仓库发货明细
    with patch.object(SalesOrderItem, 'filter') as mock_filter:
        mock_filter.return_value.all = AsyncMock(return_value=[])

        result = await service._calculate_delivery_status(order_id=1)

        assert result == DeliveryStatus.NONE, f"预期 NONE，实际 {result}"


@pytest.mark.asyncio
async def test_calculate_delivery_status_full():
    """测试全部已出库场景

    场景: 所有仓库发货明细的待出库单 out_qty >= qty
    预期: 返回 DeliveryStatus.FULL
    """
    service = SalesOrderService()

    # 模拟仓库发货明细
    mock_items = [
        MagicMock(spec=SalesOrderItem, id=1, qty=10),
        MagicMock(spec=SalesOrderItem, id=2, qty=5),
    ]

    # 模拟待出库单已全部出库
    mock_pendings = [
        MagicMock(spec=PendingOutboundOrder, sales_order_item_id=1, out_qty=10),
        MagicMock(spec=PendingOutboundOrder, sales_order_item_id=2, out_qty=5),
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_item_filter, \
         patch.object(PendingOutboundOrder, 'filter') as mock_pending_filter:

        mock_item_filter.return_value.all = AsyncMock(return_value=mock_items)
        mock_pending_filter.return_value.all = AsyncMock(return_value=mock_pendings)

        result = await service._calculate_delivery_status(order_id=1)

        assert result == DeliveryStatus.FULL, f"预期 FULL，实际 {result}"


@pytest.mark.asyncio
async def test_calculate_delivery_status_partial():
    """测试部分出库场景

    场景: 部分明细已出库，部分未出库
    预期: 返回 DeliveryStatus.PARTIAL
    """
    service = SalesOrderService()

    # 模拟仓库发货明细
    mock_items = [
        MagicMock(spec=SalesOrderItem, id=1, qty=10),
        MagicMock(spec=SalesOrderItem, id=2, qty=5),
    ]

    # 模拟部分出库
    mock_pendings = [
        MagicMock(spec=PendingOutboundOrder, sales_order_item_id=1, out_qty=10),  # 已出库
        MagicMock(spec=PendingOutboundOrder, sales_order_item_id=2, out_qty=0),   # 未出库
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_item_filter, \
         patch.object(PendingOutboundOrder, 'filter') as mock_pending_filter:

        mock_item_filter.return_value.all = AsyncMock(return_value=mock_items)
        mock_pending_filter.return_value.all = AsyncMock(return_value=mock_pendings)

        result = await service._calculate_delivery_status(order_id=1)

        assert result == DeliveryStatus.PARTIAL, f"预期 PARTIAL，实际 {result}"


@pytest.mark.asyncio
async def test_calculate_delivery_status_none():
    """测试全部未出库场景

    场景: 所有仓库发货明细的待出库单 out_qty == 0
    预期: 返回 DeliveryStatus.NONE
    """
    service = SalesOrderService()

    # 模拟仓库发货明细
    mock_items = [
        MagicMock(spec=SalesOrderItem, id=1, qty=10),
        MagicMock(spec=SalesOrderItem, id=2, qty=5),
    ]

    # 模拟全部未出库
    mock_pendings = [
        MagicMock(spec=PendingOutboundOrder, sales_order_item_id=1, out_qty=0),
        MagicMock(spec=PendingOutboundOrder, sales_order_item_id=2, out_qty=0),
    ]

    with patch.object(SalesOrderItem, 'filter') as mock_item_filter, \
         patch.object(PendingOutboundOrder, 'filter') as mock_pending_filter:

        mock_item_filter.return_value.all = AsyncMock(return_value=mock_items)
        mock_pending_filter.return_value.all = AsyncMock(return_value=mock_pendings)

        result = await service._calculate_delivery_status(order_id=1)

        assert result == DeliveryStatus.NONE, f"预期 NONE，实际 {result}"


# ============ Task 3.3: 测试选择性更新功能 ============

@pytest.mark.asyncio
async def test_update_order_status_selective_push():
    """测试只更新下推状态

    场景: 调用 update_order_status(order_id, status_types=["push"])
    预期: 只更新 push_status，未查询发货相关数据
    """
    service = SalesOrderService()

    # 模拟订单
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = None
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.save = AsyncMock()

    with patch.object(SalesOrder, 'filter') as mock_order_filter, \
         patch.object(service, '_update_push_status') as mock_update_push:

        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)
        mock_update_push.return_value = {"old": None, "new": "none", "changed": True}

        result = await service.update_order_status(order_id=1, status_types=["push"])

        assert "push" in result["updated"], "应包含 push 状态更新结果"
        assert "delivery" not in result["updated"], "不应包含 delivery 状态更新结果"
        mock_update_push.assert_called_once()


@pytest.mark.asyncio
async def test_update_order_status_selective_delivery():
    """测试只更新发货状态

    场景: 调用 update_order_status(order_id, status_types=["delivery"])
    预期: 只更新 delivery_status
    """
    service = SalesOrderService()

    # 模拟订单
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = None
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.save = AsyncMock()

    with patch.object(SalesOrder, 'filter') as mock_order_filter, \
         patch.object(service, '_update_delivery_status') as mock_update_delivery:

        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)
        mock_update_delivery.return_value = {"old": "none", "new": "full", "changed": True}

        result = await service.update_order_status(order_id=1, status_types=["delivery"])

        assert "delivery" in result["updated"], "应包含 delivery 状态更新结果"
        assert "push" not in result["updated"], "不应包含 push 状态更新结果"
        mock_update_delivery.assert_called_once()


@pytest.mark.asyncio
async def test_update_order_status_all():
    """测试更新全部状态

    场景: 调用 update_order_status(order_id) 不指定 status_types
    预期: 同时更新 push_status 和 delivery_status
    """
    service = SalesOrderService()

    # 模拟订单
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = None
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.save = AsyncMock()

    with patch.object(SalesOrder, 'filter') as mock_order_filter, \
         patch.object(service, '_update_push_status') as mock_update_push, \
         patch.object(service, '_update_delivery_status') as mock_update_delivery:

        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)
        mock_update_push.return_value = {"old": None, "new": "none", "changed": True}
        mock_update_delivery.return_value = {"old": "none", "new": "none", "changed": False}

        result = await service.update_order_status(order_id=1)

        assert "push" in result["updated"], "应包含 push 状态更新结果"
        assert "delivery" in result["updated"], "应包含 delivery 状态更新结果"
        mock_update_push.assert_called_once()
        mock_update_delivery.assert_called_once()


# ============ Task 3.4: 测试状态变更记录 ============

@pytest.mark.asyncio
async def test_status_flow_recorded_on_change():
    """测试状态变更时记录到 OrderStatusFlow

    场景: 状态实际从 NONE 变更为 FULL
    预期: OrderStatusFlow 中有对应记录
    """
    service = SalesOrderService()

    # 模拟订单（状态将变更）
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = PushStatus.NONE
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.save = AsyncMock()

    # 模拟计算返回新状态
    with patch.object(SalesOrder, 'filter') as mock_order_filter, \
         patch.object(service, '_calculate_push_status') as mock_calc, \
         patch.object(OrderStatusFlow, 'create') as mock_flow_create:

        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)
        mock_calc.return_value = PushStatus.FULL
        mock_flow_create.return_value = MagicMock()

        result = await service._update_push_status(mock_order, "test_user")

        assert result["changed"] is True, "状态应已变更"
        assert result["old"] == "none"
        assert result["new"] == "full"
        mock_flow_create.assert_called_once()

        # 验证记录参数
        call_kwargs = mock_flow_create.call_args[1]
        assert call_kwargs["order_no"] == "SO20250520001"
        assert call_kwargs["field"] == "push_status"
        assert call_kwargs["old_value"] == "none"
        assert call_kwargs["new_value"] == "full"
        assert call_kwargs["operator"] == "test_user"


@pytest.mark.asyncio
async def test_status_flow_not_recorded_on_same():
    """测试状态未变更时不记录

    场景: 状态保持不变
    预期: OrderStatusFlow 中没有新增记录
    """
    service = SalesOrderService()

    # 模拟订单（状态不变）
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = PushStatus.FULL
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.save = AsyncMock()

    # 模拟计算返回相同状态
    with patch.object(SalesOrder, 'filter') as mock_order_filter, \
         patch.object(service, '_calculate_push_status') as mock_calc, \
         patch.object(OrderStatusFlow, 'create') as mock_flow_create:

        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)
        mock_calc.return_value = PushStatus.FULL  # 状态不变
        mock_flow_create.return_value = MagicMock()

        result = await service._update_push_status(mock_order, "test_user")

        assert result["changed"] is False, "状态应未变更"
        mock_flow_create.assert_not_called()


# ============ Task 3.5: 测试预留状态接口 ============

@pytest.mark.asyncio
async def test_reserved_status_returns_skipped():
    """测试预留状态返回跳过信息

    场景: 调用 update_order_status(order_id, status_types=["receive"])
    预期: 返回 skipped 状态
    """
    service = SalesOrderService()

    # 模拟订单
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = None
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.receive_status = ReceiveStatus.NONE
    mock_order.invoice_status = InvoiceStatus.NONE
    mock_order.finance_status = FinanceStatus.UNPAID
    mock_order.save = AsyncMock()

    with patch.object(SalesOrder, 'filter') as mock_order_filter:
        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)

        result = await service.update_order_status(order_id=1, status_types=["receive"])

        assert "receive" in result["updated"], "应包含 receive 状态结果"
        assert result["updated"]["receive"]["status"] == "skipped"
        assert "暂不支持" in result["updated"]["receive"]["reason"]


@pytest.mark.asyncio
async def test_reserved_status_not_changed():
    """测试预留状态保持原值

    场景: 调用 update_order_status(order_id) 更新全部状态
    预期: receive_status、invoice_status、finance_status 保持原值
    """
    service = SalesOrderService()

    # 模拟订单
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = None
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.receive_status = ReceiveStatus.FULL  # 预设值
    mock_order.invoice_status = InvoiceStatus.PARTIAL  # 预设值
    mock_order.finance_status = FinanceStatus.PAID  # 预设值
    mock_order.save = AsyncMock()

    with patch.object(SalesOrder, 'filter') as mock_order_filter, \
         patch.object(service, '_update_push_status') as mock_update_push, \
         patch.object(service, '_update_delivery_status') as mock_update_delivery:

        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)
        mock_update_push.return_value = {"old": None, "new": "none", "changed": True}
        mock_update_delivery.return_value = {"old": "none", "new": "none", "changed": False}

        await service.update_order_status(order_id=1)

        # 验证预留状态未被修改
        assert mock_order.receive_status == ReceiveStatus.FULL
        assert mock_order.invoice_status == InvoiceStatus.PARTIAL
        assert mock_order.finance_status == FinanceStatus.PAID


@pytest.mark.asyncio
async def test_update_order_status_order_not_found():
    """测试订单不存在时的异常处理

    场景: 传入不存在的订单ID
    预期: 抛出 ValueError
    """
    service = SalesOrderService()

    with patch.object(SalesOrder, 'filter') as mock_order_filter:
        mock_order_filter.return_value.first = AsyncMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            await service.update_order_status(order_id=999)

        assert "订单不存在" in str(exc_info.value)


# ============ 辅助测试 ============

@pytest.mark.asyncio
async def test_multiple_status_types():
    """测试同时更新多个状态类型

    场景: 同时指定 push 和 delivery
    预期: 两个状态都被更新
    """
    service = SalesOrderService()

    # 模拟订单
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.push_status = None
    mock_order.delivery_status = DeliveryStatus.NONE
    mock_order.save = AsyncMock()

    with patch.object(SalesOrder, 'filter') as mock_order_filter, \
         patch.object(service, '_update_push_status') as mock_update_push, \
         patch.object(service, '_update_delivery_status') as mock_update_delivery:

        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)
        mock_update_push.return_value = {"old": None, "new": "none", "changed": True}
        mock_update_delivery.return_value = {"old": "none", "new": "partial", "changed": True}

        result = await service.update_order_status(
            order_id=1,
            status_types=["push", "delivery"]
        )

        assert "push" in result["updated"]
        assert "delivery" in result["updated"]
        mock_update_push.assert_called_once()
        mock_update_delivery.assert_called_once()


@pytest.mark.asyncio
async def test_unknown_status_type():
    """测试未知状态类型处理

    场景: 传入未知的状态类型
    预期: 跳过处理，不报错
    """
    service = SalesOrderService()

    # 模拟订单
    mock_order = MagicMock(spec=SalesOrder)
    mock_order.id = 1
    mock_order.order_no = "SO20250520001"
    mock_order.save = AsyncMock()

    with patch.object(SalesOrder, 'filter') as mock_order_filter:
        mock_order_filter.return_value.first = AsyncMock(return_value=mock_order)

        result = await service.update_order_status(
            order_id=1,
            status_types=["unknown_type"]
        )

        # 未知类型不应出现在结果中
        assert "unknown_type" not in result["updated"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
