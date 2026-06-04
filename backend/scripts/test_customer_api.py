"""
客户管理 - 接口测试脚本
测试所有客户管理 API 接口
"""
import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None
TEST_CUSTOMER_ID = None
HEADERS = {}

passed = 0
failed = 0
errors = []


OK_STR = "[OK]"
FAIL_STR = "[FAIL]"

def test(name: str, response: requests.Response, expected_status: int = 200):
    global passed, failed
    status_ok = response.status_code == expected_status
    try:
        data = response.json()
    except Exception:
        data = response.text

    if status_ok:
        passed += 1
        print(f"  {OK_STR} {name} (status={response.status_code})")
    else:
        failed += 1
        msg = f"  {FAIL_STR} {name} (expected={expected_status}, got={response.status_code}, body={data})"
        print(msg)
        errors.append(msg)
    return data


def login():
    global TOKEN, HEADERS
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "123456"
    })
    data = resp.json()
    TOKEN = data["result"]["access_token"]
    HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    print(f"登录成功, token={TOKEN[:20]}...")


# ===== 1. 客户 CRUD =====
def test_create_customer():
    global TEST_CUSTOMER_ID
    print("\n--- 创建客户 ---")
    resp = requests.post(f"{BASE_URL}/customers/", headers=HEADERS, json={
        "customer_code": f"TESTAPI{int(time.time()) % 100000}",
        "customer_name": "接口测试客户",
        "customer_type": "terminal",
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "province": "北京市",
        "city": "北京市",
        "district": "海淀区",
        "address": "中关村大街1号",
        "settlement_method": 1,
    })
    data = test("创建客户", resp)
    if resp.status_code == 200:
        TEST_CUSTOMER_ID = data.get("result", {}).get("id")
        print(f"  客户ID: {TEST_CUSTOMER_ID}")


def test_list_customers():
    print("\n--- 客户列表 ---")
    resp = requests.get(f"{BASE_URL}/customers/?page=1&page_size=5", headers=HEADERS)
    data = test("获取客户列表", resp)
    if resp.status_code == 200:
        result = data.get("result", {})
        print(f"  总数: {result.get('total', 0)}, 当前页: {len(result.get('items', []))}条")


def test_list_customers_with_filters():
    print("\n--- 客户列表（带筛选） ---")
    resp = requests.get(
        f"{BASE_URL}/customers/?page=1&page_size=5&customer_status=1&customer_type=terminal",
        headers=HEADERS
    )
    test("带状态筛选", resp)

    resp = requests.get(
        f"{BASE_URL}/customers/?page=1&page_size=5&keyword=测试",
        headers=HEADERS
    )
    test("带关键词搜索", resp)


def test_get_customer():
    print("\n--- 客户详情 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    resp = requests.get(f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}", headers=HEADERS)
    data = test("获取客户详情", resp)
    if resp.status_code == 200:
        customer = data.get("result", {})
        print(f"  名称: {customer.get('customer_name')}, 状态: {customer.get('customer_status')}")


def test_update_customer():
    print("\n--- 更新客户 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    resp = requests.put(
        f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}",
        headers=HEADERS,
        json={"customer_name": "接口测试客户-已更新", "contact_person": "李四"}
    )
    test("更新客户信息", resp)


def test_customer_stats():
    print("\n--- 客户统计 ---")
    resp = requests.get(f"{BASE_URL}/customers/stats", headers=HEADERS)
    data = test("获取客户统计", resp)
    if resp.status_code == 200:
        stats = data.get("result", {})
        print(f"  统计数据: {json.dumps(stats, ensure_ascii=False)}")


# ===== 2. 客户状态/认领 =====
def test_update_customer_status():
    print("\n--- 客户状态更新 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    # 设为公共池
    resp = requests.patch(
        f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}/status",
        headers=HEADERS,
        json={"customer_status": 2}
    )
    test("设为公共池", resp)

    # 认领回正常
    resp = requests.post(
        f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}/claim",
        headers=HEADERS
    )
    test("客户认领", resp)


# ===== 3. 会员注册 =====
def test_register_member():
    print("\n--- 会员注册 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    resp = requests.put(
        f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}/member-account",
        headers=HEADERS,
        json={"member_account": "VIP20240001"}
    )
    test("注册会员账号", resp)


# ===== 4. 订单默认值 =====
def test_set_order_defaults():
    print("\n--- 订单默认值 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    resp = requests.put(
        f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}/order-defaults",
        headers=HEADERS,
        json={
            "settlement_method": 2,
            "default_tax_rate": 13.00
        }
    )
    test("设置订单默认值", resp)


