# 销售订单 API 测试与文档更新 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 更新销售订单模块的 API 测试脚本和接口文档，反映 MySQL 迁移后的数据结构变更

**Architecture:** 基于现有的 requests 测试脚本模式，更新测试用例以匹配新的接口定义；更新 API 文档以反映 MySQL 表结构和状态枚举变更

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL, requests

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/tests/test_sales_order_api.py` | 修改 | 更新测试脚本，匹配新接口 |
| `backend/app/routers/api_docs/sales_order.md` | 修改 | 更新 API 文档 |
| `.project_docs/backend/项目模块说明.md` | 修改 | 更新模块概览 |

---

## 1. 环境准备

### Task 1: 检查后端服务状态

**Files:**
- 无文件变更

- [ ] **Step 1: 检查服务健康状态**

Run: `curl -s http://localhost:8000/api/v1/health`
Expected: 返回 `{"status": "success", ...}` 或确认服务未启动

- [ ] **Step 2: 如服务未启动，启动后端服务**

Run: `cd backend && venv/Scripts/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &`
Expected: 服务启动成功

---

## 2. 更新测试脚本

### Task 2: 更新测试脚本以匹配新接口

**Files:**
- Modify: `backend/tests/test_sales_order_api.py`

- [ ] **Step 1: 分析现有测试脚本与新接口的差异**

新接口变更点：
1. 新增 `POST /{order_no}/submit` 提交审核接口
2. 新增 `POST /{order_no}/approve` 审核通过接口
3. 新增 `POST /{order_no}/reject` 驳回接口
4. 新增 `POST /{order_no}/cancel` 取消接口
5. 移除旧的 `PATCH /{order_no}/{status_key}` 统一状态更新接口
6. 订单状态新增 `pending`（待审核）
7. 响应格式中 `status` 字段改为直接返回 `order_status` 等

- [ ] **Step 2: 更新测试脚本头部注释**

修改文件头部注释：

```python
"""销售订单模块接口测试脚本 (MySQL 版本)

测试流程: 查找已有数据 → 创建订单 → 列表/详情/搜索 → 更新 → 状态流转 → 删除
使用方法: python tests/test_sales_order_api.py

接口变更说明 (MySQL 迁移后):
- 新增 submit/approve/reject/cancel 独立状态操作接口
- 订单状态新增 pending（待审核）
- 响应格式中状态字段直接返回 order_status 等字符串值
"""
```

- [ ] **Step 3: 更新 test_create_order 函数中的状态验证**

找到第 153-157 行，修改状态验证逻辑：

```python
# 旧代码（第 153-157 行）
actual_status = detail.get("status", {}).get("order_status")
print(f"  📋 详情: order_no={detail.get('order_no')}, status={actual_status}, customer_id={detail.get('customer_id')}")
result.record("创建订单-状态为draft",
               actual_status == "draft",
               f"status={actual_status}")

# 新代码
actual_status = detail.get("order_status")
print(f"  📋 详情: order_no={detail.get('order_no')}, order_status={actual_status}, customer_id={detail.get('customer_id')}")
result.record("创建订单-状态为draft",
               actual_status == "draft",
               f"order_status={actual_status}")
```

- [ ] **Step 4: 更新 test_create_and_submit 函数中的状态验证**

找到第 199-201 行，修改状态验证逻辑：

```python
# 旧代码（第 199-201 行）
result.record("创建并提交订单-状态为audited",
               detail.get("status", {}).get("order_status") == "audited",
               f"status={detail.get('status', {}).get('order_status')}")

# 新代码
result.record("创建并提交订单-状态为audited",
               detail.get("order_status") == "audited",
               f"order_status={detail.get('order_status')}")
```

- [ ] **Step 5: 更新 test_get_detail 函数中的状态验证**

找到第 281-284 行，修改状态验证逻辑：

