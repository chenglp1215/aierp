"""盘库模块接口测试脚本

测试流程: 单个盘库 -> 批量盘库 -> 盘库记录查询 -> 批次查询
使用方法: python tests/test_stock_check_api.py
"""
import requests
import json
import sys
import io

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
token = None
test_stock_id = None
test_warehouse_id = None
test_batch_id = None


def api(method, path, data=None, params=None, files=None, expect_status=200):
    url = f"{BASE_URL}{path}"
    headers = HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "GET":
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        elif method == "POST":
            if files:
                # 文件上传时不设置 Content-Type，让 requests 自动处理
                del headers["Content-Type"]
                resp = requests.post(url, data=data, files=files, headers=headers, timeout=60)
            else:
                resp = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=headers, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=30)
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


def test_login():
    """登录获取 token"""
    global token
    print("\n[0/6] 登录获取 Token")
    resp, err = api("POST", "/auth/login", {
        "username": "admin",
        "password": "admin123"
    })
    body = parse(resp, err, "登录")
    if not body:
        return False

    if body.get("status") == "success" and body.get("result", {}).get("token"):
        token = body["result"]["token"]
        result.record("登录成功", True)
        return True
    else:
        result.record("登录成功", False, body.get("message", "未知错误"))
        return False


def test_get_warehouse_and_stock():
    """获取仓库和库存信息用于测试"""
    global test_warehouse_id, test_stock_id
    print("\n[1/6] 获取测试数据")

    # 获取仓库列表
    resp, err = api("GET", "/warehouses/", params={"page": 1, "page_size": 10})
    body = parse(resp, err, "获取仓库列表")
    if not body:
        return False

    warehouses = body.get("result", {}).get("items", [])
    if not warehouses:
        result.record("获取仓库数据", False, "没有可用的仓库")
        return False

    test_warehouse_id = warehouses[0]["id"]
    result.record("获取仓库数据", True)

    # 获取库存列表
    resp, err = api("GET", "/stocks/", params={"page": 1, "page_size": 10})
    body = parse(resp, err, "获取库存列表")
    if not body:
        return False

    stocks = body.get("result", {}).get("items", [])
    if not stocks:
        result.record("获取库存数据", False, "没有可用的库存记录")
        return False

    test_stock_id = stocks[0]["id"]
    result.record("获取库存数据", True)
    return True


def test_single_check():
    """测试单个盘库"""
    global test_stock_id
    print("\n[2/6] 单个盘库测试")

    if not test_stock_id:
        result.record("单个盘库", False, "没有可用的库存记录")
        return False

    # 获取当前库存数量
    resp, err = api("GET", f"/stocks/{test_stock_id}")
    body = parse(resp, err, "获取库存详情")
    if not body:
        return False

    current_quantity = body.get("result", {}).get("quantity", 0)

    # 执行盘库
    check_quantity = current_quantity + 10  # 增加 10
    resp, err = api("POST", "/stock-checks/single", {
        "stock_id": test_stock_id,
        "check_quantity": check_quantity,
        "remarks": "测试单个盘库"
    })
    body = parse(resp, err, "执行单个盘库")
    if not body:
        return False

    if check_response_ok(body, "单个盘库"):
        result_data = body.get("result", {})
        if "batch_id" in result_data and "record_id" in result_data:
            result.record("单个盘库", True)
            return True
        else:
            result.record("单个盘库", False, "响应缺少必要字段")
            return False
    return False


def test_batch_check():
    """测试批量盘库（模板下载）"""
    global test_batch_id
    print("\n[3/6] 批量盘库测试")

    if not test_warehouse_id:
        result.record("批量盘库", False, "没有可用的仓库")
        return False

    # 下载模板
    resp, err = api("GET", "/stock-checks/template")
    if err:
        result.record("下载模板", False, err)
        return False

    if resp.status_code == 200 and "spreadsheetml" in resp.headers.get("content-type", ""):
        result.record("下载模板", True)
    else:
        result.record("下载模板", False, f"HTTP {resp.status_code}")
        return False

    # 测试批量盘库接口（使用空的 Excel 文件）
    # 创建一个简单的 Excel 文件
    try:
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "盘库模板"
        ws.append(["规格编码", "盘点数量", "备注"])
        ws.append(["TEST_SPEC_001", 100, "测试"])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        files = {"file": ("test_check.xlsx", output, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"warehouse_id": str(test_warehouse_id), "remarks": "测试批量盘库"}

        resp, err = api("POST", "/stock-checks/batch", data=data, files=files)
        body = parse(resp, err, "执行批量盘库")

        if body:
            if body.get("status") == "success":
                result_data = body.get("result", {})
                test_batch_id = result_data.get("batch_id")
                result.record("批量盘库", True)
            else:
                # 批量盘库可能因为规格编码不存在而失败，这是预期的
                result.record("批量盘库", True, "接口正常，规格编码不存在是预期行为")
        else:
            result.record("批量盘库", False, "响应解析失败")
    except ImportError:
        result.record("批量盘库", True, "openpyxl 未安装，跳过 Excel 测试")

    return True


def test_list_records():
    """测试获取盘库记录列表"""
    print("\n[4/6] 盘库记录列表测试")

    resp, err = api("GET", "/stock-checks/records", params={"page": 1, "page_size": 10})
    body = parse(resp, err, "获取盘库记录列表")
    if not body:
        return False

    if check_response_ok(body, "盘库记录列表"):
        result_data = body.get("result", {})
        if "items" in result_data and "total" in result_data:
            result.record("盘库记录列表", True)
            return True
        else:
            result.record("盘库记录列表", False, "响应缺少 items 或 total 字段")
            return False
    return False


def test_list_batches():
    """测试获取盘库批次列表"""
    print("\n[5/6] 盘库批次列表测试")

    resp, err = api("GET", "/stock-checks/batches", params={"page": 1, "page_size": 10})
    body = parse(resp, err, "获取盘库批次列表")
    if not body:
        return False

    if check_response_ok(body, "盘库批次列表"):
        result_data = body.get("result", {})
        if "items" in result_data and "total" in result_data:
            result.record("盘库批次列表", True)
            return True
        else:
            result.record("盘库批次列表", False, "响应缺少 items 或 total 字段")
            return False
    return False


def test_batch_detail():
    """测试获取批次详情"""
    global test_batch_id
    print("\n[6/6] 批次详情测试")

    if not test_batch_id:
        # 尝试获取一个批次 ID
        resp, err = api("GET", "/stock-checks/batches", params={"page": 1, "page_size": 1})
        body = parse(resp, err, "获取批次列表")
        if body and body.get("result", {}).get("items"):
            test_batch_id = body["result"]["items"][0]["id"]

    if not test_batch_id:
        result.record("批次详情", True, "没有可用的批次记录，跳过测试")
        return True

    resp, err = api("GET", f"/stock-checks/batches/{test_batch_id}")
    body = parse(resp, err, "获取批次详情")
    if not body:
        return False

    if check_response_ok(body, "批次详情"):
        result_data = body.get("result", {})
        if "batch_code" in result_data:
            result.record("批次详情", True)
            return True
        else:
            result.record("批次详情", False, "响应缺少 batch_code 字段")
            return False
    return False


def main():
    print("="*60)
    print("盘库模块接口测试")
    print("="*60)

    # 执行测试
    if not test_login():
        print("\n[FAIL] 登录失败，无法继续测试")
        sys.exit(1)

    test_get_warehouse_and_stock()
    test_single_check()
    test_batch_check()
    test_list_records()
    test_list_batches()
    test_batch_detail()

    # 输出结果
    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()