# ===== 5. 账期额度 =====
def test_set_credit():
    print("\n--- 账期额度 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    resp = requests.put(
        f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}/credit",
        headers=HEADERS,
        json={"credit_days": 30, "credit_limit": 50000.00}
    )
    test("设置账期额度", resp)


# ===== 6. 超账期检查 =====
def test_check_overdue():
    print("\n--- 超账期检查 ---")
    resp = requests.get(f"{BASE_URL}/customers/check-overdue", headers=HEADERS)
    test("批量超账期检查", resp)


# ===== 7. 客户转移 =====
def test_transfer_customer():
    print("\n--- 客户转移 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    # 获取用户列表找一个用户
    resp = requests.get(f"{BASE_URL}/users/?page=1&page_size=10", headers=HEADERS)
    data = resp.json()
    users = data.get("result", {}).get("items", [])
    if users and len(users) > 1:
        target_user_id = users[1].get("id")
        resp = requests.patch(
            f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}/transfer",
            headers=HEADERS,
            json={"new_user_id": target_user_id}
        )
        test("客户转移", resp)
    else:
        print("  SKIP: 没有可转移的目标用户")


# ===== 8. 导出 =====
def test_export_customers():
    print("\n--- 导出客户 ---")
    resp = requests.post(
        f"{BASE_URL}/customers/export",
        headers=HEADERS,
        json={"customer_ids": [TEST_CUSTOMER_ID] if TEST_CUSTOMER_ID else []}
    )
    is_ok = resp.status_code == 200 and (
        resp.headers.get("content-type", "").startswith("application/vnd.openxmlformats")
        or resp.headers.get("content-type", "").startswith("application/octet-stream")
    )
    if is_ok:
        global passed
        passed += 1
        print(f"  {OK_STR} 导出客户 (status=200, size={len(resp.content)} bytes)")
    else:
        global failed
        failed += 1
        print(f"  {FAIL_STR} 导出客户 (status={resp.status_code}, content-type={resp.headers.get('content-type', '')})")


# ===== 9. 删除客户 =====
def test_delete_customer():
    print("\n--- 删除客户 ---")
    if not TEST_CUSTOMER_ID:
        print("  SKIP: 无测试客户ID")
        return
    resp = requests.delete(f"{BASE_URL}/customers/{TEST_CUSTOMER_ID}", headers=HEADERS)
    test("删除客户", resp)


# ===== 10. 客户折扣 =====
def test_customer_discounts():
    print("\n--- 客户折扣 ---")
    # 创建折扣
    resp = requests.post(f"{BASE_URL}/customer-discounts/", headers=HEADERS, json={
        "customer_id": TEST_CUSTOMER_ID,
        "brand_id": 1,
        "brand_name": "测试品牌",
        "discount_value": 0.95
    })
    discount_data = test("创建客户折扣", resp)
    discount_id = None
    if resp.status_code == 200:
        discount_id = discount_data.get("result", {}).get("id")

    if discount_id:
        # 获取折扣列表
        resp = requests.get(
            f"{BASE_URL}/customer-discounts/?customer_id={TEST_CUSTOMER_ID}",
            headers=HEADERS
        )
        test("获取折扣列表", resp)

        # 更新折扣
        resp = requests.put(
            f"{BASE_URL}/customer-discounts/{discount_id}",
            headers=HEADERS,
            json={"discount_value": 0.90}
        )
        test("更新折扣", resp)

        # 切换折扣状态
        resp = requests.patch(
            f"{BASE_URL}/customer-discounts/{discount_id}/status?is_active=false",
            headers=HEADERS
        )
        test("切换折扣状态", resp)

        # 删除折扣
        resp = requests.delete(
            f"{BASE_URL}/customer-discounts/{discount_id}",
            headers=HEADERS
        )
        test("删除折扣", resp)


if __name__ == "__main__":
    print("=" * 60)
    print("客户管理接口测试")
    print("=" * 60)

    login()

    # CRUD
    test_create_customer()
    test_list_customers()
    test_list_customers_with_filters()
    test_get_customer()
    test_update_customer()
    test_customer_stats()

    # 新功能
    test_update_customer_status()
    test_register_member()
    test_set_order_defaults()
    test_set_credit()
    test_check_overdue()
    test_transfer_customer()
    test_export_customers()

    # 折扣
    test_customer_discounts()

    # 清理
    test_delete_customer()

    # 汇总
    print("\n" + "=" * 60)
    print(f"测试完成: {OK_STR} {passed} 通过, {FAIL_STR} {failed} 失败")
    if errors:
        print("\n失败详情:")
        for e in errors:
            print(e)
    print("=" * 60)

    sys.exit(1 if failed > 0 else 0)