```python
# 旧代码（第 281-284 行）
result.record("获取详情-order_no正确", order.get("order_no") == order_no)
result.record("获取详情-包含items", "items" in order)
result.record("获取详情-包含status", "status" in order)
result.record("获取详情-包含customer_id", "customer_id" in order)

# 新代码
result.record("获取详情-order_no正确", order.get("order_no") == order_no)
result.record("获取详情-包含items", "items" in order)
result.record("获取详情-包含order_status", "order_status" in order)
result.record("获取详情-包含customer_id", "customer_id" in order)
```

- [ ] **Step 6: 替换 test_update_status 函数为新的状态流转测试**

删除旧的 `test_update_status` 函数（第 316-334 行），替换为新的状态流转测试函数：

```python
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
```

- [ ] **Step 7: 删除 test_update_invalid_status_key 函数**

删除 `test_update_invalid_status_key` 函数（第 337-345 行），因为新的接口设计中不再有统一的 PATCH 状态更新接口。

- [ ] **Step 8: 更新 main 函数中的测试流程**

找到 main 函数（第 400-450 行），修改测试流程：

```python
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
```

- [ ] **Step 9: 运行测试脚本验证修改**

Run: `cd backend && venv/Scripts/python tests/test_sales_order_api.py`
Expected: 所有测试用例通过

- [ ] **Step 10: 提交测试脚本更新**

```bash
git add backend/tests/test_sales_order_api.py
git commit -m "test: 更新销售订单 API 测试脚本以匹配 MySQL 迁移后的接口

- 更新状态字段验证逻辑（order_status 直接返回）
- 新增 submit/approve/reject/cancel 独立状态操作测试
- 移除旧的 PATCH 统一状态更新测试
- 更新测试流程以覆盖完整状态流转"
```

---

## 3. 更新 API 文档

### Task 3: 更新销售订单 API 文档

**Files:**
- Modify: `backend/app/routers/api_docs/sales_order.md`

- [ ] **Step 1: 更新状态枚举值说明**

找到第 577-586 行的订单状态枚举，添加 `pending` 状态：

```markdown
#### 订单状态 (order_status)
| 值 | 说明 |
|------|------|
| draft | 草稿 |
| pending | 待审核 |
| audited | 已审核 |
| partially_pushed_to_purchase | 部分下推采购 |
| pushed_to_purchase | 已下推采购 |
| closed | 已关闭 |
| cancelled | 已取消 |
```

- [ ] **Step 2: 更新状态流转图**

找到第 547-559 行的状态流转图，更新为：

```markdown
### 订单状态流转

```
draft → pending → audited → partially_pushed_to_purchase → pushed_to_purchase → closed
  ↓        ↓         ↓                  ↓                        ↓
cancelled cancelled  cancelled          cancelled               cancelled
```

| 当前状态 | 可变更为 |
|----------|----------|
| draft（草稿） | pending, cancelled |
| pending（待审核） | audited, draft |
| audited（已审核） | partially_pushed_to_purchase, pushed_to_purchase, closed, cancelled |
| partially_pushed_to_purchase（部分下推） | pushed_to_purchase, closed, cancelled |
| pushed_to_purchase（已下推） | closed, cancelled |
| closed / cancelled | 不可变更 |
```

- [ ] **Step 3: 添加新的状态操作接口文档**

在 7.7.7 节之前添加新的接口文档：

```markdown
### 7.7.7 提交审核

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/submit` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单已提交审核",
  "result": null
}
```

> 将订单状态从 draft 变更为 pending

---

### 7.7.8 审核通过

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/approve` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单审核通过",
  "result": null
}
```

> 将订单状态从 pending 变更为 audited

---

### 7.7.9 驳回订单

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/reject` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单已驳回",
  "result": null
}
```

> 将订单状态从 pending 变更为 draft

---

### 7.7.10 取消订单

| 属性 | 值 |
|------|-----|
| **URL** | `POST /api/v1/sales-orders/{order_no}/cancel` |
| **权限** | `order.edit` |

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| order_no | string | 订单号 |

**成功响应**

```json
{
  "status": "success",
  "message": "订单已取消",
  "result": null
}
```

> 将订单状态变更为 cancelled（仅特定状态可取消）

---
```

