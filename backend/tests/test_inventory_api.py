"""库存模块接口测试脚本

测试流程: 仓库 → 入库 → 库存 → 出库 的完整CRUD及异常验证
使用方法: python tests/test_inventory_api.py
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record(self, name, success, detail=""):
        if success:
            self.passed += 1
            print(f"  [OK] {name}")
        else:
            self.failed += 1
            self.errors.append({"test": name, "detail": detail})
            print(f"  [FAIL] {name}: {detail}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"测试结果: {self.passed}/{total} 通过, {self.failed} 失败")
        if self.errors:
            print(f"\n失败项:")
            for e in self.errors:
                print(f"  - {e['test']}: {e['detail']}")
        print(f"{'='*60}")
        return self.failed == 0


result = TestResult()
created_ids = {}


def api(method, path, data=None, params=None, expect_status=200):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=HEADERS, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=HEADERS, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=HEADERS, timeout=30)
        else:
            return None, f"未知方法: {method}"
        return resp, None
    except requests.exceptions.ConnectionError:
        return None, "服务未启动或连接失败"


def parse(resp, err, test_name):
    if err:
        result.record(test_name, False, err)
        return None
    if resp.status_code != 200:
        result.record(test_name, False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        return None
    try:
        body = resp.json()
    except Exception:
        result.record(test_name, False, f"响应非JSON: {resp.text[:200]}")
        return None
    return body


def check_response_ok(body, test_name):
    if body.get("status") != "success":
        result.record(test_name, False, f"status != success: {body.get('message')}")
        return False
    return True


def check_field(body, field, test_name):
    if field not in body:
        result.record(test_name, False, f"响应缺少字段: {field}")
        return False
    return True


# ============ 仓库测试 ============

def test_create_warehouse():
    print("\n[1/16] 创建仓库")
    resp, err = api("POST", "/warehouses/", {
        "warehouse_code": "WH_TEST_001",
        "name": "测试仓库-深圳仓",
        "address": "深圳市南山区科技园路100号",
        "manager_name": "测试管理员",
        "status": "active",
        "description": "库存接口测试用仓库"
    })
    body = parse(resp, err, "创建仓库")
    if not body:
        return None
    ok = check_response_ok(body, "创建仓库")
    if ok and check_field(body, "result", "创建仓库"):
        data = body["result"]
        wh_id = data.get("id")
        result.record("创建仓库-返回id", bool(wh_id), f"id={wh_id}")
        result.record("创建仓库-warehouse_code正确", data.get("warehouse_code") == "WH_TEST_001")
        result.record("创建仓库-name正确", data.get("name") == "测试仓库-深圳仓")
        result.record("创建仓库-address正确", data.get("address") == "深圳市南山区科技园路100号")
        result.record("创建仓库-status默认active", data.get("status") == "active")
        created_ids["warehouse_id"] = wh_id
        return wh_id
    return None


def test_list_warehouses():
    print("\n[2/16] 查询仓库列表")
    resp, err = api("GET", "/warehouses/", params={"page": 1, "page_size": 20})
    body = parse(resp, err, "查询仓库列表")
    if not body:
        return
    ok = check_response_ok(body, "查询仓库列表")
    if ok and check_field(body, "result", "查询仓库列表"):
        data = body["result"]
        result.record("仓库列表-包含total", "total" in data, f"keys={list(data.keys())}")
        result.record("仓库列表-包含items", "items" in data)
        result.record("仓库列表-包含page", "page" in data)
        result.record("仓库列表-包含page_size", "page_size" in data)
        items = data.get("items", [])
        if items and created_ids.get("warehouse_id"):
            wh_ids = [w.get("id") for w in items]
            found = created_ids["warehouse_id"] in wh_ids
            result.record("仓库列表-包含新建仓库", found)
        result.record("仓库列表-total为整数", isinstance(data.get("total"), int))


def test_get_warehouse():
    print("\n[3/16] 查询仓库详情")
    wh_id = created_ids.get("warehouse_id", "")
    if not wh_id:
        print("  [SKIP] 跳过（无测试仓库）")
        return
    resp, err = api("GET", f"/warehouses/{wh_id}")
    body = parse(resp, err, "查询仓库详情")
    if not body:
        return
    ok = check_response_ok(body, "查询仓库详情")
    if ok and check_field(body, "result", "查询仓库详情"):
        data = body["result"]
        result.record("仓库详情-包含id", "id" in data)
        result.record("仓库详情-包含name", "name" in data)
        result.record("仓库详情-包含warehouse_code", "warehouse_code" in data)
        result.record("仓库详情-包含address", "address" in data)
        result.record("仓库详情-包含status", "status" in data)
        result.record("仓库详情-名称匹配", data.get("name") == "测试仓库-深圳仓")


def test_update_warehouse():
    print("\n[4/16] 更新仓库")
    wh_id = created_ids.get("warehouse_id", "")
    if not wh_id:
        print("  [SKIP] 跳过（无测试仓库）")
        return
    resp, err = api("PUT", f"/warehouses/{wh_id}", {
        "name": "测试仓库-已更新",
        "address": "深圳市南山区科技园路200号",
        "description": "更新后的描述"
    })
    body = parse(resp, err, "更新仓库")
    if not body:
        return
    ok = check_response_ok(body, "更新仓库")
    if ok:
        result.record("更新仓库-返回成功", body.get("message") == "仓库更新成功", f"msg={body.get('message')}")
    resp2, _ = api("GET", f"/warehouses/{wh_id}")
    body2 = parse(resp2, None, "更新仓库-验证")
    if body2 and body2.get("result"):
        data = body2["result"]
        result.record("更新仓库-name已更新", data.get("name") == "测试仓库-已更新", f"name={data.get('name')}")
        result.record("更新仓库-address已更新", data.get("address") == "深圳市南山区科技园路200号")


# ============ 入库批次测试 ============

def test_create_inbound_batch():
    print("\n[5/16] 创建入库批次（自动创建库存）")
    wh_id = created_ids.get("warehouse_id", "")

    # 先创建分类
    resp, err = api("POST", "/categories/", {
        "name": "测试库存分类",
        "tax_code": "TAX_INV"
    })
    cat_body = parse(resp, err, "创建测试分类")
    if cat_body and cat_body.get("status") == "success":
        created_ids["category_id"] = cat_body["result"]["id"]

    # 创建品牌
    resp, err = api("POST", "/brands/", {"name": "测试库存品牌"})
    brand_body = parse(resp, err, "创建测试品牌")
    if brand_body and brand_body.get("status") == "success":
        created_ids["brand_id"] = brand_body["result"]["id"]

    # 创建商品
    resp, err = api("POST", "/products/", {
        "name": "测试库存商品",
        "category_id": created_ids.get("category_id", ""),
        "brand_id": created_ids.get("brand_id", "")
    })
    prod_body = parse(resp, err, "创建测试商品")
    if not prod_body or prod_body.get("status") != "success":
        print("  [SKIP] 无法创建测试商品")
        return None
    created_ids["product_id"] = prod_body["result"]["id"]

    # 创建规格
    resp, err = api("POST", f"/products/{created_ids['product_id']}/specs", {
        "spec_code": "SPEC_INV_001",
        "packaging": "500g/袋",
        "price": 88.00
    })
    spec_body = parse(resp, err, "创建测试规格")
    if not spec_body or spec_body.get("status") != "success":
        print("  [SKIP] 无法创建测试规格")
        return None
    created_ids["spec_id"] = spec_body["result"]["id"]

    # 创建入库批次
    resp, err = api("POST", "/inbound-batches/", {
        "warehouse_id": wh_id,
        "product_id": created_ids["product_id"],
        "product_code": prod_body["result"].get("product_code", ""),
        "product_name": "测试库存商品",
        "spec_id": created_ids["spec_id"],
        "spec_code": "SPEC_INV_001",
        "quantity": 100,
        "user_id": 1,
        "user_name": "测试操作员"
    })
    body = parse(resp, err, "创建入库批次")
    if not body:
        return None
    ok = check_response_ok(body, "创建入库批次")
    if ok and check_field(body, "result", "创建入库批次"):
        data = body["result"]
        batch_id = data.get("id")
        stock_id = data.get("stock_id")
        result.record("创建入库批次-返回id", bool(batch_id), f"id={batch_id}")
        result.record("创建入库批次-stock_id已填充", bool(stock_id), f"stock_id={stock_id}")
        result.record("创建入库批次-warehouse_id正确", data.get("warehouse_id") == wh_id)
        result.record("创建入库批次-quantity正确", data.get("quantity") == 100)
        result.record("创建入库批次-product_name正确", data.get("product_name") == "测试库存商品")
        created_ids["inbound_batch_id"] = batch_id
        created_ids["stock_id"] = stock_id
        return batch_id
    return None


def test_list_inbound_batches():
    print("\n[6/16] 查询入库批次列表")
    stock_id = created_ids.get("stock_id", "")
    params = {"page": 1, "page_size": 20}
    if stock_id:
        params["stock_id"] = stock_id
    resp, err = api("GET", "/inbound-batches/", params=params)
    body = parse(resp, err, "查询入库批次列表")
    if not body:
        return
    ok = check_response_ok(body, "查询入库批次列表")
    if ok and check_field(body, "result", "查询入库批次列表"):
        data = body["result"]
        result.record("入库批次列表-包含total", "total" in data)
        result.record("入库批次列表-包含items", "items" in data)
        items = data.get("items", [])
        if items and created_ids.get("inbound_batch_id"):
            batch_ids = [b.get("id") for b in items]
            found = created_ids["inbound_batch_id"] in batch_ids
            result.record("入库批次列表-包含新建批次", found)


def test_get_inbound_batch():
    print("\n[7/16] 查询入库批次详情")
    batch_id = created_ids.get("inbound_batch_id", "")
    if not batch_id:
        print("  [SKIP] 跳过（无测试入库批次）")
        return
    resp, err = api("GET", f"/inbound-batches/{batch_id}")
    body = parse(resp, err, "查询入库批次详情")
    if not body:
        return
    ok = check_response_ok(body, "查询入库批次详情")
    if ok and check_field(body, "result", "查询入库批次详情"):
        data = body["result"]
        result.record("入库批次详情-包含id", "id" in data)
        result.record("入库批次详情-包含warehouse_id", "warehouse_id" in data)
        result.record("入库批次详情-包含stock_id", "stock_id" in data)
        result.record("入库批次详情-包含quantity", "quantity" in data)
        result.record("入库批次详情-包含product_name", "product_name" in data)


def test_update_inbound_batch():
    print("\n[8/16] 更新入库批次")
    batch_id = created_ids.get("inbound_batch_id", "")
    if not batch_id:
        print("  [SKIP] 跳过（无测试入库批次）")
        return
    resp, err = api("PUT", f"/inbound-batches/{batch_id}", {
        "product_name": "测试入库商品-已更新"
    })
    body = parse(resp, err, "更新入库批次")
    if not body:
        return
    ok = check_response_ok(body, "更新入库批次")
    if ok:
        result.record("更新入库批次-返回成功", body.get("message") == "入库批次更新成功", f"msg={body.get('message')}")


# ============ 库存测试 ============

def test_list_stocks():
    print("\n[9/16] 查询库存列表")
    wh_id = created_ids.get("warehouse_id", "")
    params = {"page": 1, "page_size": 20}
    if wh_id:
        params["warehouse_id"] = wh_id
    resp, err = api("GET", "/stocks/", params=params)
    body = parse(resp, err, "查询库存列表")
    if not body:
        return
    ok = check_response_ok(body, "查询库存列表")
    if ok and check_field(body, "result", "查询库存列表"):
        data = body["result"]
        result.record("库存列表-包含total", "total" in data)
        result.record("库存列表-包含items", "items" in data)
        result.record("库存列表-包含page", "page" in data)
        result.record("库存列表-包含page_size", "page_size" in data)
        items = data.get("items", [])
        if items and created_ids.get("stock_id"):
            stock_ids = [s.get("id") for s in items]
            found = created_ids["stock_id"] in stock_ids
            result.record("库存列表-包含入库创建的库存", found)


def test_get_stock():
    print("\n[10/16] 查询库存详情")
    stock_id = created_ids.get("stock_id", "")
    if not stock_id:
        print("  [SKIP] 跳过（无测试库存）")
        return
    resp, err = api("GET", f"/stocks/{stock_id}")
    body = parse(resp, err, "查询库存详情")
    if not body:
        return
    ok = check_response_ok(body, "查询库存详情")
    if ok and check_field(body, "result", "查询库存详情"):
        data = body["result"]
        result.record("库存详情-包含id", "id" in data)
        result.record("库存详情-包含warehouse_id", "warehouse_id" in data)
        result.record("库存详情-包含product_id", "product_id" in data)
        result.record("库存详情-包含quantity", "quantity" in data)
        result.record("库存详情-入库数量正确", data.get("quantity") == 100, f"quantity={data.get('quantity')}")


def test_update_stock():
    print("\n[11/16] 手动盘库更新库存")
    stock_id = created_ids.get("stock_id", "")
    if not stock_id:
        print("  [SKIP] 跳过（无测试库存）")
        return
    resp, err = api("PUT", f"/stocks/{stock_id}", {
        "quantity": 95,
        "min_stock": 10,
        "max_stock": 500
    })
    body = parse(resp, err, "手动盘库更新")
    if not body:
        return
    ok = check_response_ok(body, "手动盘库更新")
    if ok:
        result.record("手动盘库-返回成功", body.get("message") == "库存更新成功", f"msg={body.get('message')}")
    resp2, _ = api("GET", f"/stocks/{stock_id}")
    body2 = parse(resp2, None, "手动盘库-验证")
    if body2 and body2.get("result"):
        data = body2["result"]
        result.record("手动盘库-quantity已更新", data.get("quantity") == 95, f"quantity={data.get('quantity')}")


# ============ 出库批次测试 ============

def test_create_outbound_batch():
    print("\n[12/16] 创建出库批次")
    stock_id = created_ids.get("stock_id", "")
    wh_id = created_ids.get("warehouse_id", "")
    product_id = created_ids.get("product_id", "")
    spec_id = created_ids.get("spec_id", "")
    if not stock_id:
        print("  [SKIP] 跳过（无测试库存）")
        return None
    resp, err = api("POST", "/outbound-batches/", {
        "warehouse_id": wh_id,
        "product_id": product_id,
        "product_code": "TPC001",
        "product_name": "测试出库商品",
        "spec_id": spec_id,
        "spec_code": "SPEC_INV_001",
        "stock_id": stock_id,
        "quantity": 20,
        "user_id": 1,
        "user_name": "测试操作员"
    })
    body = parse(resp, err, "创建出库批次")
    if not body:
        return None
    ok = check_response_ok(body, "创建出库批次")
    if ok and check_field(body, "result", "创建出库批次"):
        data = body["result"]
        batch_id = data.get("id")
        result.record("创建出库批次-返回id", bool(batch_id), f"id={batch_id}")
        result.record("创建出库批次-stock_id正确", data.get("stock_id") == stock_id)
        result.record("创建出库批次-quantity正确", data.get("quantity") == 20)
        result.record("创建出库批次-warehouse_id正确", data.get("warehouse_id") == wh_id)
        created_ids["outbound_batch_id"] = batch_id
        resp2, _ = api("GET", f"/stocks/{stock_id}")
        body2 = parse(resp2, None, "出库后验证库存数量")
        if body2 and body2.get("result"):
            result.record("出库后-库存数量扣减正确", body2["result"].get("quantity") == 75,
                           f"quantity={body2['result'].get('quantity')}")
        return batch_id
    return None


def test_list_outbound_batches():
    print("\n[13/16] 查询出库批次列表")
    stock_id = created_ids.get("stock_id", "")
    params = {"page": 1, "page_size": 20}
    if stock_id:
        params["stock_id"] = stock_id
    resp, err = api("GET", "/outbound-batches/", params=params)
    body = parse(resp, err, "查询出库批次列表")
    if not body:
        return
    ok = check_response_ok(body, "查询出库批次列表")
    if ok and check_field(body, "result", "查询出库批次列表"):
        data = body["result"]
        result.record("出库批次列表-包含total", "total" in data)
        result.record("出库批次列表-包含items", "items" in data)
        items = data.get("items", [])
        if items and created_ids.get("outbound_batch_id"):
            batch_ids = [b.get("id") for b in items]
            found = created_ids["outbound_batch_id"] in batch_ids
            result.record("出库批次列表-包含新建批次", found)


def test_get_outbound_batch():
    print("\n[14/16] 查询出库批次详情")
    batch_id = created_ids.get("outbound_batch_id", "")
    if not batch_id:
        print("  [SKIP] 跳过（无测试出库批次）")
        return
    resp, err = api("GET", f"/outbound-batches/{batch_id}")
    body = parse(resp, err, "查询出库批次详情")
    if not body:
        return
    ok = check_response_ok(body, "查询出库批次详情")
    if ok and check_field(body, "result", "查询出库批次详情"):
        data = body["result"]
        result.record("出库批次详情-包含id", "id" in data)
        result.record("出库批次详情-包含stock_id", "stock_id" in data)
        result.record("出库批次详情-包含quantity", "quantity" in data)
        result.record("出库批次详情-包含product_name", "product_name" in data)


def test_update_outbound_batch():
    print("\n[15/16] 更新出库批次")
    batch_id = created_ids.get("outbound_batch_id", "")
    if not batch_id:
        print("  [SKIP] 跳过（无测试出库批次）")
        return
    resp, err = api("PUT", f"/outbound-batches/{batch_id}", {
        "product_name": "测试出库商品-已更新"
    })
    body = parse(resp, err, "更新出库批次")
    if not body:
        return
    ok = check_response_ok(body, "更新出库批次")
    if ok:
        result.record("更新出库批次-返回成功", body.get("message") == "出库批次更新成功", f"msg={body.get('message')}")


# ============ 异常验证测试 ============

def test_validation():
    print("\n[16/16] 异常参数验证测试")

    print("\n  [异常-1] 创建仓库-缺少必填warehouse_code")
    resp, err = api("POST", "/warehouses/", {"name": "无编码仓库", "address": "测试地址"})
    body = parse(resp, err, "异常-仓库缺少warehouse_code")
    if body:
        # warehouse_code 会自动生成，所以应该返回成功
        result.record("异常-仓库缺少warehouse_code应自动生成",
                       body.get("status") == "success",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-2] 创建仓库-缺少必填name")
    resp, err = api("POST", "/warehouses/", {"warehouse_code": "WH_NO_NAME", "address": "测试地址"})
    body = parse(resp, err, "异常-仓库缺少name")
    if body:
        result.record("异常-仓库缺少name应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-3] 创建仓库-缺少必填address")
    resp, err = api("POST", "/warehouses/", {"warehouse_code": "WH_NO_ADDR", "name": "无地址仓库"})
    body = parse(resp, err, "异常-仓库缺少address")
    if body:
        result.record("异常-仓库缺少address应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-4] 创建入库批次-缺少必填字段")
    resp, err = api("POST", "/inbound-batches/", {"quantity": 10})
    body = parse(resp, err, "异常-入库批次缺少必填字段")
    if body:
        result.record("异常-入库批次缺少必填字段应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-5] 创建出库批次-缺少必填字段")
    resp, err = api("POST", "/outbound-batches/", {"quantity": 10})
    body = parse(resp, err, "异常-出库批次缺少必填字段")
    if body:
        result.record("异常-出库批次缺少必填字段应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-6] 创建出库批次-stock_id不存在")
    resp, err = api("POST", "/outbound-batches/", {
        "warehouse_id": created_ids.get("warehouse_id", ""),
        "product_id": created_ids.get("product_id", 1),
        "product_code": "TPC001",
        "product_name": "测试",
        "spec_id": created_ids.get("spec_id", 1),
        "spec_code": "SPEC001",
        "stock_id": 99999,
        "quantity": 10,
        "user_id": 1,
        "user_name": "测试"
    })
    body = parse(resp, err, "异常-出库stock_id不存在")
    if body:
        result.record("异常-出库stock_id不存在应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-7] 出库数量超过库存")
    stock_id = created_ids.get("stock_id", "")
    if stock_id:
        resp, err = api("POST", "/outbound-batches/", {
            "warehouse_id": created_ids.get("warehouse_id", ""),
            "product_id": created_ids.get("product_id", 1),
            "product_code": "TPC001",
            "product_name": "测试",
            "spec_id": created_ids.get("spec_id", 1),
            "spec_code": "SPEC001",
            "stock_id": stock_id,
            "quantity": 999999,
            "user_id": 1,
            "user_name": "测试"
        })
        body = parse(resp, err, "异常-出库超库存")
        if body:
            result.record("异常-出库数量超过库存应报错",
                           body.get("status") == "error",
                           f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-8] 查询不存在的仓库详情")
    resp, err = api("GET", "/warehouses/99999")
    body = parse(resp, err, "异常-查询不存在仓库")
    if body:
        result.record("异常-查询不存在仓库应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-9] 查询不存在的库存详情")
    resp, err = api("GET", "/stocks/99999")
    body = parse(resp, err, "异常-查询不存在库存")
    if body:
        result.record("异常-查询不存在库存应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-10] 查询不存在的入库批次详情")
    resp, err = api("GET", "/inbound-batches/99999")
    body = parse(resp, err, "异常-查询不存在入库批次")
    if body:
        result.record("异常-查询不存在入库批次应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-11] 查询不存在的出库批次详情")
    resp, err = api("GET", "/outbound-batches/99999")
    body = parse(resp, err, "异常-查询不存在出库批次")
    if body:
        result.record("异常-查询不存在出库批次应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-12] 手动盘库-库存不存在")
    resp, err = api("PUT", "/stocks/99999", {"quantity": 10})
    body = parse(resp, err, "异常-盘库库存不存在")
    if body:
        result.record("异常-盘库库存不存在应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")


def main():
    import time as _time
    _time.sleep(2)

    print("=" * 60)
    print("库存模块接口测试")
    print(f"服务地址: {BASE_URL}")
    print("=" * 60)

    health_resp, health_err = api("GET", "/health/")
    if health_err or (health_resp and health_resp.status_code != 200):
        print(f"\n[FAIL] 服务未就绪: {health_err or health_resp.status_code}")
        sys.exit(1)
    print("[OK] 服务健康检查通过")

    test_create_warehouse()
    test_list_warehouses()
    test_get_warehouse()
    test_update_warehouse()
    test_create_inbound_batch()
    test_list_inbound_batches()
    test_get_inbound_batch()
    test_update_inbound_batch()
    test_list_stocks()
    test_get_stock()
    test_update_stock()
    test_create_outbound_batch()
    test_list_outbound_batches()
    test_get_outbound_batch()
    test_update_outbound_batch()
    test_validation()

    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
