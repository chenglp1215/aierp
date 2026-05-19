# 修复采购单下推品牌字段错误 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复销售订单下推采购单时的 AttributeError，通过正确的关联链获取品牌信息。

**Architecture:** 在路由层使用 `select_related` 预加载关联数据，服务层通过已加载的关联对象获取 brand_id。

**Tech Stack:** Python, FastAPI, Tortoise ORM

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/routers/sales_order.py` | 修改 | 添加 select_related 预加载 |
| `backend/services/purchase_order_service_mysql.py` | 修改 | 修复字段访问方式 |

---

### Task 1: 修改路由层添加预加载

**Files:**
- Modify: `backend/app/routers/sales_order.py:154-163`

- [ ] **Step 1: 修改路由层，在获取销售订单明细时预加载关联数据**

将第 154 行的 `prefetch_related("items")` 改为同时预加载关联链：

```python
# 获取销售订单，预加载明细及其关联数据
order = await SalesOrder.filter(order_no=order_no).prefetch_related("items").first()
if not order:
    raise ValueError(f"销售订单不存在: {order_no}")

# 获取选中的明细行号
items_data = data.get("items", [])
selected_row_nos = [item.get("row_no") for item in items_data if item.get("row_no")]

# 筛选选中的明细，并预加载关联数据
selected_items = [item for item in order.items if item.row_no in selected_row_nos]

# 预加载选中明细的关联数据
if selected_items:
    item_ids = [item.id for item in selected_items]
    selected_items = list(await SalesOrderItem.filter(id__in=item_ids).select_related(
        "spec__product__brand",
        "warehouse"
    ).all())
```

需要在文件顶部添加导入：
```python
from models_mysql.sales_order import SalesOrder, SalesOrderItem, ShippingMethod
```

- [ ] **Step 2: 验证修改后的代码语法正确**

运行: `cd e:/ai_erp/aierp/backend && python -c "from app.routers.sales_order import router; print('OK')"`

---

### Task 2: 修改服务层字段访问方式

**Files:**
- Modify: `backend/services/purchase_order_service_mysql.py:48-104`

- [ ] **Step 1: 修改 create_from_sales_order 方法中的品牌分组逻辑**

将第 48-54 行的品牌分组逻辑从：
```python
# 按品牌分组
items_by_brand: Dict[int, List[SalesOrderItem]] = {}
for item in selected_items:
    brand_id = item.brand_id or 0
    if brand_id not in items_by_brand:
        items_by_brand[brand_id] = []
    items_by_brand[brand_id].append(item)
```

修改为：
```python
# 按品牌分组（通过关联链获取品牌）
items_by_brand: Dict[int, List[SalesOrderItem]] = {}
for item in selected_items:
    # 通过 spec -> product -> brand 获取品牌ID
    brand_id = 0
    if item.spec_id:
        try:
            spec = item.spec
            if spec and hasattr(spec, 'product') and spec.product:
                product = spec.product
                if hasattr(product, 'brand') and product.brand:
                    brand_id = product.brand.id or 0
        except (TypeError, AttributeError):
            pass
    if brand_id not in items_by_brand:
        items_by_brand[brand_id] = []
    items_by_brand[brand_id].append(item)
```

- [ ] **Step 2: 修改明细创建时的字段赋值**

将第 88-104 行的明细创建从：
```python
for idx, item in enumerate(items, 1):
    amt = self._calculate_item_amount(item.qty, item.price, Decimal(str(item.discount)))
    await PurchaseOrderItem.create(
        purchase_order=purchase_order,
        row_no=idx,
        spec_id=item.spec_id,
        product_id=item.product_id,
        brand_id=item.brand_id,
        warehouse_id=item.warehouse_id,
        ...
    )
```

修改为：
```python
for idx, item in enumerate(items, 1):
    amt = self._calculate_item_amount(item.qty, item.price, Decimal(str(item.discount)))

    # 通过关联链获取 product_id 和 brand_id
    product_id = None
    brand_id = None
    if item.spec_id:
        try:
            spec = item.spec
            if spec and hasattr(spec, 'product') and spec.product:
                product_id = spec.product.id
                if hasattr(spec.product, 'brand') and spec.product.brand:
                    brand_id = spec.product.brand.id
        except (TypeError, AttributeError):
            pass

    await PurchaseOrderItem.create(
        purchase_order=purchase_order,
        row_no=idx,
        spec_id=item.spec_id,
        product_id=product_id,
        brand_id=brand_id,
        warehouse_id=item.warehouse_id,
        purchase_qty=item.qty,
        purchase_price=item.price,
        discount=item.discount,
        amt=amt,
        source_sale_row_no=item.row_no,
        shipping_method=item.shipping_method.value if item.shipping_method else None,
    )
```

- [ ] **Step 3: 验证修改后的代码语法正确**

运行: `cd e:/ai_erp/aierp/backend && python -c "from services.purchase_order_service_mysql import purchase_order_service_mysql; print('OK')"`

---

### Task 3: 提交修复

- [ ] **Step 1: 提交代码修改**

```bash
git add backend/app/routers/sales_order.py backend/services/purchase_order_service_mysql.py
git commit -m "fix: 修复销售订单下推采购单时品牌字段访问错误

- 通过 spec->product->brand 关联链获取品牌信息
- 在路由层添加 select_related 预加载避免 N+1 查询
- 处理品牌为空的情况，默认分组为 0

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: 验证修复

- [ ] **Step 1: 启动后端服务测试接口**

运行: `cd e:/ai_erp/aierp/backend && python -m uvicorn main:app --reload`

- [ ] **Step 2: 测试下推采购接口**

使用 API 测试工具或 curl 测试：
```
POST /api/sales-orders/{order_no}/push-to-purchase
{
  "items": [{"row_no": 1}]
}
```

验证返回结果正常，无 AttributeError 错误。
