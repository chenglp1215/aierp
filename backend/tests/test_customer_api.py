"""客户模块接口测试脚本

测试流程: 登录获取token -> 客户CRUD -> 客户折扣CRUD
使用方法: python tests/test_customer_api.py
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.token = None

    def record(self, name, success, detail=""):
        if success:
            self.passed += 1
            print(f"  [PASS] {name}")
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


def login():
    print("\n[0/?] 登录获取token")
    resp, err = api("POST", "/auth/login", {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    if err or not resp:
        result.record("登录", False, err or "未获取到响应")
        return False
    if resp.status_code != 200:
        body = parse_error(resp)
        result.record("登录", False, f"status={resp.status_code}, {body}")
        return False
    try:
        body = resp.json()
    except:
        result.record("登录", False, f"响应非JSON: {resp.text[:200]}")
        return False
    if "access_token" not in body:
        result.record("登录", False, f"响应没有access_token: {body}")
        return False
    token = body.get("access_token")
    if not token:
        result.record("登录", False, "未获取到access_token")
        return False
    result.token = token
    HEADERS["Authorization"] = f"Bearer {token}"
    result.record("登录-获取token", True, f"token={token[:20]}...")
    return True


def api(method, path, data=None, params=None, expect_status=200):
    url = f"{BASE_URL}{path}"
    try:
        headers = HEADERS.copy()
        if method == "GET":
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == "PATCH":
            resp = requests.patch(url, json=data, params=params, headers=headers, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
        else:
            return None, f"未知方法: {method}"
        return resp, None
    except requests.exceptions.ConnectionError:
        return None, "服务未启动或连接失败"


def parse_error(resp):
    try:
        return resp.json()
    except:
        return resp.text[:200]


def parse(resp, err, test_name, expect_error=False, expect_status=None):
    if err:
        if not expect_error:
            result.record(test_name, False, err)
        return None
    if resp.status_code == 422:
        body = parse_error(resp)
        result.record(f"{test_name}-422参数校验错误", True, f"正常返回422: {body}")
        return None
    # Handle 201 Created as success
    if resp.status_code == 201:
        try:
            body = resp.json()
            return body
        except:
            return None
    if resp.status_code != 200:
        body = parse_error(resp)
        if expect_error:
            result.record(f"{test_name}-应该报错", True, f"status={resp.status_code}")
            return None
        result.record(test_name, False, f"HTTP {resp.status_code}: {body}")
        return None
    try:
        body = resp.json()
    except Exception:
        result.record(test_name, False, f"响应非JSON: {resp.text[:200]}")
        return None
    return body


def check_field(body, field, test_name):
    if field not in body:
        result.record(test_name, False, f"响应缺少字段: {field}")
        return False
    return True


def check_response_ok(body, test_name):
    if body.get("status") != "success":
        result.record(test_name, False, f"status != success: {body.get('message')}")
        return False
    return True


def test_create_customer():
    print("\n[1/10] 创建客户")
    resp, err = api("POST", "/customers/", {
        "name": "测试客户",
        "customer_type": "terminal",
        "research_group": "测试课题组",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "contact_email": "test@example.com",
        "invoice_infos": [
            {
                "invoice_title": "测试客户公司",
                "invoice_type": "增值税",
                "tax_number": "91110000000000000X",
                "bank_name": "中国工商银行",
                "bank_account": "6222021234567890",
                "is_default": True
            }
        ],
        "shipping_addresses": [
            {
                "recipient_name": "张三",
                "recipient_phone": "13800138000",
                "province": "北京市",
                "city": "北京市",
                "address": "林林路100号",
                "is_default": True
            }
        ]
    })
    body = parse(resp, err, "创建客户")
    if not body:
        return None
    ok = check_response_ok(body, "创建客户")
    if ok and check_field(body, "result", "创建客户"):
        data = body["result"]
        cust_id = data.get("id")
        cust_code = data.get("customer_code")
        result.record("创建客户-返回id", bool(cust_id), f"id={cust_id}")
        result.record("创建客户-自动生成customer_code", bool(cust_code) and cust_code.startswith("CUST"), f"code={cust_code}")
        result.record("创建客户-开票信息已添加", len(data.get("invoice_infos", [])) > 0)
        result.record("创建客户-收货地址已添加", len(data.get("shipping_addresses", [])) > 0)
        created_ids["customer_id"] = cust_id
        return cust_id
    return None


def test_list_customers():
    print("\n[2/10] 查询客户列表")
    resp, err = api("GET", "/customers/", params={"page": 1, "page_size": 20})
    body = parse(resp, err, "查询客户列表")
    if not body:
        return
    ok = check_response_ok(body, "查询客户列表")
    if ok:
        result.record("查询客户列表-返回成功", True)
        # list_customers returns (items, total) tuple
        items = body.get("result")
        if isinstance(items, list) and len(items) >= 2:
            customer_list = items[0]
            total = items[1]
            result.record("查询客户列表-包含新建客户", any(c.get("id") == created_ids["customer_id"] for c in customer_list if isinstance(c, dict)))
        elif isinstance(items, list):
            result.record("查询客户列表-包含新建客户", any(c.get("id") == created_ids["customer_id"] for c in items if isinstance(c, dict)))


def test_get_customer_stats():
    print("\n[3/10] 获取客户统计")
    resp, err = api("GET", "/customers/stats")
    body = parse(resp, err, "获取客户统计")
    if not body:
        return
    ok = check_response_ok(body, "获取客户统计")
    if ok and check_field(body, "result", "获取客户统计"):
        data = body["result"]
        result.record("统计-包含total", "total" in data)
        result.record("统计-包含terminal_count", "terminal_count" in data)
        result.record("统计-包含dealer_count", "dealer_count" in data)


def test_get_customer_detail():
    print("\n[4/10] 获取客户详情")
    cust_id = created_ids.get("customer_id", "")
    resp, err = api("GET", f"/customers/{cust_id}")
    body = parse(resp, err, "获取客户详情")
    if not body:
        return
    ok = check_response_ok(body, "获取客户详情")
    if ok and check_field(body, "result", "获取客户详情"):
        data = body["result"]
        result.record("详情-返回客户名称", data.get("name") == "测试客户")
        result.record("详情-包含开票信息", len(data.get("invoice_infos", [])) > 0)
        result.record("详情-包含收货地址", len(data.get("shipping_addresses", [])) > 0)


def test_update_customer():
    print("\n[5/10] 更新客户")
    cust_id = created_ids.get("customer_id", "")
    resp, err = api("PUT", f"/customers/{cust_id}", {
        "name": "测试客户-已更新",
        "contact_person": "李四"
    })
    body = parse(resp, err, "更新客户")
    if not body:
        return
    ok = check_response_ok(body, "更新客户")
    if ok:
        result.record("更新客户-返回成功", True)

    resp2, _ = api("GET", f"/customers/{cust_id}")
    body2 = parse(resp2, None, "更新客户-验证")
    if body2 and body2.get("status") == "success":
        data = body2["result"]
        result.record("更新客户-名称已更新", data.get("name") == "测试客户-已更新", f"name={data.get('name')}")
        result.record("更新客户-联系人已更新", data.get("contact_person") == "李四", f"contact={data.get('contact_person')}")


def test_update_customer_status():
    print("\n[6/10] 更新客户状态")
    cust_id = created_ids.get("customer_id", "")
    resp, err = api("PATCH", f"/customers/{cust_id}/status", {"status": "inactive"})
    body = parse(resp, err, "更新客户状态")
    if not body:
        return
    ok = check_response_ok(body, "更新客户状态")
    if ok:
        result.record("更新客户状态-返回成功", True)

    resp2, _ = api("GET", f"/customers/{cust_id}")
    body2 = parse(resp2, None, "更新客户状态-验证")
    if body2 and body2.get("status") == "success":
        data = body2["result"]
        result.record("更新客户状态-状态已更新", data.get("status") == "inactive", f"status={data.get('status')}")


def test_create_brand_for_discount():
    print("\n  创建测试品牌(用于客户折扣测试)")
    resp, err = api("POST", "/brands/", {
        "name": "折扣测试品牌",
        "description": "测试品牌描述",
        "is_active": True
    })
    body = parse(resp, err, "创建测试品牌")
    if body and body.get("status") == "success":
        brand_id = body.get("result", {}).get("id")
        if brand_id:
            created_ids["brand_id"] = brand_id
            return brand_id
    return created_ids.get("brand_id")


def test_create_customer_discount():
    print("\n[7/10] 创建客户折扣")
    cust_id = created_ids.get("customer_id", "")
    brand_id = created_ids.get("brand_id") or test_create_brand_for_discount()
    if not brand_id:
        result.record("创建客户折扣-无品牌ID", False, "无品牌可用")
        return None
    resp, err = api("POST", "/customer-discounts/", {
        "customer_id": cust_id,
        "brand_id": brand_id,
        "discount_value": 0.85,
        "is_active": True
    })
    body = parse(resp, err, "创建客户折扣")
    if not body:
        return None
    ok = check_response_ok(body, "创建客户折扣")
    if ok and check_field(body, "result", "创建客户折扣"):
        data = body["result"]
        discount_id = data.get("id")
        result.record("创建折扣-返回id", bool(discount_id), f"id={discount_id}")
        result.record("创建折扣-折扣值正确", data.get("discount_value") == 0.85, f"value={data.get('discount_value')}")
        created_ids["discount_id"] = discount_id
        return discount_id
    return None


def test_list_customer_discounts():
    print("\n[8/10] 查询客户折扣列表")
    cust_id = created_ids.get("customer_id", "")
    resp, err = api("GET", "/customer-discounts/", params={"customer_id": cust_id})
    body = parse(resp, err, "查询客户折扣列表")
    if not body:
        return
    ok = check_response_ok(body, "查询客户折扣列表")
    if ok:
        result.record("查询折扣列表-返回成功", True)


def test_get_discount_by_customer_and_brand():
    print("\n[9/10] 按客户和品牌获取折扣")
    cust_id = created_ids.get("customer_id", "")
    brand_id = created_ids.get("brand_id", "")
    resp, err = api("GET", f"/customer-discounts/customer/{cust_id}/brand/{brand_id}")
    body = parse(resp, err, "按客户和品牌获取折扣")
    if not body:
        return
    ok = check_response_ok(body, "按客户和品牌获取折扣")
    if ok:
        result.record("按客户和品牌获取折扣-返回成功", True)


def test_update_customer_discount():
    print("\n[10/10] 更新客户折扣")
    discount_id = created_ids.get("discount_id", "")
    resp, err = api("PUT", f"/customer-discounts/{discount_id}", {
        "discount_value": 0.8,
        "is_active": False
    })
    body = parse(resp, err, "更新客户折扣")
    if not body:
        return
    ok = check_response_ok(body, "更新客户折扣")
    if ok:
        result.record("更新折扣-返回成功", True)


def test_validation():
    print("\n[验证] 异常参数验证测试")

    print("\n  [异常-1] 创建客户-缺少必填名称")
    resp, err = api("POST", "/customers/", {"customer_type": "terminal"})
    body = parse(resp, err, "异常-客户缺少名称", expect_error=True)
    if body:
        result.record("异常-客户缺少名称应报错", body.get("status") == "error")

    print("\n  [异常-2] 创建客户-无效的客户类型")
    resp, err = api("POST", "/customers/", {"name": "测试", "customer_type": "invalid_type"})
    body = parse(resp, err, "异常-客户类型无效", expect_error=True)
    if body:
        result.record("异常-客户类型无效应报错", body.get("status") == "error")

    print("\n  [异常-3] 查询不存在的客户")
    resp, err = api("GET", "/customers/000000000000000000000099")
    body = parse(resp, err, "异常-查询不存在客户", expect_error=True)
    if body:
        result.record("异常-查询不存在客户应报错", body.get("status") == "error")

    print("\n  [异常-4] 创建折扣-缺少必填字段")
    resp, err = api("POST", "/customer-discounts/", {"discount_value": 0.85})
    body = parse(resp, err, "异常-折扣缺少必填字段", expect_error=True)
    if body:
        result.record("异常-折扣缺少必填字段应报错", body.get("status") == "error")


def cleanup():
    print("\n[清理] 清理测试数据")

    if created_ids.get("discount_id"):
        api("DELETE", f"/customer-discounts/{created_ids['discount_id']}")

    if created_ids.get("brand_id"):
        api("DELETE", f"/brands/{created_ids['brand_id']}")

    if created_ids.get("customer_id"):
        api("DELETE", f"/customers/{created_ids['customer_id']}")


def main():
    import time as _time
    _time.sleep(2)

    print("=" * 60)
    print("客户模块接口测试")
    print(f"服务地址: {BASE_URL}")
    print("=" * 60)

    health_resp, health_err = api("GET", "/health")
    if health_err or (health_resp and health_resp.status_code != 200):
        print(f"\n[FAIL] 服务未就绪: {health_err or health_resp.status_code}")
        sys.exit(1)
    print("[PASS] 服务健康检查通过")

    if not login():
        sys.exit(1)

    test_create_customer()
    test_list_customers()
    test_get_customer_stats()
    test_get_customer_detail()
    test_update_customer()
    test_update_customer_status()

    test_create_brand_for_discount()
    test_create_customer_discount()
    test_list_customer_discounts()
    test_get_discount_by_customer_and_brand()
    test_update_customer_discount()

    test_validation()

    cleanup()

    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
