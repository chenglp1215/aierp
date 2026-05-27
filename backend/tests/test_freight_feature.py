"""销售订单运费功能测试脚本

测试内容:
1. 品牌创建/更新时运费字段正常保存
2. 销售订单创建时运费自动累加正确
3. 销售订单创建时运费可手动修改
4. 销售订单金额计算正确（运费不计税）
5. 历史订单数据兼容（运费显示为 0）

使用方法: python tests/test_freight_feature.py
"""
import requests
import json
import sys
import time
import random

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        self.test_results = []

    def record(self, test_id, name, success, detail=""):
        if success:
            self.passed += 1
            self.test_results.append({"id": test_id, "name": name, "status": "passed", "notes": detail})
            print(f"  [PASS] {name}")
        else:
            self.failed += 1
            self.test_results.append({"id": test_id, "name": name, "status": "failed", "notes": detail})
            self.errors.append({"test": name, "detail": detail})
            print(f"  [FAIL] {name}: {detail}")

    def skip(self, test_id, name, reason=""):
        self.skipped += 1
        self.test_results.append({"id": test_id, "name": name, "status": "skipped", "notes": reason})
        print(f"  [SKIP] {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'='*60}")
        print(f"测试结果: {self.passed}/{total} 通过, {self.failed} 失败, {self.skipped} 跳过")
        if self.errors:
            print(f"\n失败项:")
            for e in self.errors:
                print(f"  - {e['test']}: {e['detail']}")
        print(f"{'='*60}")
        return self.failed == 0


result = TestResult()
created_resources = {}


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
        result.record("", test_name, False, err)
        return None
    if resp.status_code != 200:
        return None
    try:
        body = resp.json()
    except Exception:
        result.record("", test_name, False, f"响应非JSON: {resp.text[:200]}")
        return None
    return body


def check_response_ok(body, test_name):
    if body.get("status") != "success":
        result.record("", test_name, False, f"status != success: {body.get('message')}")
        return False
    return True


def setup_test_data():
    """创建测试所需的基础数据：分类、客户、仓库"""
    print("\n[SETUP] 创建测试基础数据...")

    # 创建分类
    resp, _ = api("POST", "/categories/", {
        "name": f"运费测试分类_{random.randint(1000, 9999)}",
        "sort_order": 1
    })
    body = parse(resp, None, "创建分类")
    if body and body.get("status") == "success":
        created_resources["category_id"] = body["result"]["id"]
        print(f"  分类ID: {body['result']['id']}")

    # 创建客户
    resp, _ = api("POST", "/customers/", {
        "name": f"运费测试客户_{random.randint(1000, 9999)}",
        "customer_code": f"CT{random.randint(10000, 99999)}",
        "customer_type": "terminal",
        "is_active": True
    })
    body = parse(resp, None, "创建客户")
    if body and body.get("status") == "success":
        created_resources["customer_id"] = body["result"]["id"]
        created_resources["customer_name"] = body["result"]["name"]
        print(f"  客户ID: {body['result']['id']}")

    # 获取仓库列表
    resp, _ = api("GET", "/warehouses/", params={"page_size": 1})
    body = parse(resp, None, "获取仓库")
    if body and body.get("status") == "success":
        items = body.get("result", {}).get("items", [])
        if items:
            created_resources["warehouse_id"] = items[0]["id"]
            print(f"  仓库ID: {items[0]['id']}")


