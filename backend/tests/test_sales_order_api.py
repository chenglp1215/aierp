"""销售订单模块接口测试脚本 (MySQL 版本)

测试流程: 查找已有数据 → 创建订单 → 列表/详情/搜索 → 更新 → 状态流转 → 删除
使用方法: python tests/test_sales_order_api.py

接口变更说明 (MySQL 迁移后):
- 新增 submit/approve/reject/cancel 独立状态操作接口
- 订单状态新增 pending（待审核）
- 响应格式中状态字段直接返回 order_status 等字符串值
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
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            self.errors.append({"test": name, "detail": detail})
            print(f"  ❌ {name}: {detail}")

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


def api(method, path, data=None, params=None, expect_status=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=HEADERS, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=HEADERS, timeout=30)
        elif method == "PATCH":
            resp = requests.patch(url, json=data, headers=HEADERS, timeout=30)
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
    try:
        body = resp.json()
    except Exception:
        result.record(test_name, False, f"响应非JSON: {resp.text[:200]}")
        return None
    return body


def find_existing_customer():
    print("\n🔍 查找已有客户")
    resp, err = api("GET", "/customers/", params={"page": 1, "page_size": 1})
    body = parse(resp, err, "查找客户")
    if not body or body.get("status") != "success":
        return None
    items = body.get("result", {}).get("items", [])
    if not items:
        print("  ⚠️ 数据库中没有客户数据，请先创建客户")
        return None
    customer_id = items[0].get("id")
    customer_name = items[0].get("name", "")
    result.record("查找已有客户", bool(customer_id), f"id={customer_id}, name={customer_name}")
    return customer_id


def find_existing_product():
    print("\n🔍 查找已有商品和规格")
    resp, err = api("GET", "/products/", params={"page": 1, "page_size": 1})
    body = parse(resp, err, "查找商品")
    if not body or body.get("status") != "success":
        return None, None
    items = body.get("result", {}).get("items", [])
    if not items:
        print("  ⚠️ 数据库中没有商品数据，请先创建商品")
        return None, None
    product = items[0]
    product_code = product.get("product_code")
    specs = product.get("specs", [])
    spec_code = specs[0].get("spec_code") if specs else None
    result.record("查找已有商品", bool(product_code), f"product_code={product_code}")
    result.record("查找已有规格", bool(spec_code), f"spec_code={spec_code}")
    return product_code, spec_code


def _build_order_items(product_code, spec_code, qty=10):
    return [{
        "row_no": 1,
        "product_code": product_code,
        "spec_code": spec_code,
        "qty": qty,
        "price": 100.00,
        "discount": 1.0,
        "shipping_method": "快递",
    }]


def test_create_order(customer_id, product_code, spec_code):
    print("\n📦 [1/14] 创建销售订单")
    payload = {
        "order_date": "2026-05-12",
        "customer_id": customer_id,
        "customer_name": "测试客户",
        "settle_type": "月结",
        "tax_rate": 0.13,
        "expect_deliver_date": "2026-06-01",
        "remark": "接口测试订单",
        "items": _build_order_items(product_code, spec_code),
    }
    resp, err = api("POST", "/sales-orders/", payload)
    body = parse(resp, err, "创建订单")
    if not body:
        return None
    if body.get("status") != "success":
        result.record("创建订单", False, body.get("message", "未知错误"))
        return None
    order = body.get("result", {})
    order_no = order.get("order_no")
    result.record("创建订单-返回order_no", bool(order_no), f"order_no={order_no}")
    result.record("创建订单-返回id", bool(order.get("id")), f"id={order.get('id')}")

    resp2, _ = api("GET", f"/sales-orders/{order_no}")
    body2 = parse(resp2, None, "创建订单-验证详情")
    if body2 and body2.get("result"):
        detail = body2["result"]
        actual_status = detail.get("order_status")
        print(f"  📋 详情: order_no={detail.get('order_no')}, order_status={actual_status}, customer_id={detail.get('customer_id')}")
        result.record("创建订单-状态为draft",
                       actual_status == "draft",
                       f"order_status={actual_status}")
        result.record("创建订单-customer_id正确",
                       detail.get("customer_id") == customer_id)
        result.record("创建订单-明细数量正确",
                       len(detail.get("items", [])) == 1,
                       f"items_count={len(detail.get('items', []))}")
        if detail.get("items"):
            item = detail["items"][0]
            result.record("创建订单-商品编码回填",
                           item.get("product_code") == product_code,
                           f"product_code={item.get('product_code')}")
            result.record("创建订单-商品名称回填",
                           bool(item.get("product_name")),
                           f"product_name={item.get('product_name')}")
    return order_no


def test_create_and_submit(customer_id, product_code, spec_code):
    print("\n📦 [2/14] 创建并提交销售订单")
    payload = {
        "order_date": "2026-05-12",
        "customer_id": customer_id,
        "customer_name": "测试客户",
        "settle_type": "月结",
        "tax_rate": 0.13,
        "items": _build_order_items(product_code, spec_code, qty=20),
    }
    resp, err = api("POST", "/sales-orders/create-and-submit", payload)
    body = parse(resp, err, "创建并提交订单")
    if not body:
        return None
    if body.get("status") != "success":
        result.record("创建并提交订单", False, body.get("message", "未知错误"))
        return None
    order = body.get("result", {})
    order_no = order.get("order_no")
    result.record("创建并提交订单-返回order_no", bool(order_no))

    resp2, _ = api("GET", f"/sales-orders/{order_no}")
    body2 = parse(resp2, None, "创建并提交订单-验证详情")
    if body2 and body2.get("result"):
        detail = body2["result"]
        result.record("创建并提交订单-状态为audited",
                       detail.get("order_status") == "audited",
                       f"order_status={detail.get('order_status')}")
    return order_no


def test_validation_empty_items():
    print("\n📦 [3/14] 校验-空明细")
    payload = {
        "customer_id": "test_id",
        "customer_name": "测试",
        "sales_user_id": "user_001",
        "items": [],
    }
    resp, err = api("POST", "/sales-orders/", payload)
    body = parse(resp, err, "校验-空明细")
    if body:
        result.record("校验-空明细应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")


def test_validation_missing_product_code():
    print("\n📦 [4/14] 校验-缺少商品编码")
    payload = {
        "customer_id": "test_id",
        "customer_name": "测试",
        "sales_user_id": "user_001",
        "items": [{"quantity": 1, "unit_price": 10}],
    }
    resp, err = api("POST", "/sales-orders/", payload)
    body = parse(resp, err, "校验-缺少商品编码")
    if body:
        result.record("校验-缺少商品编码应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")


def test_list_orders():
    print("\n📦 [5/14] 列表查询")
    resp, err = api("GET", "/sales-orders/", params={"page": 1, "page_size": 10})
    body = parse(resp, err, "列表查询")
    if not body:
        return
    result.record("列表查询-返回成功", body.get("status") == "success", f"status={body.get('status')}")
    data = body.get("result", {})
    result.record("列表查询-包含total", "total" in data)
    result.record("列表查询-包含items", "items" in data)
    result.record("列表查询-包含page", "page" in data)
    result.record("列表查询-包含page_size", "page_size" in data)


def test_list_with_keyword():
    print("\n📦 [6/14] 关键字搜索")
    resp, err = api("GET", "/sales-orders/", params={"page": 1, "page_size": 10, "keyword": "不存在的订单XYZ"})
    body = parse(resp, err, "关键字搜索")
    if not body:
        return
    result.record("关键字搜索-返回成功", body.get("status") == "success")
    items = body.get("result", {}).get("items", [])
    result.record("关键字搜索-结果为空", len(items) == 0, f"count={len(items)}")


def test_list_with_customer_filter(customer_id):
    print("\n📦 [7/14] 按客户过滤")
    resp, err = api("GET", "/sales-orders/", params={"page": 1, "page_size": 10, "customer_id": customer_id})
    body = parse(resp, err, "按客户过滤")
    if not body:
        return
    result.record("按客户过滤-返回成功", body.get("status") == "success")


def test_get_detail(order_no):
    print("\n📦 [8/14] 获取详情")
    resp, err = api("GET", f"/sales-orders/{order_no}")
    body = parse(resp, err, "获取详情")
    if not body:
        return
    if body.get("status") != "success":
        result.record("获取详情", False, body.get("message"))
        return
    order = body.get("result", {})
    result.record("获取详情-order_no正确", order.get("order_no") == order_no)
    result.record("获取详情-包含items", "items" in order)
    result.record("获取详情-包含order_status", "order_status" in order)
    result.record("获取详情-包含customer_id", "customer_id" in order)


def test_get_detail_nonexistent():
    print("\n📦 [9/14] 获取不存在订单详情")
    resp, err = api("GET", "/sales-orders/NONEXISTENT_000")
    body = parse(resp, err, "获取不存在订单详情")
    if body:
        result.record("获取不存在订单详情-应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")


def test_update_order(order_no):
    print("\n📦 [10/14] 更新订单")
    payload = {"remark": "测试更新备注"}
    resp, err = api("PUT", f"/sales-orders/{order_no}", payload)
    body = parse(resp, err, "更新订单")
    if not body:
        return
    if body.get("status") != "success":
        result.record("更新订单", False, body.get("message"))
        return
    result.record("更新订单-返回成功", body.get("status") == "success")
    resp2, _ = api("GET", f"/sales-orders/{order_no}")
    body2 = parse(resp2, None, "更新订单-验证")
    if body2 and body2.get("result"):
        result.record("更新订单-备注已更新",
                       body2["result"].get("remark") == "测试更新备注",
                       f"remark={body2['result'].get('remark')}")


def test_submit_order(order_no):
    """提交审核：draft → pending"""
    print(f"\n📦 提交审核: {order_no}")
    resp, err = api("POST", f"/sales-orders/{order_no}/submit")
    body = parse(resp, err, "提交审核")
    if not body:
        return False
    if body.get("status") != "success":
        result.record("提交审核", False, body.get("message"))
        return False
    result.record("提交审核-返回成功", True)

    # 验证状态已变更
    resp2, _ = api("GET", f"/sales-orders/{order_no}")
    body2 = parse(resp2, None, "提交审核-验证")
    if body2 and body2.get("result"):
        actual = body2["result"].get("order_status")
        result.record("提交审核-状态为pending",
                       actual == "pending",
                       f"order_status={actual}")
    return True


def test_approve_order(order_no):
    """审核通过：pending → audited"""
    print(f"\n📦 审核通过: {order_no}")
    resp, err = api("POST", f"/sales-orders/{order_no}/approve")
    body = parse(resp, err, "审核通过")
    if not body:
        return False
    if body.get("status") != "success":
        result.record("审核通过", False, body.get("message"))
        return False
    result.record("审核通过-返回成功", True)

    resp2, _ = api("GET", f"/sales-orders/{order_no}")
    body2 = parse(resp2, None, "审核通过-验证")
    if body2 and body2.get("result"):
        actual = body2["result"].get("order_status")
        result.record("审核通过-状态为audited",
                       actual == "audited",
                       f"order_status={actual}")
    return True


def test_reject_order(order_no):
    """驳回：pending → draft"""
    print(f"\n📦 驳回订单: {order_no}")
    resp, err = api("POST", f"/sales-orders/{order_no}/reject")
    body = parse(resp, err, "驳回订单")
    if not body:
        return False
    if body.get("status") != "success":
        result.record("驳回订单", False, body.get("message"))
        return False
    result.record("驳回订单-返回成功", True)

    resp2, _ = api("GET", f"/sales-orders/{order_no}")
    body2 = parse(resp2, None, "驳回订单-验证")
    if body2 and body2.get("result"):
        actual = body2["result"].get("order_status")
        result.record("驳回订单-状态为draft",
                       actual == "draft",
                       f"order_status={actual}")
    return True


def test_cancel_order(order_no):
    """取消订单：* → cancelled"""
    print(f"\n📦 取消订单: {order_no}")
    resp, err = api("POST", f"/sales-orders/{order_no}/cancel")
    body = parse(resp, err, "取消订单")
    if not body:
        return False
    if body.get("status") != "success":
        result.record("取消订单", False, body.get("message"))
        return False
    result.record("取消订单-返回成功", True)

    resp2, _ = api("GET", f"/sales-orders/{order_no}")
    body2 = parse(resp2, None, "取消订单-验证")
    if body2 and body2.get("result"):
        actual = body2["result"].get("order_status")
        result.record("取消订单-状态为cancelled",
                       actual == "cancelled",
                       f"order_status={actual}")
    return True


def test_get_status_flows(order_no):
    print("\n📦 [13/14] 获取状态流转记录")
    resp, err = api("GET", f"/sales-orders/{order_no}/status-flows")
    body = parse(resp, err, "获取状态流转记录")
    if not body:
        return
    result.record("获取状态流转记录-返回成功", body.get("status") == "success")
    records = body.get("result", [])
    result.record("获取状态流转记录-类型为列表", isinstance(records, list), f"type={type(records).__name__}")


def test_delete_nonexistent():
    print("\n📦 删除不存在订单")
    resp, err = api("DELETE", "/sales-orders/NONEXISTENT_000")
    body = parse(resp, err, "删除不存在订单")
    if body:
        result.record("删除不存在订单-应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")


def test_delete_non_draft_order(order_no):
    print("\n📦 [14/14] 删除已审核订单（应拒绝）")
    resp, err = api("DELETE", f"/sales-orders/{order_no}")
    body = parse(resp, err, "删除已审核订单")
    if body:
        result.record("删除已审核订单-应拒绝",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")


def test_delete_draft_order(order_no):
    print("\n📦 删除草稿订单")
    resp, err = api("DELETE", f"/sales-orders/{order_no}")
    body = parse(resp, err, "删除草稿订单")
    if not body:
        return
    if body.get("status") == "success":
        result.record("删除草稿订单-成功", True)
        import time as _time
        _time.sleep(1)
        resp2, _ = api("GET", f"/sales-orders/{order_no}")
        body2 = parse(resp2, None, "删除草稿订单-验证已删除")
        if body2:
            print(f"  📋 查询响应: status={body2.get('status')}, msg={body2.get('message', '')[:80]}")
            result.record("删除草稿订单-查询应不存在",
                           body2.get("status") == "error",
                           f"status={body2.get('status')}")
    else:
        result.record("删除草稿订单", False, body.get("message"))


def main():
    time.sleep(2)
    print("=" * 60)
    print("销售订单模块接口测试 (MySQL 版本)")
    print(f"服务地址: {BASE_URL}")
    print("=" * 60)

    health_resp, health_err = api("GET", "/health")
    if health_err or (health_resp and health_resp.status_code != 200):
        print(f"\n❌ 服务未就绪: {health_err or health_resp.status_code}")
        sys.exit(1)
    print("✅ 服务健康检查通过")

    customer_id = find_existing_customer()
    if not customer_id:
        print("\n❌ 无法继续测试：缺少客户数据")
        sys.exit(1)

    product_code, spec_code = find_existing_product()
    if not product_code:
        print("\n❌ 无法继续测试：缺少商品数据")
        sys.exit(1)

    # 创建测试订单
    order_no_1 = test_create_order(customer_id, product_code, spec_code)
    order_no_2 = test_create_and_submit(customer_id, product_code, spec_code)

    # 校验测试
    test_validation_empty_items()
    test_validation_missing_product_code()

    # 列表查询测试
    test_list_orders()
    test_list_with_keyword()
    test_list_with_customer_filter(customer_id)

    if order_no_1:
        # 详情和更新测试
        test_get_detail(order_no_1)
        test_update_order(order_no_1)
        test_get_status_flows(order_no_1)

        # 状态流转测试：draft → pending → audited → cancelled
        test_submit_order(order_no_1)  # draft → pending
        test_approve_order(order_no_1)  # pending → audited

        # 创建新订单测试驳回流程
        order_no_3 = test_create_order(customer_id, product_code, spec_code)
        if order_no_3:
            test_submit_order(order_no_3)  # draft → pending
            test_reject_order(order_no_3)  # pending → draft
            test_delete_draft_order(order_no_3)  # 删除草稿订单

        # 取消并删除
        test_cancel_order(order_no_1)  # audited → cancelled
    else:
        print("\n⏭ 跳过依赖创建订单的测试（创建订单失败）")

    # 边界条件测试
    test_get_detail_nonexistent()
    test_delete_nonexistent()

    if order_no_2:
        test_delete_non_draft_order(order_no_2)

    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