- [ ] **Step 4: 更新目录索引**

找到第 38-49 行的目录，更新为：

```markdown
## 目录

- [7.7.1 创建销售订单](#771-创建销售订单)
- [7.7.2 创建并提交销售订单](#772-创建并提交销售订单直接审核通过)
- [7.7.3 获取销售订单列表](#773-获取销售订单列表)
- [7.7.4 获取销售订单详情](#774-获取销售订单详情)
- [7.7.5 更新销售订单](#775-更新销售订单)
- [7.7.6 删除销售订单](#776-删除销售订单)
- [7.7.7 提交审核](#777-提交审核)
- [7.7.8 审核通过](#778-审核通过)
- [7.7.9 驳回订单](#779-驳回订单)
- [7.7.10 取消订单](#7710-取消订单)
- [7.7.11 获取状态流转记录](#7711-获取状态流转记录)
- [7.7.12 下推采购](#7712-下推采购)
- [数据模型](#数据模型)
- [业务规则](#业务规则)
- [权限说明](#权限说明)
```

- [ ] **Step 5: 更新数据模型说明**

找到第 489-515 行的 SalesOrder 数据模型，更新字段：

```markdown
### SalesOrder（销售订单）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 订单ID（MySQL 自增主键） |
| order_no | string | 订单号（系统自动生成，格式 SO{YYYYMMDD}{4位序号}） |
| order_date | string | 订单日期 |
| customer_id | int | 客户ID |
| customer_name | string | 客户名称 |
| sale_user_id | int | 销售人员ID |
| sale_user_name | string | 销售人员名称 |
| order_status | string | 订单状态（draft/pending/audited/...） |
| delivery_status | string | 发货状态（none/partial/full） |
| receive_status | string | 收货状态（none/partial/full） |
| invoice_status | string | 开票状态（none/partial/full） |
| total_amt | float | 商品总金额（未税） |
| tax_rate | float | 税率 |
| tax_amt | float | 税额 |
| total_tax_amt | float | 含税总金额 |
| total_discount_amt | float | 整单折扣金额 |
| expect_deliver_date | string | 期望交货日 |
| settle_type | string | 结算方式 |
| remark | string | 备注 |
| creator_id | int | 创建人ID |
| creator_name | string | 创建人名称 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |
| items | SalesOrderItem[] | 商品明细 |
| deliver_info | SalesDeliverInfo | 发货信息 |
```

- [ ] **Step 6: 更新 SalesOrderItem 数据模型**

找到第 517-539 行，更新为：

```markdown
### SalesOrderItem（商品明细）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 明细ID |
| sales_order_id | int | 关联订单ID |
| row_no | int | 行号 |
| product_id | int | 商品ID |
| product_code | string | 商品编码 |
| product_name | string | 商品名称 |
| spec_id | int | 规格ID |
| spec_code | string | 规格编码 |
| brand_id | int | 品牌ID |
| brand_name | string | 品牌名称 |
| warehouse_id | int | 仓库ID |
| warehouse_name | string | 仓库名称 |
| qty | int | 订购数量 |
| price | float | 原始单价 |
| discount | float | 折扣率 |
| discounted_price | float | 折后单价 |
| amt | float | 行金额 |
| shipping_method | string | 发货方式（direct/warehouse） |
| pushed | boolean | 是否已下推采购 |
| out_qty | int | 已发货数量 |
| return_qty | int | 已退货数量 |
```

- [ ] **Step 7: 添加 SalesDeliverInfo 数据模型**

在 SalesOrderItem 之后添加：

```markdown
### SalesDeliverInfo（发货信息）

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 发货信息ID |
| sales_order_id | int | 关联订单ID |
| addr | string | 详细地址 |
| province | string | 省 |
| city | string | 市 |
| person_name | string | 收货人 |
| person_tel | string | 联系电话 |
```

- [ ] **Step 8: 提交文档更新**

