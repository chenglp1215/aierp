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
    print(f"✅ 登录成功, token: {token[:50] if token else 'None'}...\n")
    return token


def test_get_me():
    print("=== 测试获取当前用户 ===")
    body, code = api("GET", "/auth/me")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:300]}")
    assert code == 200, f"获取当前用户失败: {code}"
    print("✅ 获取当前用户成功\n")


def test_list_users():
    print("=== 测试用户列表 ===")
    body, code = api("GET", "/auth/users/")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取用户列表失败: {code}"
    assert "items" in body.get("result", {}), "无items字段"
    print(f"✅ 获取用户列表成功, 共{body['result'].get('total', 0)}条\n")
    return body["result"]


def test_list_roles():
    print("=== 测试角色列表 ===")
    body, code = api("GET", "/auth/roles/")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取角色列表失败: {code}"
    print(f"✅ 获取角色列表成功, 共{body['result'].get('total', 0)}条\n")
    return body["result"]


def test_list_permissions():
    print("=== 测试权限列表 ===")
    body, code = api("GET", "/auth/permissions/")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取权限列表失败: {code}"
    print(f"✅ 获取权限列表成功, 共{body['result'].get('total', 0)}条\n")


def test_permission_tree():
    print("=== 测试权限树 ===")
    body, code = api("GET", "/auth/permissions/tree")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:500]}")
    assert code == 200, f"获取权限树失败: {code}"
    print("✅ 获取权限树成功\n")


def test_create_role():
    print("=== 测试创建角色 ===")
    role_data = {
        "code": "test_role_refactor",
        "name": "测试角色-重构",
        "description": "接口测试创建的角色",
        "permission_ids": []
    }
    body, code = api("POST", "/auth/roles/", data=role_data)
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"创建角色失败: {code}"
    role_id = body.get("result", {}).get("id")
    print(f"✅ 创建角色成功, id: {role_id}\n")
    return role_id


def test_update_role(role_id):
    print("=== 测试更新角色 ===")
    body, code = api("PUT", f"/auth/roles/{role_id}/", data={"name": "测试角色-已更新"})
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"更新角色失败: {code}"
    print("✅ 更新角色成功\n")


def test_delete_role(role_id):
    print("=== 测试删除角色 ===")
    body, code = api("DELETE", f"/auth/roles/{role_id}/")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 200, f"删除角色失败: {code}"
    print("✅ 删除角色成功\n")


def test_get_user_detail(user_id):
    print("=== 测试获取用户详情 ===")
    body, code = api("GET", f"/auth/users/{user_id}/")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:300]}")
    assert code == 200, f"获取用户详情失败: {code}"
    print("✅ 获取用户详情成功\n")


def test_get_role_detail(role_id):
    print("=== 测试获取角色详情 ===")
    body, code = api("GET", f"/auth/roles/{role_id}/")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)[:300]}")
    assert code == 200, f"获取角色详情失败: {code}"
    print("✅ 获取角色详情成功\n")


def test_fixed_role_protection(roles_result):
    print("=== 测试固化角色保护 ===")
    fixed_role = None
    for role in roles_result.get("items", []):
        if role.get("is_fixed"):
            fixed_role = role
            break

    if not fixed_role:
        print("⚠️ 未找到固化角色，跳过测试\n")
        return

    body, code = api("DELETE", f"/auth/roles/{fixed_role['id']}/")
    print(f"状态码: {code}, 响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
    assert code == 400, f"固化角色删除应该被拒绝: {code}, 响应: {body}"
    assert body.get("status") == "error", f"应该是错误响应"
    print("✅ 固化角色保护正常\n")


if __name__ == "__main__":
    print("=" * 60)
    print("开始接口测试...")
    print("=" * 60)

    time.sleep(3)

    test_login()
    time.sleep(0.5)

    test_get_me()
    time.sleep(0.5)

    users_result = test_list_users()
    time.sleep(0.5)

    roles_result = test_list_roles()
    time.sleep(0.5)

    test_list_permissions()
    time.sleep(0.5)

    test_permission_tree()
    time.sleep(0.5)

    role_id = test_create_role()
    time.sleep(0.5)

    test_get_role_detail(role_id)
    time.sleep(0.5)

    test_update_role(role_id)
    time.sleep(0.5)

    test_delete_role(role_id)
    time.sleep(0.5)

    test_fixed_role_protection(roles_result)
    time.sleep(0.5)

    if users_result.get("items") and len(users_result["items"]) > 0:
        test_get_user_detail(users_result["items"][0]["id"])

    print("=" * 60)
    print("所有接口测试通过! ✅")
    print("=" * 60)