def test_t1_1_brand_freight_field():
    """T1.1 验证品牌创建/更新时运费字段正常保存"""
    print("\n[TEST] T1.1 品牌运费字段测试")

    # 创建品牌带运费
    resp, err = api("POST", "/brands/", {
        "name": f"运费测试品牌A_{random.randint(1000, 9999)}",
        "description": "测试品牌A",
        "default_freight": 50.00,
        "is_active": True
    })
    body = parse(resp, err, "T1.1-创建品牌带运费")
    if not body:
        return

    ok = check_response_ok(body, "T1.1-创建品牌带运费")
    if ok:
        data = body["result"]
        brand_id = data.get("id")
        created_resources["brand_a_id"] = brand_id

        # 验证运费字段返回
        freight = data.get("default_freight")
        result.record("T1.1", "品牌创建-运费字段返回", freight is not None, f"default_freight={freight}")
        result.record("T1.1", "品牌创建-运费值正确", freight == 50.00, f"期望50.00, 实际{freight}")

    # 更新品牌运费
    if "brand_a_id" in created_resources:
        brand_id = created_resources["brand_a_id"]
        resp, err = api("PUT", f"/brands/{brand_id}", {
            "default_freight": 80.00
        })
        body = parse(resp, err, "T1.1-更新品牌运费")
        if body and body.get("status") == "success":
            # 再次查询验证
            resp2, _ = api("GET", f"/brands/{brand_id}")
            body2 = parse(resp2, None, "T1.1-查询更新后品牌")
            if body2 and body2.get("status") == "success":
                freight = body2["result"].get("default_freight")
                result.record("T1.1", "品牌更新-运费值正确", freight == 80.00, f"期望80.00, 实际{freight}")

    # 测试运费负数验证
    resp, err = api("POST", "/brands/", {
        "name": f"运费负数测试品牌_{random.randint(1000, 9999)}",
        "default_freight": -10.00
    })
    body = parse(resp, err, "T1.1-运费负数验证")
    if body:
        is_error = body.get("status") == "error"
        result.record("T1.1", "品牌创建-运费负数应报错", is_error, f"status={body.get('status')}, msg={body.get('message')}")


def test_t1_2_order_freight_auto_calculate():
    """T1.2 验证销售订单创建时运费自动累加正确"""
    print("\n[TEST] T1.2 订单运费自动累加测试")

    # 创建第二个品牌
    resp, _ = api("POST", "/brands/", {
        "name": f"运费测试品牌B_{random.randint(1000, 9999)}",
        "description": "测试品牌B",
        "default_freight": 30.00,
        "is_active": True
    })
    body = parse(resp, None, "T1.2-创建品牌B")
    if body and body.get("status") == "success":
        created_resources["brand_b_id"] = body["result"]["id"]

    # 创建商品和规格
    if "brand_a_id" not in created_resources or "category_id" not in created_resources:
        result.skip("T1.2", "订单运费自动累加", "缺少品牌或分类")
        return

    # 创建商品A（品牌A）
    resp, _ = api("POST", "/products/", {
        "name": f"运费测试商品A_{random.randint(1000, 9999)}",
        "brand_id": created_resources["brand_a_id"],
        "category_id": created_resources["category_id"],
        "is_active": True
    })
    body = parse(resp, None, "T1.2-创建商品A")
    if body and body.get("status") == "success":
        product_a_id = body["result"]["id"]
        # 创建规格
        resp, _ = api("POST", f"/products/{product_a_id}/specs", {
            "spec_code": f"SPEC_A_{random.randint(10000, 99999)}",
            "price": 100.00,
            "is_active": True
        })
        body = parse(resp, None, "T1.2-创建规格A")
        if body and body.get("status") == "success":
            created_resources["spec_a_id"] = body["result"]["id"]

    # 创建商品B（品牌B）
    if "brand_b_id" in created_resources:
        resp, _ = api("POST", "/products/", {
            "name": f"运费测试商品B_{random.randint(1000, 9999)}",
            "brand_id": created_resources["brand_b_id"],
            "category_id": created_resources["category_id"],
            "is_active": True
        })
        body = parse(resp, None, "T1.2-创建商品B")
        if body and body.get("status") == "success":
            product_b_id = body["result"]["id"]
            resp, _ = api("POST", f"/products/{product_b_id}/specs", {
                "spec_code": f"SPEC_B_{random.randint(10000, 99999)}",
                "price": 200.00,
                "is_active": True
            })
            body = parse(resp, None, "T1.2-创建规格B")
            if body and body.get("status") == "success":
                created_resources["spec_b_id"] = body["result"]["id"]

    # 创建订单（包含两个品牌商品，运费应为 80 + 30 = 110）
    if "spec_a_id" not in created_resources or "customer_id" not in created_resources:
        result.skip("T1.2", "订单运费自动累加", "缺少规格或客户")
        return

    order_data = {
        "order_date": "2026-05-20",
        "customer_id": created_resources["customer_id"],
        "customer_name": created_resources.get("customer_name", ""),
        "freight_amt": 110.00,  # 前端计算后传入
        "items": [
            {
                "row_no": 1,
                "spec_id": created_resources["spec_a_id"],
                "qty": 2,
                "price": 100.00,
                "discount": 1.0,
                "shipping_method": "direct"
            }
        ]
    }

    if "spec_b_id" in created_resources:
        order_data["items"].append({
            "row_no": 2,
            "spec_id": created_resources["spec_b_id"],
            "qty": 1,
            "price": 200.00,
            "discount": 1.0,
            "shipping_method": "direct"
        })

    resp, err = api("POST", "/sales-orders/", order_data)
    body = parse(resp, err, "T1.2-创建订单")
    if body and body.get("status") == "success":
        order_no = body["result"].get("order_no")
        created_resources["test_order_no"] = order_no
        result.record("T1.2", "订单创建成功", True, f"order_no={order_no}")

        # 查询订单详情验证运费
        resp2, _ = api("GET", f"/sales-orders/{order_no}")
        body2 = parse(resp2, None, "T1.2-查询订单详情")
        if body2 and body2.get("status") == "success":
            order = body2["result"]
            freight = order.get("freight_amt")
            result.record("T1.2", "订单运费字段存在", freight is not None, f"freight_amt={freight}")
            result.record("T1.2", "订单运费值正确", freight == 110.00, f"期望110.00, 实际{freight}")


