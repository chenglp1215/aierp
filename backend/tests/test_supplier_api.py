"""
供应商管理 API 测试脚本 (MySQL 版本)
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"


def api(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if method == "GET":
        resp = requests.get(url, headers=headers, params=data)
    elif method == "POST":
        resp = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        resp = requests.put(url, headers=headers, json=data)
    elif method == "PATCH":
        resp = requests.patch(url, headers=headers, json=data)
    elif method == "DELETE":
        resp = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    try:
        return resp.json(), resp.status_code
    except:
        return {"text": resp.text}, resp.status_code


def test_login():
    print("=== 测试登录 ===")
    body, code = api("POST", "/auth/login", {"username": "admin", "password": "admin123"})
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"登录失败: {code}"
    assert body.get("status") == "success", f"登录失败: {body}"
    result = body.get("result", {})
    token = result.get("access_token")
    print(f"✅ 登录成功, token: {token[:50] if token else 'none'}...\n")
    return token


def test_list_suppliers(token):
    print("=== 测试获取供应商列表 ===")
    body, code = api("GET", "/suppliers/", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取供应商列表失败: {code}"
    assert "items" in body.get("result", {}), "无items字段"
    # 验证 ID 是整数类型
    items = body["result"].get("items", [])
    if items:
        assert isinstance(items[0].get("id"), int), "ID 应该是整数类型"
    print(f"✅ 获取供应商列表成功, 共{body['result'].get('total', 0)}条\n")
    return body["result"]


def test_get_all_suppliers(token):
    print("=== 测试获取所有供应商 ===")
    body, code = api("GET", "/suppliers/all", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取所有供应商失败: {code}"
    print(f"✅ 获取所有供应商成功\n")
    return body["result"]


def test_create_supplier(token, name, brand_id=None):
    print(f"=== 测试创建供应商: {name} ===")
    supplier_data = {
        "name": name,
        "contact_person": "张三",
        "contact_phone": "13800138000",
        "contact_email": "zhangsan@example.com",
        "address": "北京市朝阳区某某街道123号",
        "bank_account": {
            "bank_name": "中国工商银行",
            "account_name": name,
            "account_no": "6222021234567890123"
        },
        "supplied_brands": [],
        "remark": "优质供应商",
        "is_active": True
    }
    # 如果提供了品牌 ID，添加品牌关联
    if brand_id:
        supplier_data["supplied_brands"].append({
            "brand_id": brand_id,
            "discount": 0.95,
            "is_priority": True
        })

    body, code = api("POST", "/suppliers/", data=supplier_data, token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"创建供应商失败: {code}"
    supplier_id = body.get("result", {}).get("id")
    # 验证 ID 是整数类型
    assert isinstance(supplier_id, int), f"ID 应该是整数类型, 实际是: {type(supplier_id)}"
    print(f"✅ 创建供应商成功, id: {supplier_id}\n")
    return supplier_id


def test_create_duplicate_name_supplier(token, name):
    print(f"=== 测试创建重复名称供应商 ===")
    supplier_data = {"name": name}
    body, code = api("POST", "/suppliers/", data=supplier_data, token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"应该返回错误: {code}"
    assert body.get("status") == "error", f"应该是错误响应"
    print("✅ 重复名称校验正常\n")


def test_get_supplier_detail(token, supplier_id):
    print(f"=== 测试获取供应商详情: {supplier_id} ===")
    body, code = api("GET", f"/suppliers/{supplier_id}", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取供应商详情失败: {code}"
    # 验证 ID 是整数类型
    result_id = body.get("result", {}).get("id")
    assert isinstance(result_id, int), f"ID 应该是整数类型, 实际是: {type(result_id)}"
    print(f"✅ 获取供应商详情成功\n")
    return body["result"]


def test_get_nonexistent_supplier(token):
    print("=== 测试获取不存在的供应商 ===")
    body, code = api("GET", "/suppliers/999999", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"应该返回错误: {code}"
    assert body.get("status") == "error", f"应该是错误响应"
    print("✅ 不存在供应商校验正常\n")


def test_update_supplier(token, supplier_id):
    print(f"=== 测试更新供应商: {supplier_id} ===")
    update_data = {
        "contact_person": "李四",
        "contact_phone": "13900139000",
        "remark": "更新后的备注"
    }
    body, code = api("PUT", f"/suppliers/{supplier_id}", data=update_data, token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"更新供应商失败: {code}"
    print("✅ 更新供应商成功\n")


def test_toggle_supplier_active(token, supplier_id):
    print(f"=== 测试切换供应商激活状态: {supplier_id} ===")
    body, code = api("PATCH", f"/suppliers/{supplier_id}/toggle-active?is_active=false", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"切换激活状态失败: {code}"
    print("✅ 切换激活状态成功\n")

    body, code = api("PATCH", f"/suppliers/{supplier_id}/toggle-active?is_active=true", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"切换激活状态失败: {code}"
    print("✅ 激活供应商成功\n")


def test_delete_supplier(token, supplier_id):
    print(f"=== 测试删除供应商: {supplier_id} ===")
    body, code = api("DELETE", f"/suppliers/{supplier_id}", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"删除供应商失败: {code}"
    print("✅ 删除供应商成功\n")


def test_search_suppliers(token):
    print("=== 测试搜索供应商 ===")
    body, code = api("GET", "/suppliers/", token=token, data={"keyword": "测试", "is_active": True})
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"搜索供应商失败: {code}"
    print(f"✅ 搜索供应商成功\n")


def test_get_suppliers_by_brand(token, brand_id):
    print(f"=== 测试按品牌查询供应商: {brand_id} ===")
    body, code = api("GET", f"/suppliers/by-brand/{brand_id}", token=token)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"按品牌查询供应商失败: {code}"
    print(f"✅ 按品牌查询供应商成功\n")


def get_first_brand_id(token):
    """获取第一个品牌 ID 用于测试"""
    body, code = api("GET", "/brands/all", token=token)
    if code == 200 and body.get("result"):
        brands = body["result"]
        if brands:
            return brands[0].get("id")
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("开始供应商接口测试 (MySQL 版本)...")
    print("=" * 60)

    time.sleep(1)

    token = test_login()
    time.sleep(0.5)

    test_list_suppliers(token)
    time.sleep(0.5)

    test_get_all_suppliers(token)
    time.sleep(0.5)

    test_search_suppliers(token)
    time.sleep(0.5)

    # 获取品牌 ID 用于测试
    brand_id = get_first_brand_id(token)
    print(f"使用品牌 ID: {brand_id}")
    time.sleep(0.5)

    supplier_name = f"测试供应商_{int(time.time())}"
    supplier_id = test_create_supplier(token, supplier_name, brand_id)
    time.sleep(0.5)

    test_create_duplicate_name_supplier(token, supplier_name)
    time.sleep(0.5)

    test_get_supplier_detail(token, supplier_id)
    time.sleep(0.5)

    test_get_nonexistent_supplier(token)
    time.sleep(0.5)

    test_update_supplier(token, supplier_id)
    time.sleep(0.5)

    test_toggle_supplier_active(token, supplier_id)
    time.sleep(0.5)

    if brand_id:
        test_get_suppliers_by_brand(token, brand_id)
        time.sleep(0.5)

    test_delete_supplier(token, supplier_id)
    time.sleep(0.5)

    print("=" * 60)
    print("所有供应商接口测试通过! ✅")
    print("=" * 60)