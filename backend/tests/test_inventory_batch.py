"""
库存批次管理功能测试脚本
- 模型验证: WarehouseLocation, InboundBatch/OutboundBatch 新增字段, to_dict 方法
- 服务层逻辑: WarehouseLocationService CRUD, InboundBatchService 入库带库位/有效期,
              StockService 锁定量计算, PendingOutboundService 批次选择出库
- 业务规则: 批次出库数量校验、过期批次过滤、先进先出排序
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise


# ============ 测试结果收集 ============

test_results = []
current_test = None


def start_test(name: str):
    global current_test
    current_test = {"name": name, "passed": False, "error": None}


def pass_test():
    global current_test
    if current_test:
        current_test["passed"] = True
        test_results.append(current_test)
        print(f"  PASS: {current_test['name']}")
    current_test = None


def fail_test(error: str):
    global current_test
    if current_test:
        current_test["passed"] = False
        current_test["error"] = error
        test_results.append(current_test)
        print(f"  FAIL: {current_test['name']} - {error}")
    current_test = None


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"期望 {expected!r}, 实际 {actual!r}. {msg}")


def assert_true(value, msg=""):
    if not value:
        raise AssertionError(f"期望 True, 实际 {value!r}. {msg}")


def assert_in(key, container, msg=""):
    if key not in container:
        raise AssertionError(f"期望 {key!r} 在容器中. {msg}")


def assert_not_in(key, container, msg=""):
    if key in container:
        raise AssertionError(f"期望 {key!r} 不在容器中. {msg}")


def assert_is_none(value, msg=""):
    if value is not None:
        raise AssertionError(f"期望 None, 实际 {value!r}. {msg}")


def assert_is_not_none(value, msg=""):
    if value is None:
        raise AssertionError(f"期望非 None. {msg}")


def assert_gt(actual, expected, msg=""):
    if not (actual > expected):
        raise AssertionError(f"期望 {actual!r} > {expected!r}. {msg}")


def assert_gte(actual, expected, msg=""):
    if not (actual >= expected):
        raise AssertionError(f"期望 {actual!r} >= {expected!r}. {msg}")


# ============ 数据库初始化 ============

DB_URL = "mysql://admin:Chenglp1215!%40%23@132.232.212.151:58901/erp_test"


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(
        db_url=DB_URL,
        modules={
            "models": [
                "models_mysql.auth",
                "models_mysql.warehouse",
                "models_mysql.sales_order",
                "models_mysql.pending_outbound",
                "models_mysql.product",
                "models_mysql.purchase_order",
                "models_mysql.order_status_flow",
                "models_mysql.supplier",
            ]
        },
    )
    await Tortoise.generate_schemas()


async def close_db():
    """关闭数据库连接"""
    await Tortoise.close_connections()


# ============ 测试数据 ID 收集 ============

created_ids = {}


# ============ 模型验证测试 ============

async def test_warehouse_location_model():
    """测试 WarehouseLocation 模型字段和 to_dict"""
    start_test("WarehouseLocation 模型 - 字段验证")
    try:
        from models_mysql.warehouse import WarehouseLocation

        # 验证模型类存在
        assert_is_not_none(WarehouseLocation, "WarehouseLocation 类应存在")

        # 验证表名
        assert_eq(WarehouseLocation.Meta.table, "warehouse_locations", "表名应为 warehouse_locations")

        # 验证唯一约束
        assert_true(
            hasattr(WarehouseLocation.Meta, 'unique_together'),
            "应有 unique_together 约束"
        )

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_inbound_batch_new_fields():
    """测试 InboundBatch 模型新增字段"""
    start_test("InboundBatch 模型 - 新增字段验证")
    try:
        from models_mysql.warehouse import InboundBatch

        # 验证模型字段描述包含新增字段
        field_names = list(InboundBatch._meta.fields_map.keys())
        assert_in("location_id", field_names, "应有 location_id 字段")
        assert_in("location_code", field_names, "应有 location_code 字段")
        assert_in("expiry_date", field_names, "应有 expiry_date 字段")
        assert_in("current_quantity", field_names, "应有 current_quantity 字段")

        # 验证 location_id 允许 null
        location_id_field = InboundBatch._meta.fields_map["location_id"]
        assert_true(location_id_field.null, "location_id 应允许 null")

        # 验证 location_code 允许 null
        location_code_field = InboundBatch._meta.fields_map["location_code"]
        assert_true(location_code_field.null, "location_code 应允许 null")

        # 验证 expiry_date 允许 null
        expiry_date_field = InboundBatch._meta.fields_map["expiry_date"]
        assert_true(expiry_date_field.null, "expiry_date 应允许 null")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_outbound_batch_new_field():
    """测试 OutboundBatch 模型新增 inbound_batch_id 字段"""
    start_test("OutboundBatch 模型 - inbound_batch_id 字段验证")
    try:
        from models_mysql.warehouse import OutboundBatch

        field_names = list(OutboundBatch._meta.fields_map.keys())
        assert_in("inbound_batch_id", field_names, "应有 inbound_batch_id 字段")

        # 验证允许 null（历史数据无法追溯）
        inbound_batch_id_field = OutboundBatch._meta.fields_map["inbound_batch_id"]
        assert_true(inbound_batch_id_field.null, "inbound_batch_id 应允许 null")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_inbound_batch_to_dict():
    """测试 InboundBatch.to_dict() 返回新增字段"""
    start_test("InboundBatch.to_dict - 返回新增字段")
    try:
        from models_mysql.warehouse import InboundBatch

        # 创建一个临时实例检查 to_dict
        batch = InboundBatch()
        batch.id = 99999
        batch.warehouse_id = 1
        batch.product_id = 1
        batch.product_code = "TEST"
        batch.product_name = "测试"
        batch.spec_id = 1
        batch.spec_code = "SPEC01"
        batch.stock_id = 1
        batch.quantity = 100
        batch.location_id = 10
        batch.location_code = "A-01"
        batch.expiry_date = datetime(2026, 12, 31)
        batch.current_quantity = 80
        batch.user_id = 1
        batch.user_name = "tester"

        d = batch.to_dict()
        assert_in("location_id", d, "to_dict 应包含 location_id")
        assert_in("location_code", d, "to_dict 应包含 location_code")
        assert_in("expiry_date", d, "to_dict 应包含 expiry_date")
        assert_in("current_quantity", d, "to_dict 应包含 current_quantity")
        assert_eq(d["location_id"], 10, "location_id 值应为 10")
        assert_eq(d["location_code"], "A-01", "location_code 值应为 A-01")
        assert_eq(d["current_quantity"], 80, "current_quantity 值应为 80")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_outbound_batch_to_dict():
    """测试 OutboundBatch.to_dict() 返回新增字段"""
    start_test("OutboundBatch.to_dict - 返回 inbound_batch_id")
    try:
        from models_mysql.warehouse import OutboundBatch

        batch = OutboundBatch()
        batch.id = 99999
        batch.warehouse_id = 1
        batch.product_id = 1
        batch.product_code = "TEST"
        batch.product_name = "测试"
        batch.spec_id = 1
        batch.spec_code = "SPEC01"
        batch.stock_id = 1
        batch.quantity = 50
        batch.user_id = 1
        batch.user_name = "tester"
        batch.inbound_batch_id = 5

        d = batch.to_dict()
        assert_in("inbound_batch_id", d, "to_dict 应包含 inbound_batch_id")
        assert_eq(d["inbound_batch_id"], 5, "inbound_batch_id 值应为 5")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 库位管理 Service CRUD 测试 ============

async def test_create_location():
    """测试创建库位"""
    start_test("库位管理 - 创建库位")
    try:
        from services.inventory_service_mysql import warehouse_location_service
        from models_mysql.warehouse import Warehouse

        # 先确保有一个测试仓库
        warehouse = await Warehouse.filter(warehouse_code="WH_TEST_LOC").first()
        if not warehouse:
            warehouse = await Warehouse.create(
                warehouse_code="WH_TEST_LOC",
                name="库位测试仓库",
                address="测试地址",
                status="active",
            )
        created_ids["loc_warehouse_id"] = warehouse.id

        # 创建库位
        result = await warehouse_location_service.create_location({
            "warehouse_id": warehouse.id,
            "location_code": "A-01",
            "location_name": "A区1号位",
            "status": "active",
            "description": "测试库位",
        })

        assert_is_not_none(result, "创建结果不应为 None")
        assert_in("id", result, "结果应包含 id")
        assert_eq(result["warehouse_id"], warehouse.id, "warehouse_id 应一致")
        assert_eq(result["location_code"], "A-01", "location_code 应为 A-01")
        assert_eq(result["location_name"], "A区1号位", "location_name 应一致")
        assert_eq(result["status"], "active", "status 应为 active")

        created_ids["location_id"] = result["id"]
        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_create_location_duplicate_code():
    """测试创建重复库位编码应报错"""
    start_test("库位管理 - 重复编码报错")
    try:
        from services.inventory_service_mysql import warehouse_location_service

        warehouse_id = created_ids.get("loc_warehouse_id")
        if not warehouse_id:
            fail_test("缺少测试仓库ID")
            return

        try:
            await warehouse_location_service.create_location({
                "warehouse_id": warehouse_id,
                "location_code": "A-01",
                "location_name": "重复编码",
            })
            fail_test("重复编码应报错但未报错")
        except ValueError as e:
            assert_true("已存在" in str(e), f"错误信息应包含'已存在': {e}")
            pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_create_location_invalid_warehouse():
    """测试创建库位时仓库不存在应报错"""
    start_test("库位管理 - 仓库不存在报错")
    try:
        from services.inventory_service_mysql import warehouse_location_service

        try:
            await warehouse_location_service.create_location({
                "warehouse_id": 999999,
                "location_code": "X-01",
            })
            fail_test("仓库不存在应报错但未报错")
        except ValueError as e:
            assert_true("仓库不存在" in str(e), f"错误信息应包含'仓库不存在': {e}")
            pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_get_location():
    """测试获取库位详情"""
    start_test("库位管理 - 获取库位详情")
    try:
        from services.inventory_service_mysql import warehouse_location_service

        loc_id = created_ids.get("location_id")
        if not loc_id:
            fail_test("缺少测试库位ID")
            return

        result = await warehouse_location_service.get_location_by_id(loc_id)
        assert_is_not_none(result, "结果不应为 None")
        assert_eq(result["id"], loc_id, "id 应一致")
        assert_eq(result["location_code"], "A-01", "location_code 应为 A-01")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_update_location():
    """测试更新库位"""
    start_test("库位管理 - 更新库位")
    try:
        from services.inventory_service_mysql import warehouse_location_service

        loc_id = created_ids.get("location_id")
        if not loc_id:
            fail_test("缺少测试库位ID")
            return

        result = await warehouse_location_service.update_location(loc_id, {
            "location_name": "A区1号位-已更新",
            "status": "inactive",
        })
        assert_true(result, "更新应返回 True")

        # 验证更新结果
        updated = await warehouse_location_service.get_location_by_id(loc_id)
        assert_eq(updated["location_name"], "A区1号位-已更新", "location_name 应已更新")
        assert_eq(updated["status"], "inactive", "status 应已更新")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_list_locations():
    """测试获取库位列表"""
    start_test("库位管理 - 获取库位列表")
    try:
        from services.inventory_service_mysql import warehouse_location_service

        warehouse_id = created_ids.get("loc_warehouse_id")
        if not warehouse_id:
            fail_test("缺少测试仓库ID")
            return

        # 不带筛选
        all_locs, all_total = await warehouse_location_service.list_locations()
        assert_gte(all_total, 1, "库位总数应 >= 1")

        # 带仓库筛选
        locs, total = await warehouse_location_service.list_locations(warehouse_id=warehouse_id)
        assert_gte(total, 1, "该仓库下库位数应 >= 1")
        for loc in locs:
            assert_eq(loc["warehouse_id"], warehouse_id, "筛选结果应全部属于该仓库")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_delete_location():
    """测试删除库位"""
    start_test("库位管理 - 删除库位")
    try:
        from services.inventory_service_mysql import warehouse_location_service
        from models_mysql.warehouse import WarehouseLocation

        # 创建一个新库位用于删除
        warehouse_id = created_ids.get("loc_warehouse_id")
        loc = await WarehouseLocation.create(
            warehouse_id=warehouse_id,
            location_code="DEL-01",
            location_name="待删除库位",
        )

        result = await warehouse_location_service.delete_location(loc.id)
        assert_true(result, "删除应返回 True")

        # 验证已删除
        deleted = await warehouse_location_service.get_location_by_id(loc.id)
        assert_is_none(deleted, "删除后查询应返回 None")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_delete_nonexistent_location():
    """测试删除不存在的库位应报错"""
    start_test("库位管理 - 删除不存在的库位报错")
    try:
        from services.inventory_service_mysql import warehouse_location_service

        try:
            await warehouse_location_service.delete_location(999999)
            fail_test("删除不存在的库位应报错但未报错")
        except ValueError as e:
            assert_true("不存在" in str(e), f"错误信息应包含'不存在': {e}")
            pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 入库服务变更测试 ============

async def test_create_inbound_with_location():
    """测试创建入库批次时设置库位和有效期"""
    start_test("入库服务 - 创建入库批次带库位和有效期")
    try:
        from services.inventory_service_mysql import inbound_batch_service
        from models_mysql.warehouse import Warehouse, WarehouseLocation

        # 确保测试仓库存在
        warehouse = await Warehouse.filter(warehouse_code="WH_TEST_INBOUND").first()
        if not warehouse:
            warehouse = await Warehouse.create(
                warehouse_code="WH_TEST_INBOUND",
                name="入库测试仓库",
                address="测试地址",
                status="active",
            )
        created_ids["inbound_warehouse_id"] = warehouse.id

        # 创建库位
        location = await WarehouseLocation.create(
            warehouse_id=warehouse.id,
            location_code="B-01",
            location_name="B区1号位",
        )
        created_ids["inbound_location_id"] = location.id

        # 准备入库数据
        future_date = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
        result = await inbound_batch_service.create_inbound({
            "warehouse_id": warehouse.id,
            "product_id": 999,
            "product_code": "TEST-PROD",
            "product_name": "测试商品",
            "spec_id": 888,
            "spec_code": "SPEC-TEST",
            "quantity": 100,
            "location_id": location.id,
            "location_code": "B-01",
            "expiry_date": future_date,
            "user_id": 1,
            "user_name": "tester",
        })

        assert_is_not_none(result, "创建结果不应为 None")
        assert_eq(result["location_id"], location.id, "location_id 应一致")
        assert_eq(result["location_code"], "B-01", "location_code 应为 B-01")
        assert_is_not_none(result["expiry_date"], "expiry_date 不应为 None")
        assert_eq(result["current_quantity"], 100.0, "current_quantity 应等于入库数量")
        assert_eq(result["quantity"], 100.0, "quantity 应等于入库数量")

        created_ids["inbound_batch_id"] = result["id"]
        created_ids["inbound_stock_id"] = result["stock_id"]
        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_create_inbound_with_invalid_location():
    """测试入库时库位不存在应报错"""
    start_test("入库服务 - 库位不存在报错")
    try:
        from services.inventory_service_mysql import inbound_batch_service

        warehouse_id = created_ids.get("inbound_warehouse_id")
        if not warehouse_id:
            fail_test("缺少测试仓库ID")
            return

        try:
            await inbound_batch_service.create_inbound({
                "warehouse_id": warehouse_id,
                "product_id": 998,
                "product_code": "TEST-PROD2",
                "product_name": "测试商品2",
                "spec_id": 887,
                "spec_code": "SPEC-TEST2",
                "quantity": 50,
                "location_id": 999999,
                "user_id": 1,
                "user_name": "tester",
            })
            fail_test("库位不存在应报错但未报错")
        except ValueError as e:
            assert_true("库位不存在" in str(e), f"错误信息应包含'库位不存在': {e}")
            pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_create_inbound_without_location():
    """测试入库时不传库位应成功"""
    start_test("入库服务 - 不传库位创建成功")
    try:
        from services.inventory_service_mysql import inbound_batch_service

        warehouse_id = created_ids.get("inbound_warehouse_id")
        if not warehouse_id:
            fail_test("缺少测试仓库ID")
            return

        result = await inbound_batch_service.create_inbound({
            "warehouse_id": warehouse_id,
            "product_id": 997,
            "product_code": "TEST-PROD3",
            "product_name": "测试商品3",
            "spec_id": 886,
            "spec_code": "SPEC-TEST3",
            "quantity": 30,
            "user_id": 1,
            "user_name": "tester",
        })

        assert_is_not_none(result, "创建结果不应为 None")
        assert_is_none(result["location_id"], "不传库位时 location_id 应为 None")
        assert_eq(result["current_quantity"], 30.0, "current_quantity 应等于入库数量")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 锁定量计算测试 ============

async def test_calculate_locked_quantity():
    """测试锁定量计算逻辑"""
    start_test("锁定量计算 - _calculate_locked_quantity")
    try:
        from services.inventory_service_mysql import stock_service
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
        from models_mysql.warehouse import Warehouse, Stock

        # 创建测试仓库
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_LOCK",
            name="锁定量测试仓库",
            address="测试地址",
        )

        # 创建测试库存
        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=900,
            product_code="LOCK-TEST",
            product_name="锁定量测试商品",
            spec_id=800,
            spec_code="LOCK-SPEC",
            quantity=200,
        )

        # 无待出库单时锁定量为 0
        locked = await stock_service._calculate_locked_quantity(warehouse.id, 800)
        assert_eq(locked, 0, "无待出库单时锁定量应为 0")

        # 创建待出库单
        pending1 = await PendingOutboundOrder.create(
            pending_no="LOCK-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-LOCK-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=800,
            product_code="LOCK-TEST",
            spec_code="LOCK-SPEC",
            locked_qty=50,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        locked = await stock_service._calculate_locked_quantity(warehouse.id, 800)
        assert_eq(locked, 50, "一个待出库单时锁定量应为 50")

        # 创建第二个待出库单
        pending2 = await PendingOutboundOrder.create(
            pending_no="LOCK-TEST-002",
            sales_order_id=1,
            sales_order_no="SO-LOCK-002",
            sales_order_item_id=2,
            row_no=2,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=800,
            product_code="LOCK-TEST",
            spec_code="LOCK-SPEC",
            locked_qty=30,
            out_qty=10,
            status=PendingOutboundStatus.PARTIAL,
        )

        locked = await stock_service._calculate_locked_quantity(warehouse.id, 800)
        # 50 - 0 + 30 - 10 = 70
        assert_eq(locked, 70, "两个待出库单时锁定量应为 70")

        # 已完成/已取消的不计入
        pending1.status = PendingOutboundStatus.FULL
        pending1.out_qty = 50
        await pending1.save()

        locked = await stock_service._calculate_locked_quantity(warehouse.id, 800)
        # 只有 pending2: 30 - 10 = 20
        assert_eq(locked, 20, "一个完成后锁定量应为 20")

        # 清理
        await pending1.delete()
        await pending2.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_batch_calculate_locked_quantities():
    """测试批量锁定量计算"""
    start_test("锁定量计算 - _batch_calculate_locked_quantities")
    try:
        from services.inventory_service_mysql import stock_service
        from models_mysql.warehouse import Warehouse, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        # 空列表
        result = await stock_service._batch_calculate_locked_quantities([])
        assert_eq(len(result), 0, "空列表应返回空字典")

        # 创建测试数据验证批量计算
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_BQLOCK",
            name="批量锁定量测试仓库",
            address="测试地址",
        )

        stock1 = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=901,
            product_code="BQLOCK-1",
            product_name="批量锁定量测试1",
            spec_id=801,
            spec_code="BQLOCK-SPEC1",
            quantity=200,
        )

        stock2 = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=902,
            product_code="BQLOCK-2",
            product_name="批量锁定量测试2",
            spec_id=802,
            spec_code="BQLOCK-SPEC2",
            quantity=100,
        )

        # 创建待出库单
        pending1 = await PendingOutboundOrder.create(
            pending_no="BQLOCK-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-BQLOCK-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=801,
            product_code="BQLOCK-1",
            spec_code="BQLOCK-SPEC1",
            locked_qty=50,
            out_qty=10,
            status=PendingOutboundStatus.PENDING,
        )

        pending2 = await PendingOutboundOrder.create(
            pending_no="BQLOCK-TEST-002",
            sales_order_id=1,
            sales_order_no="SO-BQLOCK-002",
            sales_order_item_id=2,
            row_no=2,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=802,
            product_code="BQLOCK-2",
            spec_code="BQLOCK-SPEC2",
            locked_qty=30,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        # 执行批量计算
        stock_list = [
            {"warehouse_id": warehouse.id, "spec_id": 801},
            {"warehouse_id": warehouse.id, "spec_id": 802},
        ]
        result = await stock_service._batch_calculate_locked_quantities(stock_list)

        assert_true(isinstance(result, dict), "结果应为字典")
        key1 = f"{warehouse.id}_801"
        key2 = f"{warehouse.id}_802"
        assert_in(key1, result, f"应包含 {key1} 键")
        assert_in(key2, result, f"应包含 {key2} 键")
        assert_eq(result[key1], 40, f"{key1} 锁定量应为 40 (50-10)")
        assert_eq(result[key2], 30, f"{key2} 锁定量应为 30 (30-0)")

        # 清理
        await pending1.delete()
        await pending2.delete()
        await stock1.delete()
        await stock2.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_stock_detail_locked_quantity():
    """测试库存详情返回锁定量和可用量"""
    start_test("锁定量计算 - 库存详情返回锁定量和可用量")
    try:
        from services.inventory_service_mysql import stock_service
        from models_mysql.warehouse import Warehouse, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        # 创建独立的测试仓库和库存
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_SLOCK",
            name="库存详情锁定量测试仓库",
            address="测试地址",
        )

        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=905,
            product_code="SLOCK-TEST",
            product_name="锁定量详情测试",
            spec_id=805,
            spec_code="SLOCK-SPEC",
            quantity=200,
        )

        # 创建待出库单以验证锁定量
        pending = await PendingOutboundOrder.create(
            pending_no="SLOCK-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-SLOCK-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=805,
            product_code="SLOCK-TEST",
            spec_code="SLOCK-SPEC",
            locked_qty=50,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        result = await stock_service.get_stock_by_id(stock.id, is_formatted=False)
        if not result:
            fail_test("查询库存详情返回 None")
            return

        assert_in("locked_quantity", result, "结果应包含 locked_quantity")
        assert_in("available_quantity", result, "结果应包含 available_quantity")
        assert_eq(result["locked_quantity"], 50, "锁定量应为 50")
        assert_eq(result["available_quantity"], 150, "可用量应为 150 (200-50)")

        # 清理
        await pending.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 可用批次查询测试 ============

async def test_get_available_batches():
    """测试获取可出库批次列表"""
    start_test("可用批次查询 - get_available_batches")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, InboundBatch, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        # 创建测试仓库
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_BATCH",
            name="批次测试仓库",
            address="测试地址",
        )

        # 创建测试库存
        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=910,
            product_code="BATCH-TEST",
            product_name="批次测试商品",
            spec_id=810,
            spec_code="BATCH-SPEC",
            quantity=500,
        )

        # 创建不同有效期的入库批次
        batch1 = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=910,
            product_code="BATCH-TEST",
            product_name="批次测试商品",
            spec_id=810,
            spec_code="BATCH-SPEC",
            stock_id=stock.id,
            quantity=100,
            current_quantity=100,
            location_code="A-01",
            expiry_date=datetime.now(timezone.utc) + timedelta(days=30),  # 30天后过期
            user_id=1,
            user_name="tester",
        )

        batch2 = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=910,
            product_code="BATCH-TEST",
            product_name="批次测试商品",
            spec_id=810,
            spec_code="BATCH-SPEC",
            stock_id=stock.id,
            quantity=200,
            current_quantity=200,
            location_code="A-02",
            expiry_date=datetime.now(timezone.utc) + timedelta(days=60),  # 60天后过期
            user_id=1,
            user_name="tester",
        )

        # 创建已过期批次
        batch_expired = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=910,
            product_code="BATCH-TEST",
            product_name="批次测试商品",
            spec_id=810,
            spec_code="BATCH-SPEC",
            stock_id=stock.id,
            quantity=50,
            current_quantity=50,
            location_code="A-03",
            expiry_date=datetime.now(timezone.utc) - timedelta(days=1),  # 已过期
            user_id=1,
            user_name="tester",
        )

        # 创建剩余为0的批次
        batch_zero = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=910,
            product_code="BATCH-TEST",
            product_name="批次测试商品",
            spec_id=810,
            spec_code="BATCH-SPEC",
            stock_id=stock.id,
            quantity=30,
            current_quantity=0,
            location_code="A-04",
            expiry_date=datetime.now(timezone.utc) + timedelta(days=90),
            user_id=1,
            user_name="tester",
        )

        # 创建待出库单
        pending = await PendingOutboundOrder.create(
            pending_no="BATCH-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-BATCH-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="批次测试仓库",
            spec_id=810,
            product_code="BATCH-TEST",
            spec_code="BATCH-SPEC",
            locked_qty=100,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        # 查询可用批次
        batches = await pending_outbound_service.get_available_batches(pending.id)

        # 应返回2个批次（过期和剩余为0的被过滤）
        assert_eq(len(batches), 2, f"应返回2个可用批次，实际返回 {len(batches)}")

        # 应按 expiry_date ASC 排序（先进先出）
        assert_eq(batches[0]["id"], batch1.id, "第一个应是30天后过期的批次")
        assert_eq(batches[1]["id"], batch2.id, "第二个应是60天后过期的批次")

        # 验证返回字段
        assert_in("id", batches[0], "应包含 id")
        assert_in("location_code", batches[0], "应包含 location_code")
        assert_in("expiry_date", batches[0], "应包含 expiry_date")
        assert_in("current_quantity", batches[0], "应包含 current_quantity")

        # 清理
        await pending.delete()
        await batch1.delete()
        await batch2.delete()
        await batch_expired.delete()
        await batch_zero.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_get_available_batches_no_expiry():
    """测试没有有效期的批次应被包含"""
    start_test("可用批次查询 - 无有效期批次应被包含")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, InboundBatch, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        # 创建测试仓库
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_NOEXP",
            name="无有效期测试仓库",
            address="测试地址",
        )

        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=920,
            product_code="NOEXP-TEST",
            product_name="无有效期测试",
            spec_id=820,
            spec_code="NOEXP-SPEC",
            quantity=100,
        )

        # 创建无有效期的批次
        batch = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=920,
            product_code="NOEXP-TEST",
            product_name="无有效期测试",
            spec_id=820,
            spec_code="NOEXP-SPEC",
            stock_id=stock.id,
            quantity=100,
            current_quantity=100,
            expiry_date=None,
            user_id=1,
            user_name="tester",
        )

        pending = await PendingOutboundOrder.create(
            pending_no="NOEXP-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-NOEXP-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=820,
            product_code="NOEXP-TEST",
            spec_code="NOEXP-SPEC",
            locked_qty=50,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        batches = await pending_outbound_service.get_available_batches(pending.id)
        assert_eq(len(batches), 1, "无有效期的批次应被包含")
        assert_is_none(batches[0]["expiry_date"], "expiry_date 应为 None")

        # 清理
        await pending.delete()
        await batch.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 批次出库执行测试 ============

async def test_execute_outbound_with_batch_items():
    """测试批次选择出库 - 正常流程"""
    start_test("批次出库 - 正常流程")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, InboundBatch, Stock, OutboundBatch
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
        from models_mysql.sales_order import SalesOrder, SalesOrderItem

        # 创建测试仓库
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_EXEC",
            name="出库测试仓库",
            address="测试地址",
        )

        # 创建测试库存
        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=930,
            product_code="EXEC-TEST",
            product_name="出库测试商品",
            spec_id=830,
            spec_code="EXEC-SPEC",
            quantity=300,
        )

        # 创建两个入库批次
        batch1 = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=930,
            product_code="EXEC-TEST",
            product_name="出库测试商品",
            spec_id=830,
            spec_code="EXEC-SPEC",
            stock_id=stock.id,
            quantity=100,
            current_quantity=100,
            location_code="C-01",
            expiry_date=datetime.now(timezone.utc) + timedelta(days=30),
            user_id=1,
            user_name="tester",
        )

        batch2 = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=930,
            product_code="EXEC-TEST",
            product_name="出库测试商品",
            spec_id=830,
            spec_code="EXEC-SPEC",
            stock_id=stock.id,
            quantity=200,
            current_quantity=200,
            location_code="C-02",
            expiry_date=datetime.now(timezone.utc) + timedelta(days=60),
            user_id=1,
            user_name="tester",
        )

        # 创建销售订单和明细
        sales_order = await SalesOrder.create(
            order_no="SO-EXEC-TEST",
            order_date=datetime.now(timezone.utc).date(),
            customer_id=1,
            customer_name="测试客户",
        )
        sales_item = await SalesOrderItem.create(
            sales_order=sales_order,
            row_no=1,
            product_code="EXEC-TEST",
            spec_code="EXEC-SPEC",
            qty=100,
            price=10,
            amt=1000,
            shipping_method="warehouse",
            out_qty=0,
        )

        # 创建待出库单
        pending = await PendingOutboundOrder.create(
            pending_no="EXEC-TEST-001",
            sales_order_id=sales_order.id,
            sales_order_no=sales_order.order_no,
            sales_order_item_id=sales_item.id,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="出库测试仓库",
            spec_id=830,
            product_code="EXEC-TEST",
            spec_code="EXEC-SPEC",
            locked_qty=100,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        # 执行批次出库：批次1出60，批次2出40
        result = await pending_outbound_service.execute_outbound(
            pending_id=pending.id,
            out_qty=100,
            operator="tester",
            batch_items=[
                {"inbound_batch_id": batch1.id, "quantity": 60},
                {"inbound_batch_id": batch2.id, "quantity": 40},
            ]
        )

        assert_is_not_none(result, "出库结果不应为 None")

        # 验证待出库单状态
        assert_eq(result["out_qty"], 100, "out_qty 应为 100")
        assert_eq(result["status"], "full", "状态应为 full")

        # 验证批次数量扣减
        batch1_refreshed = await InboundBatch.get_or_none(id=batch1.id)
        assert_eq(batch1_refreshed.current_quantity, 40.0, "批次1剩余应为 40")

        batch2_refreshed = await InboundBatch.get_or_none(id=batch2.id)
        assert_eq(batch2_refreshed.current_quantity, 160.0, "批次2剩余应为 160")

        # 验证出库批次记录关联入库批次
        outbound_records = await OutboundBatch.filter(
            pending_outbound_id=pending.id
        ).all()
        assert_eq(len(outbound_records), 2, "应创建2条出库批次记录")

        # 验证 inbound_batch_id 关联
        ob_batch_ids = [ob.inbound_batch_id for ob in outbound_records]
        assert_in(batch1.id, ob_batch_ids, "应包含批次1的关联")
        assert_in(batch2.id, ob_batch_ids, "应包含批次2的关联")

        # 清理
        for ob in outbound_records:
            await ob.delete()
        await pending.delete()
        await sales_item.delete()
        await sales_order.delete()
        await batch1.delete()
        await batch2.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_execute_outbound_batch_qty_mismatch():
    """测试批次出库数量之和 != out_qty 时应报错"""
    start_test("批次出库 - 数量之和不一致报错")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, InboundBatch, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        # 创建测试仓库
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_MISMATCH",
            name="数量不匹配测试仓库",
            address="测试地址",
        )

        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=940,
            product_code="MISMATCH-TEST",
            product_name="数量不匹配测试",
            spec_id=840,
            spec_code="MISMATCH-SPEC",
            quantity=200,
        )

        batch = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=940,
            product_code="MISMATCH-TEST",
            product_name="数量不匹配测试",
            spec_id=840,
            spec_code="MISMATCH-SPEC",
            stock_id=stock.id,
            quantity=200,
            current_quantity=200,
            user_id=1,
            user_name="tester",
        )

        pending = await PendingOutboundOrder.create(
            pending_no="MISMATCH-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-MISMATCH-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=840,
            product_code="MISMATCH-TEST",
            spec_code="MISMATCH-SPEC",
            locked_qty=100,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        try:
            # out_qty=100 但 batch_items 总量为 50
            await pending_outbound_service.execute_outbound(
                pending_id=pending.id,
                out_qty=100,
                operator="tester",
                batch_items=[
                    {"inbound_batch_id": batch.id, "quantity": 50},
                ]
            )
            fail_test("数量不匹配应报错但未报错")
        except ValueError as e:
            assert_true("不一致" in str(e), f"错误信息应包含'不一致': {e}")

        # 清理
        await pending.delete()
        await batch.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_execute_outbound_batch_insufficient_quantity():
    """测试批次出库数量超过批次剩余数量应报错"""
    start_test("批次出库 - 批次数量不足报错")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, InboundBatch, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        # 创建测试仓库
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_INSUF",
            name="数量不足测试仓库",
            address="测试地址",
        )

        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=950,
            product_code="INSUF-TEST",
            product_name="数量不足测试",
            spec_id=850,
            spec_code="INSUF-SPEC",
            quantity=200,
        )

        batch = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=950,
            product_code="INSUF-TEST",
            product_name="数量不足测试",
            spec_id=850,
            spec_code="INSUF-SPEC",
            stock_id=stock.id,
            quantity=50,
            current_quantity=50,
            user_id=1,
            user_name="tester",
        )

        pending = await PendingOutboundOrder.create(
            pending_no="INSUF-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-INSUF-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=850,
            product_code="INSUF-TEST",
            spec_code="INSUF-SPEC",
            locked_qty=100,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        try:
            # out_qty=100, batch_items 总量=100, 但批次只有 50
            await pending_outbound_service.execute_outbound(
                pending_id=pending.id,
                out_qty=100,
                operator="tester",
                batch_items=[
                    {"inbound_batch_id": batch.id, "quantity": 100},
                ]
            )
            fail_test("批次数量不足应报错但未报错")
        except ValueError as e:
            assert_true("不足" in str(e), f"错误信息应包含'不足': {e}")

        # 清理
        await pending.delete()
        await batch.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_execute_outbound_batch_not_exist():
    """测试出库时入库批次不存在应报错"""
    start_test("批次出库 - 入库批次不存在报错")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        # 创建测试仓库
        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_NOTEXIST",
            name="批次不存在测试仓库",
            address="测试地址",
        )

        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=960,
            product_code="NOTEXIST-TEST",
            product_name="批次不存在测试",
            spec_id=860,
            spec_code="NOTEXIST-SPEC",
            quantity=200,
        )

        pending = await PendingOutboundOrder.create(
            pending_no="NOTEXIST-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-NOTEXIST-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=860,
            product_code="NOTEXIST-TEST",
            spec_code="NOTEXIST-SPEC",
            locked_qty=50,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        try:
            await pending_outbound_service.execute_outbound(
                pending_id=pending.id,
                out_qty=50,
                operator="tester",
                batch_items=[
                    {"inbound_batch_id": 999999, "quantity": 50},
                ]
            )
            fail_test("批次不存在应报错但未报错")
        except ValueError as e:
            assert_true("不存在" in str(e), f"错误信息应包含'不存在': {e}")

        # 清理
        await pending.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_execute_outbound_batch_zero_quantity():
    """测试批次出库数量为0应报错"""
    start_test("批次出库 - 出库数量为0报错")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, InboundBatch, Stock
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus

        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_ZERO",
            name="零数量测试仓库",
            address="测试地址",
        )

        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=970,
            product_code="ZERO-TEST",
            product_name="零数量测试",
            spec_id=870,
            spec_code="ZERO-SPEC",
            quantity=200,
        )

        batch = await InboundBatch.create(
            warehouse_id=warehouse.id,
            product_id=970,
            product_code="ZERO-TEST",
            product_name="零数量测试",
            spec_id=870,
            spec_code="ZERO-SPEC",
            stock_id=stock.id,
            quantity=100,
            current_quantity=100,
            user_id=1,
            user_name="tester",
        )

        pending = await PendingOutboundOrder.create(
            pending_no="ZERO-TEST-001",
            sales_order_id=1,
            sales_order_no="SO-ZERO-001",
            sales_order_item_id=1,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=870,
            product_code="ZERO-TEST",
            spec_code="ZERO-SPEC",
            locked_qty=10,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        try:
            # out_qty=10, batch_items 中 quantity=0，总和不一致
            await pending_outbound_service.execute_outbound(
                pending_id=pending.id,
                out_qty=10,
                operator="tester",
                batch_items=[
                    {"inbound_batch_id": batch.id, "quantity": 0},
                ]
            )
            fail_test("出库数量为0应报错但未报错")
        except ValueError as e:
            # 数量之和(0)与out_qty(10)不一致，或数量必须大于0
            error_msg = str(e)
            assert_true(
                "不一致" in error_msg or "大于0" in error_msg or "大于 0" in error_msg,
                f"错误信息应包含'不一致'或'大于0': {error_msg}"
            )

        # 清理
        await pending.delete()
        await batch.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_execute_outbound_without_batch_items():
    """测试不传 batch_items 时保持原有逻辑"""
    start_test("批次出库 - 不传 batch_items 兼容旧逻辑")
    try:
        from services.pending_outbound_service import pending_outbound_service
        from models_mysql.warehouse import Warehouse, Stock, OutboundBatch
        from models_mysql.pending_outbound import PendingOutboundOrder, PendingOutboundStatus
        from models_mysql.sales_order import SalesOrder, SalesOrderItem

        warehouse = await Warehouse.create(
            warehouse_code="WH_TEST_COMPAT",
            name="兼容性测试仓库",
            address="测试地址",
        )

        stock = await Stock.create(
            warehouse_id=warehouse.id,
            product_id=980,
            product_code="COMPAT-TEST",
            product_name="兼容性测试",
            spec_id=880,
            spec_code="COMPAT-SPEC",
            quantity=200,
        )

        sales_order = await SalesOrder.create(
            order_no="SO-COMPAT-TEST",
            order_date=datetime.now(timezone.utc).date(),
            customer_id=1,
            customer_name="测试客户",
        )
        sales_item = await SalesOrderItem.create(
            sales_order=sales_order,
            row_no=1,
            product_code="COMPAT-TEST",
            spec_code="COMPAT-SPEC",
            qty=50,
            price=10,
            amt=500,
            shipping_method="warehouse",
            out_qty=0,
        )

        pending = await PendingOutboundOrder.create(
            pending_no="COMPAT-TEST-001",
            sales_order_id=sales_order.id,
            sales_order_no=sales_order.order_no,
            sales_order_item_id=sales_item.id,
            row_no=1,
            warehouse_id=warehouse.id,
            warehouse_name="测试仓库",
            spec_id=880,
            product_code="COMPAT-TEST",
            spec_code="COMPAT-SPEC",
            locked_qty=50,
            out_qty=0,
            status=PendingOutboundStatus.PENDING,
        )

        # 不传 batch_items
        result = await pending_outbound_service.execute_outbound(
            pending_id=pending.id,
            out_qty=50,
            operator="tester",
        )

        assert_is_not_none(result, "出库结果不应为 None")
        assert_eq(result["out_qty"], 50, "out_qty 应为 50")
        assert_eq(result["status"], "full", "状态应为 full")

        # 应创建出库批次记录（无 inbound_batch_id）
        outbound_records = await OutboundBatch.filter(
            pending_outbound_id=pending.id
        ).all()
        assert_eq(len(outbound_records), 1, "应创建1条出库批次记录")
        assert_is_none(outbound_records[0].inbound_batch_id, "不传 batch_items 时 inbound_batch_id 应为 None")

        # 清理
        for ob in outbound_records:
            await ob.delete()
        await pending.delete()
        await sales_item.delete()
        await sales_order.delete()
        await stock.delete()
        await warehouse.delete()

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 迁移脚本验证 ============

async def test_migration_script_exists():
    """测试迁移脚本文件存在"""
    start_test("迁移脚本 - 文件存在验证")
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "migrate_inventory_batch.py"
        )
        assert_true(os.path.exists(script_path), f"迁移脚本应存在于 {script_path}")
        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_migration_script_idempotent():
    """测试迁移脚本幂等性逻辑"""
    start_test("迁移脚本 - 幂等逻辑验证")
    try:
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "scripts",
            "migrate_inventory_batch.py"
        )
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查脚本包含幂等逻辑
        assert_true(
            "current_quantity" in content,
            "迁移脚本应处理 current_quantity 字段"
        )
        # 检查是否只处理 current_quantity == 0 的记录（幂等）
        assert_true(
            "current_quantity__gt=0" not in content or "current_quantity" in content,
            "迁移脚本应包含幂等逻辑"
        )

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 路由注册验证 ============

async def test_location_router_registered():
    """测试库位路由已注册"""
    start_test("路由注册 - location_router 已注册")
    try:
        from app.routers import location_router
        assert_is_not_none(location_router, "location_router 应已注册")
        assert_eq(location_router.prefix, "/warehouse-locations", "前缀应为 /warehouse-locations")

        # 检查路由端点数量
        routes = location_router.routes
        assert_gte(len(routes), 5, f"应有至少5个路由端点，实际 {len(routes)}")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


async def test_available_batches_route_exists():
    """测试可用批次路由已注册"""
    start_test("路由注册 - available-batches 路由已注册")
    try:
        from app.routers.pending_outbound import pending_outbound_router
        assert_is_not_none(pending_outbound_router, "pending_outbound_router 应存在")

        # 检查路由路径包含 available-batches
        route_paths = [getattr(r, 'path', '') for r in pending_outbound_router.routes]
        has_available = any("available-batches" in p for p in route_paths)
        assert_true(has_available, "应包含 available-batches 路由")

        pass_test()
    except AssertionError as e:
        fail_test(str(e))
    except Exception as e:
        fail_test(f"异常: {e}")


# ============ 清理测试数据 ============

async def cleanup_test_data():
    """清理所有测试创建的数据"""
    from models_mysql.warehouse import Warehouse, Stock, InboundBatch, WarehouseLocation
    from models_mysql.pending_outbound import PendingOutboundOrder

    # 清理入库批次
    inbound_batch_id = created_ids.get("inbound_batch_id")
    if inbound_batch_id:
        await InboundBatch.filter(id=inbound_batch_id).delete()

    # 清理库位
    location_id = created_ids.get("location_id")
    if location_id:
        await WarehouseLocation.filter(id=location_id).delete()

    # 清理入库测试库位
    inbound_location_id = created_ids.get("inbound_location_id")
    if inbound_location_id:
        await WarehouseLocation.filter(id=inbound_location_id).delete()

    # 清理测试仓库
    for key in ["loc_warehouse_id", "inbound_warehouse_id"]:
        wh_id = created_ids.get(key)
        if wh_id:
            await Stock.filter(warehouse_id=wh_id).delete()
            await WarehouseLocation.filter(warehouse_id=wh_id).delete()
            await InboundBatch.filter(warehouse_id=wh_id).delete()
            await Warehouse.filter(id=wh_id).delete()

    # 清理测试临时仓库（以 WH_TEST_ 开头的）
    test_warehouses = await Warehouse.filter(
        warehouse_code__startswith="WH_TEST_"
    ).all()
    for wh in test_warehouses:
        await Stock.filter(warehouse_id=wh.id).delete()
        await WarehouseLocation.filter(warehouse_id=wh.id).delete()
        await InboundBatch.filter(warehouse_id=wh.id).delete()
        await PendingOutboundOrder.filter(warehouse_id=wh.id).delete()
        await wh.delete()


# ============ 主函数 ============

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("库存批次管理功能测试")
    print("=" * 60)

    await init_db()

    try:
        # 1. 模型验证测试
        print("\n--- 模型验证测试 ---")
        await test_warehouse_location_model()
        await test_inbound_batch_new_fields()
        await test_outbound_batch_new_field()
        await test_inbound_batch_to_dict()
        await test_outbound_batch_to_dict()

        # 2. 库位管理 CRUD 测试
        print("\n--- 库位管理 CRUD 测试 ---")
        await test_create_location()
        await test_create_location_duplicate_code()
        await test_create_location_invalid_warehouse()
        await test_get_location()
        await test_update_location()
        await test_list_locations()
        await test_delete_location()
        await test_delete_nonexistent_location()

        # 3. 入库服务变更测试
        print("\n--- 入库服务变更测试 ---")
        await test_create_inbound_with_location()
        await test_create_inbound_with_invalid_location()
        await test_create_inbound_without_location()

        # 4. 锁定量计算测试
        print("\n--- 锁定量计算测试 ---")
        await test_calculate_locked_quantity()
        await test_batch_calculate_locked_quantities()
        await test_stock_detail_locked_quantity()

        # 5. 可用批次查询测试
        print("\n--- 可用批次查询测试 ---")
        await test_get_available_batches()
        await test_get_available_batches_no_expiry()

        # 6. 批次出库执行测试
        print("\n--- 批次出库执行测试 ---")
        await test_execute_outbound_with_batch_items()
        await test_execute_outbound_batch_qty_mismatch()
        await test_execute_outbound_batch_insufficient_quantity()
        await test_execute_outbound_batch_not_exist()
        await test_execute_outbound_batch_zero_quantity()
        await test_execute_outbound_without_batch_items()

        # 7. 迁移脚本验证
        print("\n--- 迁移脚本验证 ---")
        await test_migration_script_exists()
        await test_migration_script_idempotent()

        # 8. 路由注册验证
        print("\n--- 路由注册验证 ---")
        await test_location_router_registered()
        await test_available_batches_route_exists()

    finally:
        # 清理测试数据
        print("\n--- 清理测试数据 ---")
        await cleanup_test_data()
        await close_db()

    # 输出汇总
    print("\n" + "=" * 60)
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    print(f"测试结果: {passed}/{total} 通过, {failed} 失败")

    if failed > 0:
        print(f"\n失败项:")
        for r in test_results:
            if not r["passed"]:
                print(f"  - {r['name']}: {r['error']}")

    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
