# 修复品牌管理采购人员下拉框实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在后端添加 `GET /brands/purchaser-candidates` 接口，返回采购组用户列表，修复前端品牌管理页面采购人员下拉框无法加载的问题。

**Architecture:** 在 `brand_router` 中新增路由，复用 `MySQLUserService.list_users()` 方法按角色过滤用户，返回简化的用户信息（id、full_name、username）。

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/routers/product.py` | 修改 | 添加 `purchaser-candidates` 路由 |

---

### Task 1: 添加采购人员候选接口

**Files:**
- Modify: `backend/app/routers/product.py:210-219` (在 `list_all_brands` 函数后添加新路由)

- [ ] **Step 1: 在 brand_router 中添加 purchaser-candidates 路由**

在 `backend/app/routers/product.py` 文件中，找到 `list_all_brands` 函数（约第 210-218 行），在其后添加新路由：

```python
### 获取采购人员候选列表
@brand_router.get("/purchaser-candidates", response_model=dict)
@wrap_response
async def get_purchaser_candidates(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    _: dict = Depends(require_permission("brand.view"))
):
    """获取采购人员候选列表（采购组用户）"""
    from services.auth_service import mysql_user_service

    # 查询采购组角色的用户
    result = await mysql_user_service.list_users(
        page=1,
        page_size=100,  # 下拉框不需要太多选项
        status="active",
        keyword=keyword,
        role="purchaser_group"
    )

    # 简化返回数据，仅保留必要字段
    candidates = [
        {
            "id": str(user["id"]),
            "full_name": user.get("full_name", ""),
            "username": user.get("username", "")
        }
        for user in result.get("items", [])
    ]

    return candidates
```

**注意**：路由路径 `/purchaser-candidates` 必须放在 `/{brand_id}` 路由之前，否则会被当作 `brand_id` 参数匹配。当前代码中 `/all` 路由已在 `/{brand_id}` 之前，新路由应放在 `/all` 之后、`/{brand_id}` 之前。

- [ ] **Step 2: 验证代码语法正确**

运行 Python 语法检查：

```bash
cd backend && venv/Scripts/python -m py_compile app/routers/product.py
```

Expected: 无输出表示语法正确

- [ ] **Step 3: 提交代码**

```bash
git add backend/app/routers/product.py
git commit -m "feat: 添加品牌采购人员候选列表接口

- 新增 GET /brands/purchaser-candidates 接口
- 返回采购组角色用户列表
- 支持关键字搜索

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: 测试验证

**Files:**
- 无文件修改，仅功能验证

- [ ] **Step 1: 启动后端服务**

```bash
cd backend && venv/Scripts/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Expected: 服务启动成功，显示 `Application startup complete`

- [ ] **Step 2: 测试接口返回**

使用 curl 或浏览器测试接口：

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/brands/purchaser-candidates
```

Expected: 返回采购组用户列表，格式如：
```json
{
  "status": "success",
  "message": "success",
  "result": [
    {"id": "1", "full_name": "张三", "username": "zhangsan"}
  ]
}
```

- [ ] **Step 3: 验证前端功能**

1. 打开浏览器访问前端品牌管理页面
2. 点击"新建品牌"或"编辑"按钮
3. 检查采购人员下拉框是否正常加载用户列表

Expected: 下拉框显示采购组用户列表，可选择用户

---

## 自检清单

**1. Spec 覆盖检查:**
- ✅ `GET /brands/purchaser-candidates` 接口 - Task 1
- ✅ 返回采购组用户列表 - Task 1
- ✅ 支持 keyword 参数 - Task 1
- ✅ 返回 id、full_name、username 字段 - Task 1
- ✅ 权限检查 - Task 1 (require_permission("brand.view"))

**2. 占位符扫描:**
- 无 TBD、TODO 等占位符
- 所有代码步骤包含完整实现

**3. 类型一致性:**
- `id` 字段转换为字符串，与前端接口定义一致
- 字段名 `full_name`、`username` 与前端 `PurchaserCandidate` 接口一致