```bash
git add backend/app/routers/api_docs/sales_order.md
git commit -m "docs: 更新销售订单 API 文档以反映 MySQL 迁移后的变更

- 新增 pending 订单状态
- 新增 submit/approve/reject/cancel 独立状态操作接口文档
- 更新状态流转图
- 更新数据模型字段（MySQL 表结构）"
```

---

## 4. 更新项目模块说明

### Task 4: 更新项目模块说明文档

**Files:**
- Modify: `.project_docs/backend/项目模块说明.md`

- [ ] **Step 1: 更新销售订单模块说明**

找到第 265-283 行的销售订单模块部分，更新为：

```markdown
### 8. 销售订单

**功能**：销售订单创建、编辑、状态流转、订单号生成

**核心文件**：
- `app/routers/sales_order.py` — 路由
- `services/sales_order_service_mysql.py` — 业务服务（MySQL 版本）
- `services/order_status_flow_service.py` — 订单状态流转服务
- `models_mysql/sales_order.py` — 数据模型（Tortoise ORM）

**API 文档**：`app/routers/api_docs/sales_order.md`

**订单状态流转**：
```
draft → pending → audited → partially_pushed_to_purchase → pushed_to_purchase → closed
  ↓        ↓         ↓                  ↓                        ↓
cancelled cancelled  cancelled          cancelled               cancelled
```

**API 接口**：
| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/sales-orders/` | 创建销售订单 | `order.create` |
| POST | `/api/v1/sales-orders/create-and-submit` | 创建并提交订单 | `order.create` |
| GET | `/api/v1/sales-orders/` | 获取订单列表 | `order.view` |
| GET | `/api/v1/sales-orders/{order_no}` | 获取订单详情 | `order.view` |
| PUT | `/api/v1/sales-orders/{order_no}` | 更新订单 | `order.edit` |
| DELETE | `/api/v1/sales-orders/{order_no}` | 删除订单 | `order.delete` |
| POST | `/api/v1/sales-orders/{order_no}/submit` | 提交审核 | `order.edit` |
| POST | `/api/v1/sales-orders/{order_no}/approve` | 审核通过 | `order.edit` |
| POST | `/api/v1/sales-orders/{order_no}/reject` | 驳回订单 | `order.edit` |
| POST | `/api/v1/sales-orders/{order_no}/cancel` | 取消订单 | `order.edit` |
| GET | `/api/v1/sales-orders/{order_no}/status-flows` | 获取状态流转记录 | `order.view` |

**数据模型**：
- `SalesOrder` — 订单主表（sales_orders）
- `SalesOrderItem` — 订单明细（sales_order_items）
- `SalesDeliverInfo` — 发货信息（sales_deliver_infos）

---
```

- [ ] **Step 2: 提交文档更新**

```bash
git add .project_docs/backend/项目模块说明.md
git commit -m "docs: 更新项目模块说明中销售订单模块的 API 文档

- 更新核心文件路径（MySQL 版本）
- 更新状态流转图（新增 pending 状态）
- 新增完整的 API 接口列表"
```

---

## 5. 清理和验证

### Task 5: 关闭后端服务并验证

**Files:**
- 无文件变更

- [ ] **Step 1: 关闭后端服务**

Run: `pkill -f "uvicorn app.main:app" 2>/dev/null || taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" 2>/dev/null || echo "服务已关闭或未运行"`
Expected: 服务关闭成功

- [ ] **Step 2: 验证所有文件已提交**

Run: `git status`
Expected: 工作区干净，无未提交的变更

---

## 自检清单

**1. Spec 覆盖检查：**
- [x] API 测试脚本生成 → Task 2
- [x] 测试数据清理 → 已有机制
- [x] 测试报告输出 → 已有机制
- [x] API 文档更新 → Task 3, Task 4

**2. 占位符检查：**
- 无 TBD、TODO 等占位符
- 所有代码步骤包含完整代码

**3. 类型一致性检查：**
- `order_status` 字段在所有位置使用一致
- 状态枚举值 `draft`、`pending`、`audited` 等使用一致