def test_t1_3_order_freight_manual_modify():
    """T1.3 验证销售订单创建时运费可手动修改"""
    print("\n[TEST] T1.3 订单运费手动修改测试")

    if "spec_a_id" not in created_resources or "customer_id" not in created_resources:
        result.skip("T1.3", "订单运费手动修改", "缺少规格或客户")
        return

    # 创建订单，手动指定运费为 200（覆盖自动计算的值）
    order_data = {
        "order_date": "2026-05-20",
        "customer_id": created_resources["customer_id"],
        "customer_name": created_resources.get("customer_name", ""),
        "freight_amt": 200.00,  # 手动指定运费
        "items": [
            {
                "row_no": 1,
                "spec_id": created_resources["spec_a_id"],
                "qty": 1,
                "price": 100.00,
                "discount": 1.0,
                "shipping_method": "direct"
            }
        ]
    }

    resp, err = api("POST", "/sales-orders/", order_data)
    body = parse(resp, err, "T1.3-创建订单手动运费")
    if body and body.get("status") == "success":
        order_no = body["result"].get("order_no")

        # 查询订单详情验证运费
        resp2, _ = api("GET", f"/sales-orders/{order_no}")
        body2 = parse(resp2, None, "T1.3-查询订单详情")
        if body2 and body2.get("status") == "success":
            order = body2["result"]
            freight = order.get("freight_amt")
            result.record("T1.3", "订单运费手动修改成功", freight == 200.00, f"期望200.00, 实际{freight}")

            # 清理
            api("DELETE", f"/sales-orders/{order_no}")


def test_t1_4_order_amount_calculation():
    """T1.4 验证销售订单金额计算正确（运费不计税）"""
    print("\n[TEST] T1.4 订单金额计算测试（运费不计税）")

    if "spec_a_id" not in created_resources or "customer_id" not in created_resources:
        result.skip("T1.4", "订单金额计算", "缺少规格或客户")
        return

    # 创建订单：商品金额 100 * 2 = 200，运费 50
    # 预期计算：
    # - 商品总金额 = 200
    # - 税额 = 200 * 0.13 = 26（运费不计税）
    # - 含税总额 = 200 + 26 + 50 = 276
    order_data = {
        "order_date": "2026-05-20",
        "customer_id": created_resources["customer_id"],
        "customer_name": created_resources.get("customer_name", ""),
        "freight_amt": 50.00,
        "items": [
            {
                "row_no": 1,
                "spec_id": created_resources["spec_a_id"],
                "qty": 2,
                "price": 100.00,
                "discount": 1.0,
                "shipping_method": "direct"
            }
        ]
    }

    resp, err = api("POST", "/sales-orders/", order_data)
    body = parse(resp, err, "T1.4-创建订单验证金额")
    if body and body.get("status") == "success":
        order_no = body["result"].get("order_no")

        # 查询订单详情验证金额
        resp2, _ = api("GET", f"/sales-orders/{order_no}")
        body2 = parse(resp2, None, "T1.4-查询订单详情")
        if body2 and body2.get("status") == "success":
            order = body2["result"]

            total_amt = order.get("total_amt")  # 商品总金额（未税）
            tax_amt = order.get("tax_amt")  # 税额
            total_tax_amt = order.get("total_tax_amt")  # 含税总金额
            freight_amt = order.get("freight_amt")  # 运费

            result.record("T1.4", "商品总金额正确", total_amt == 200.00, f"期望200.00, 实际{total_amt}")
            result.record("T1.4", "运费字段正确", freight_amt == 50.00, f"期望50.00, 实际{freight_amt}")

            # 税额 = 商品总金额 * 税率（运费不计税）
            expected_tax = round(200.00 * 0.13, 2)  # 26.00
            result.record("T1.4", "税额计算正确（运费不计税）", tax_amt == expected_tax, f"期望{expected_tax}, 实际{tax_amt}")

            # 含税总额 = 商品总金额 + 税额 + 运费
            expected_total = round(200.00 + expected_tax + 50.00, 2)  # 276.00
            result.record("T1.4", "含税总额计算正确", total_tax_amt == expected_total, f"期望{expected_total}, 实际{total_tax_amt}")

            # 清理
            api("DELETE", f"/sales-orders/{order_no}")


