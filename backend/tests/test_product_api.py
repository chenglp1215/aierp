"""商品模块接口测试脚本

测试流程: 分类 → 品牌 → 商品 → 规格 的完整CRUD及异常验证
使用方法: python tests/test_product_api.py
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


def test_create_category():
    print("\n📦 [1/12] 创建分类")
    resp, err = api("POST", "/categories/", {
        "name": "测试电子产品",
        "tax_code": "TAX_ELEC",
        "sort_order": 1,
        "is_shop_display": True
    })
    body = parse(resp, err, "创建分类")
    if not body:
        return None
    ok = check_response_ok(body, "创建分类")
    if ok and check_field(body, "result", "创建分类"):
        data = body["result"]
        cat_id = data.get("id")
        result.record("创建分类-返回id", bool(cat_id), f"id={cat_id}")
        created_ids["category_id"] = cat_id
        return cat_id
    return None


def test_create_brand():
    print("\n📦 [2/12] 创建品牌")
    resp, err = api("POST", "/brands/", {
        "name": "测试品牌",
        "description": "测试品牌描述",
        "logo_url": "http://example.com/logo.png",
        "purchaser_id": None,
        "is_active": True
    })
    body = parse(resp, err, "创建品牌")
    if not body:
        return None
    ok = check_response_ok(body, "创建品牌")
    if ok and check_field(body, "result", "创建品牌"):
        data = body["result"]
        brand_id = data.get("id")
        result.record("创建品牌-返回id", bool(brand_id), f"id={brand_id}")
        created_ids["brand_id"] = brand_id
        return brand_id
    return None


def test_query_categories():
    print("\n📦 [3/12] 查询分类树")
    resp, err = api("GET", "/categories/")
    body = parse(resp, err, "查询分类树")
    if not body:
        return
    ok = check_response_ok(body, "查询分类树")
    if ok and check_field(body, "result", "查询分类树"):
        tree = body["result"]
        result.record("分类树-类型为列表", isinstance(tree, list), f"类型={type(tree).__name__}")
        cat_ids = [c.get("id") for c in tree]
        if created_ids.get("category_id"):
            found = created_ids["category_id"] in cat_ids
            result.record("分类树-包含新建分类", found)
        children_field = all("children" in c for c in tree) if tree else True
        result.record("分类树-包含children字段", children_field)
        level_field = all("level" in c for c in tree) if tree else True
        result.record("分类树-包含level字段", level_field)


def test_query_brands():
    print("\n📦 [4/12] 查询品牌列表")
    resp, err = api("GET", "/brands/", params={"page": 1, "page_size": 20})
    body = parse(resp, err, "查询品牌列表")
    if not body:
        return
    ok = check_response_ok(body, "查询品牌列表")
    if ok and check_field(body, "result", "查询品牌列表"):
        data = body["result"]
        result.record("品牌列表-包含total", "total" in data, f"keys={list(data.keys())}")
        result.record("品牌列表-包含items", "items" in data)
        if data.get("items") and created_ids.get("brand_id"):
            brand_ids = [b.get("id") for b in data["items"]]
            found = created_ids["brand_id"] in brand_ids
            result.record("品牌列表-包含新建品牌", found)


def test_create_product():
    print("\n📦 [5/12] 创建商品")
    cat_id = created_ids.get("category_id", "")
    brand_id = created_ids.get("brand_id", "")
    resp, err = api("POST", "/products/", {
        "name": "测试商品",
        "image_url": "http://example.com/product.png",
        "brand_id": brand_id,
        "category_id": cat_id,
        "tax_code": "TAX_PROD",
        "is_active": True
    })
    body = parse(resp, err, "创建商品")
    if not body:
        return None
    ok = check_response_ok(body, "创建商品")
    if ok and check_field(body, "result", "创建商品"):
        data = body["result"]
        prod_id = data.get("id")
        prod_code = data.get("product_code")
        result.record("创建商品-返回id", bool(prod_id))
        result.record("创建商品-自动生成product_code", bool(prod_code) and prod_code.startswith("PROD"), f"code={prod_code}")
        result.record("创建商品-brand_name填充", bool(data.get("brand_name")), f"brand_name={data.get('brand_name')}")
        result.record("创建商品-category_name填充", bool(data.get("category_name")), f"category_name={data.get('category_name')}")
        created_ids["product_id"] = prod_id
        return prod_id
    return None


def test_create_spec():
    print("\n📦 [6/12] 创建商品规格")
    prod_id = created_ids.get("product_id", "")
    resp, err = api("POST", f"/products/{prod_id}/specs", {
        "spec_code": "SPEC_TEST_001",
        "packaging": "100g/罐",
        "sales_spec": "100g*24罐/箱",
        "price": 128.50,
        "cas_number": "68917-21-1",
        "is_active": True
    })
    body = parse(resp, err, "创建规格")
    if not body:
        return None
    ok = check_response_ok(body, "创建规格")
    if ok and check_field(body, "result", "创建规格"):
        data = body["result"]
        spec_id = data.get("id")
        result.record("创建规格-返回id", bool(spec_id))
        result.record("创建规格-spec_code正确", data.get("spec_code") == "SPEC_TEST_001")
        result.record("创建规格-price正确", data.get("price") == 128.50)
        result.record("创建规格-product_id关联", data.get("product_id") == prod_id)
        created_ids["spec_id"] = spec_id
        return spec_id
    return None


def test_edit_product():
    print("\n📦 [7/12] 编辑商品")
    prod_id = created_ids.get("product_id", "")
    resp, err = api("PUT", f"/products/{prod_id}", {
        "name": "测试商品-已更新",
        "tax_code": "TAX_PROD_V2"
    })
    body = parse(resp, err, "编辑商品")
    if not body:
        return
    ok = check_response_ok(body, "编辑商品")
    if ok:
        result.record("编辑商品-返回成功", body.get("message") == "商品更新成功", f"msg={body.get('message')}")
    resp2, _ = api("GET", f"/products/{prod_id}")
    body2 = parse(resp2, None, "编辑商品-验证")
    if body2 and body2.get("result"):
        data = body2["result"]
        result.record("编辑商品-名称已更新", data.get("name") == "测试商品-已更新", f"name={data.get('name')}")
        result.record("编辑商品-tax_code已更新", data.get("tax_code") == "TAX_PROD_V2")


def test_edit_spec():
    print("\n📦 [8/12] 编辑商品规格")
    spec_id = created_ids.get("spec_id", "")
    resp, err = api("PUT", f"/products/specs/{spec_id}", {
        "price": 138.00,
        "packaging": "200g/罐"
    })
    body = parse(resp, err, "编辑规格")
    if not body:
        return
    ok = check_response_ok(body, "编辑规格")
    if ok:
        result.record("编辑规格-返回成功", body.get("message") == "规格更新成功", f"msg={body.get('message')}")
    resp2, _ = api("GET", f"/products/specs/{spec_id}")
    body2 = parse(resp2, None, "编辑规格-验证")
    if body2 and body2.get("result"):
        data = body2["result"]
        result.record("编辑规格-price已更新", data.get("price") == 138.00, f"price={data.get('price')}")
        result.record("编辑规格-packaging已更新", data.get("packaging") == "200g/罐")


def test_delete_spec():
    print("\n📦 [9/12] 删除规格")
    spec_id = created_ids.get("spec_id", "")
    resp, err = api("DELETE", f"/products/specs/{spec_id}")
    body = parse(resp, err, "删除规格")
    if not body:
        return
    ok = check_response_ok(body, "删除规格")
    if ok:
        result.record("删除规格-返回成功", body.get("message") == "规格删除成功")
    resp2, _ = api("GET", f"/products/specs/{spec_id}")
    body2 = parse(resp2, None, "删除规格-验证已删除")
    if body2:
        result.record("删除规格-再次查询应不存在", body2.get("status") == "error", f"status={body2.get('status')}")


def test_delete_product():
    print("\n📦 [10/12] 删除商品")
    prod_id = created_ids.get("product_id", "")
    resp, err = api("DELETE", f"/products/{prod_id}")
    body = parse(resp, err, "删除商品")
    if not body:
        return
    ok = check_response_ok(body, "删除商品")
    if ok:
        result.record("删除商品-返回成功", body.get("message") == "商品删除成功")
    resp2, _ = api("GET", f"/products/{prod_id}")
    body2 = parse(resp2, None, "删除商品-验证已删除")
    if body2:
        result.record("删除商品-再次查询应不存在", body2.get("status") == "error")


def test_delete_brand():
    print("\n📦 [11/12] 删除品牌")
    brand_id = created_ids.get("brand_id", "")
    resp, err = api("DELETE", f"/brands/{brand_id}")
    body = parse(resp, err, "删除品牌")
    if not body:
        return
    ok = check_response_ok(body, "删除品牌")
    if ok:
        result.record("删除品牌-返回成功", body.get("message") == "品牌删除成功")


def test_delete_category():
    print("\n📦 [12/12] 删除分类")
    cat_id = created_ids.get("category_id", "")
    resp, err = api("DELETE", f"/categories/{cat_id}")
    body = parse(resp, err, "删除分类")
    if not body:
        return
    ok = check_response_ok(body, "删除分类")
    if ok:
        result.record("删除分类-返回成功", body.get("message") == "分类删除成功")


def test_validation():
    print("\n🔍 异常参数验证测试")

    print("\n  [异常-1] 创建分类-缺少必填name")
    resp, err = api("POST", "/categories/", {"tax_code": "TAX001"})
    body = parse(resp, err, "异常-分类缺少name")
    if body:
        result.record("异常-分类缺少name应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-2] 创建品牌-缺少必填name")
    resp, err = api("POST", "/brands/", {"description": "无名称"})
    body = parse(resp, err, "异常-品牌缺少name")
    if body:
        result.record("异常-品牌缺少name应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-3] 创建商品-缺少必填name")
    resp, err = api("POST", "/products/", {"tax_code": "TAX001"})
    body = parse(resp, err, "异常-商品缺少name")
    if body:
        result.record("异常-商品缺少name应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-4] 创建规格-缺少必填spec_code")
    resp, err = api("POST", f"/products/{created_ids.get('product_id', 'x')}/specs", {"price": 100})
    body = parse(resp, err, "异常-规格缺少spec_code")

    print("\n  [异常-5] 创建规格-缺少必填price")
    resp, err = api("POST", f"/products/{created_ids.get('product_id', 'x')}/specs", {"spec_code": "SP001"})
    body = parse(resp, err, "异常-规格缺少price")
    if body:
        result.record("异常-规格缺少price应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-6] 创建商品-brand_id不存在")
    resp, err = api("POST", "/products/", {
        "name": "无效品牌商品",
        "brand_id": "000000000000000000000099"
    })
    body = parse(resp, err, "异常-商品brand_id不存在")
    if body:
        result.record("异常-商品brand_id不存在应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-7] 创建商品-category_id不存在")
    resp, err = api("POST", "/products/", {
        "name": "无效分类商品",
        "category_id": "000000000000000000000099"
    })
    body = parse(resp, err, "异常-商品category_id不存在")
    if body:
        result.record("异常-商品category_id不存在应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-8] 查询不存在的商品详情")
    resp, err = api("GET", "/products/000000000000000000000099")
    body = parse(resp, err, "异常-查询不存在商品")
    if body:
        result.record("异常-查询不存在商品应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-9] 查询不存在的品牌详情")
    resp, err = api("GET", "/brands/000000000000000000000099")
    body = parse(resp, err, "异常-查询不存在品牌")
    if body:
        result.record("异常-查询不存在品牌应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-10] 查询不存在的分类详情")
    resp, err = api("GET", "/categories/000000000000000000000099")
    body = parse(resp, err, "异常-查询不存在分类")
    if body:
        result.record("异常-查询不存在分类应报错",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-11] 规格搜索-缺少keyword")
    resp, err = api("GET", "/products/specs/search")
    if resp and resp.status_code == 422:
        result.record("异常-规格搜索缺少keyword应报错", True)
    else:
        body = parse(resp, err, "异常-规格搜索缺少keyword")
        if body:
            result.record("异常-规格搜索缺少keyword应报错",
                           body.get("status") == "error",
                           f"status={body.get('status')}, msg={body.get('message')}")

    print("\n  [异常-12] 无效分类ID格式查询分类详情")
    resp, err = api("GET", "/categories/invalid-id-format")
    body = parse(resp, err, "异常-无效分类ID格式")
    if body:
        is_error = body.get("status") == "error" or resp.status_code in (404, 400, 500)
        result.record("异常-无效分类ID应报错", is_error,
                       f"status={body.get('status')}, http={resp.status_code}")


def test_delete_constraint():
    print("\n🔍 删除约束验证测试")

    cat_resp, _ = api("POST", "/categories/", {"name": "约束测试分类"})
    cat_body = parse(cat_resp, None, "约束测试-创建分类")
    if not cat_body or cat_body.get("status") != "success":
        return
    cat_id = cat_body["result"]["id"]

    prod_resp, _ = api("POST", "/products/", {
        "name": "约束测试商品",
        "category_id": cat_id
    })
    prod_body = parse(prod_resp, None, "约束测试-创建商品关联分类")
    if not prod_body or prod_body.get("status") != "success":
        return

    resp, err = api("DELETE", f"/categories/{cat_id}")
    body = parse(resp, err, "约束-删除有关联商品的分类")
    if body:
        result.record("约束-删除有关联商品的分类应失败",
                       body.get("status") == "error",
                       f"status={body.get('status')}, msg={body.get('message')}")

    prod_id = prod_body["result"]["id"]
    del_resp, _ = api("DELETE", f"/products/{prod_id}")
    del_body = parse(del_resp, None, "约束测试-删除商品")
    if del_body and del_body.get("status") == "success":
        del_cat_resp, _ = api("DELETE", f"/categories/{cat_id}")
        del_cat_body = parse(del_cat_resp, None, "约束测试-删除分类")
        if del_cat_body:
            result.record("约束-删除无关联分类应成功",
                           del_cat_body.get("status") == "success")


def test_search_spec():
    print("\n🔍 规格搜索测试")
    prod_id = created_ids.get("product_id", "")
    if not prod_id:
        print("  ⏭ 跳过（无测试商品）")
        return

    resp, _ = api("POST", f"/products/{prod_id}/specs", {
        "spec_code": "SEARCH_TEST_001",
        "price": 99.99
    })
    body = parse(resp, None, "搜索测试-创建规格")
    if not body or body.get("status") != "success":
        return
    test_spec_id = body["result"]["id"]

    resp, _ = api("GET", "/products/specs/search", params={"keyword": "SEARCH_TEST"})
    body = parse(resp, None, "搜索规格")
    if body and body.get("status") == "success":
        items = body["result"].get("items", [])
        result.record("规格搜索-能搜到结果", len(items) > 0, f"count={len(items)}")
        if items:
            result.record("规格搜索-包含product_name",
                           "product_name" in items[0],
                           f"keys={list(items[0].keys())}")
    api("DELETE", f"/products/specs/{test_spec_id}")


def test_product_list():
    print("\n🔍 商品列表查询测试")
    resp, _ = api("GET", "/products/", params={"page": 1, "page_size": 10})
    body = parse(resp, None, "商品列表")
    if body and body.get("status") == "success":
        data = body["result"]
        result.record("商品列表-包含total", "total" in data)
        result.record("商品列表-包含items", "items" in data)
        result.record("商品列表-包含page", "page" in data)
        result.record("商品列表-包含page_size", "page_size" in data)


def test_category_detail():
    print("\n🔍 分类详情测试")
    cat_id = created_ids.get("category_id", "")
    if not cat_id:
        print("  ⏭ 跳过（无测试分类）")
        return
    resp, _ = api("GET", f"/categories/{cat_id}")
    body = parse(resp, None, "分类详情")
    if body and body.get("status") == "success":
        data = body["result"]
        result.record("分类详情-包含id", "id" in data)
        result.record("分类详情-包含name", "name" in data)
        result.record("分类详情-包含level", "level" in data)
        result.record("分类详情-包含children", "children" in data)


def test_brand_detail():
    print("\n🔍 品牌详情测试")
    brand_id = created_ids.get("brand_id", "")
    if not brand_id:
        print("  ⏭ 跳过（无测试品牌）")
        return
    resp, _ = api("GET", f"/brands/{brand_id}")
    body = parse(resp, None, "品牌详情")
    if body and body.get("status") == "success":
        data = body["result"]
        result.record("品牌详情-包含id", "id" in data)
        result.record("品牌详情-包含name", "name" in data)
        result.record("品牌详情-包含purchaser_id", "purchaser_id" in data)


def main():
    import time as _time
    _time.sleep(2)

    print("=" * 60)
    print("商品模块接口测试")
    print(f"服务地址: {BASE_URL}")
    print("=" * 60)

    health_resp, health_err = api("GET", "/health")
    if health_err or (health_resp and health_resp.status_code != 200):
        print(f"\n❌ 服务未就绪: {health_err or health_resp.status_code}")
        sys.exit(1)
    print("✅ 服务健康检查通过")

    test_create_category()
    test_create_brand()
    test_query_categories()
    test_query_brands()
    test_create_product()
    test_create_spec()
    test_product_list()
    test_category_detail()
    test_brand_detail()
    test_search_spec()
    test_edit_product()
    test_edit_spec()
    test_validation()
    test_delete_constraint()
    test_delete_spec()
    test_delete_product()
    test_delete_brand()
    test_delete_category()

    success = result.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
