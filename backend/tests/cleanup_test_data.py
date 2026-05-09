"""清理测试数据"""
import requests
import time

BASE = "http://localhost:8000/api/v1"


def cleanup():
    time.sleep(2)
    try:
        r = requests.get(f"{BASE}/categories/", timeout=30)
        data = r.json()
        if data.get("status") == "success":
            for cat in data.get("result", []):
                name = cat.get("name", "")
                if "测试" in name or "test" in name.lower() or "约束" in name:
                    cat_id = cat["id"]
                    requests.delete(f"{BASE}/categories/{cat_id}", timeout=30)
                    print(f"deleted category: {name}")
    except Exception as e:
        print(f"category cleanup error: {e}")

    try:
        r = requests.get(f"{BASE}/brands/", params={"page": 1, "page_size": 100}, timeout=30)
        data = r.json()
        if data.get("status") == "success":
            for b in data.get("result", {}).get("items", []):
                name = b.get("name", "")
                if "测试" in name or "test" in name.lower() or "约束" in name:
                    brand_id = b["id"]
                    requests.delete(f"{BASE}/brands/{brand_id}", timeout=30)
                    print(f"deleted brand: {name}")
    except Exception as e:
        print(f"brand cleanup error: {e}")

    print("cleanup done")


if __name__ == "__main__":
    cleanup()