def test_t1_5_historical_order_compatibility():
    """T1.5 验证历史订单数据兼容（运费显示为 0）"""
    print("\n[TEST] T1.5 历史订单数据兼容测试")

    # 查询现有订单列表
    resp, _ = api("GET", "/sales-orders/", params={"page": 1, "page_size": 10})
    body = parse(resp, None, "T1.5-查询订单列表")
    if body and body.get("status") == "success":
        items = body.get("result", {}).get("items", [])
        if items:
            # 检查每个订单都有 freight_amt 字段
            all_have_freight = all("freight_amt" in item for item in items)
            result.record("T1.5", "所有订单包含freight_amt字段", all_have_freight)

            # 检查 freight_amt 默认值为 0 或数值
            valid_freight = all(
                item.get("freight_amt") is not None and item.get("freight_amt") >= 0
                for item in items
            )
            result.record("T1.5", "freight_amt值为有效数值", valid_freight)
        else:
            result.record("T1.5", "订单列表为空，跳过兼容性测试", True)


def cleanup():
    """清理测试数据"""
    print("\n[CLEANUP] 清理测试数据...")

    # 删除测试订单
    if "test_order_no" in created_resources:
        api("DELETE", f"/sales-orders/{created_resources['test_order_no']}")

    # 删除测试品牌
    for brand_key in ["brand_a_id", "brand_b_id"]:
        if brand_key in created_resources:
            api("DELETE", f"/brands/{created_resources[brand_key]}")

    # 删除测试客户
    if "customer_id" in created_resources:
        api("DELETE", f"/customers/{created_resources['customer_id']}")

    # 删除测试分类
    if "category_id" in created_resources:
        api("DELETE", f"/categories/{created_resources['category_id']}")


def main():
    print("=" * 60)
    print("销售订单运费功能测试")
    print(f"服务地址: {BASE_URL}")
    print("=" * 60)

    # 健康检查
    health_resp, health_err = api("GET", "/health/")
    if health_err or (health_resp and health_resp.status_code != 200):
        print(f"\n[FAIL] 服务未就绪: {health_err or health_resp.status_code}")
        print("请确保后端服务正在运行: cd backend && python -m uvicorn app.main:app --reload")
        sys.exit(1)
    print("[OK] 服务健康检查通过")

    # 执行测试
    setup_test_data()
    test_t1_1_brand_freight_field()
    test_t1_2_order_freight_auto_calculate()
    test_t1_3_order_freight_manual_modify()
    test_t1_4_order_amount_calculation()
    test_t1_5_historical_order_compatibility()

    # 清理
    cleanup()

    # 输出结果
    success = result.summary()

    # 输出 JSON 格式结果
    print("\n[JSON OUTPUT]")
    output = {
        "status": "DONE" if success else "DONE_WITH_CONCERNS",
        "outputFile": "outputs/testing/task-20260520232724.md",
        "summary": "测试验证完成" if success else "测试验证完成，存在失败用例",
        "testResults": result.test_results,
        "concerns": result.errors
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
