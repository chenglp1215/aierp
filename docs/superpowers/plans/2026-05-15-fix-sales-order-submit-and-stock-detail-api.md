# 修复销售订单提交和规格库存详情接口 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复两个 BUG：1) 销售订单提交时 customer_name 为 null 的问题；2) 规格库存详情接口 404 问题

**Architecture:** 后端新增库存详情接口复用现有 StockService，前端在提交订单数据中添加 customer_name 字段

**Tech Stack:** Python/FastAPI (后端), Vue 3/TypeScript (前端), Tortoise ORM

---

## 文件结构

**修改文件：**
- `backend/app/routers/product.py` - 新增 `/specs/{spec_id}/stock-detail` 接口
- `web/src/components/workspace/SalesOrderWorkspace.vue` - submitData 添加 customer_name
- `web/src/components/workspace/SalesOrderCreate.vue` - data 添加 customer_name

---

### Task 1: 后端 - 新增规格库存详情接口

**Files:**
- Modify: `backend/app/routers/product.py:82-83` (在 delete_spec 接口后添加新接口)

- [ ] **Step 1: 在 product.py 中添加库存详情接口**

在 `@product_router.delete("/specs/{spec_id}")` 接口之后（约第 82 行后）添加新接口：

```python
@product_router.get("/specs/{spec_id}/stock-detail", response_model=dict)
@wrap_response
async def get_spec_stock_detail(
    spec_id: str,
    _: dict = Depends(require_permission("product.view"))
):
    """获取规格库存详情"""
    from services.inventory_service_mysql import stock_service

    spec_id_int = to_int_id(spec_id)
    stock_status = await stock_service.get_stock_status_by_spec_ids([spec_id_int])

    items = stock_status.get(str(spec_id_int), [])
    total_quantity = sum(item.get("quantity", 0) for item in items)

    return {
        "spec_id": spec_id_int,
        "items": items,
        "total_quantity": total_quantity
    }
```

- [ ] **Step 2: 验证接口实现**

检查代码是否正确：
1. 导入 `stock_service` 在函数内部，避免循环导入
2. 使用 `to_int_id` 转换 spec_id
3. 返回格式包含 `spec_id`、`items` 和 `total_quantity`

---

### Task 2: 前端 - 修复 SalesOrderWorkspace.vue 提交数据

**Files:**
- Modify: `web/src/components/workspace/SalesOrderWorkspace.vue:1037-1058`

- [ ] **Step 1: 在 submitData 中添加 customer_name 字段**

找到 `handleSubmitOrder` 函数中的 `submitData` 对象（约第 1037 行），在 `customer_id` 后添加 `customer_name`：

```typescript
  formLoading.value = true
  try {
    const submitData = {
      order_date: orderForm.value.order_date,
      customer_id: orderForm.value.customer_id,
      customer_name: orderForm.value.customer_name,
      sale_user_id: orderForm.value.sale_user_id || undefined,
      deliver_info: orderForm.value.deliver_info,
      expect_deliver_date: orderForm.value.expect_deliver_date || undefined,
      settle_type: orderForm.value.settle_type,
      invoice_info: orderForm.value.invoice_info,
      remark: orderForm.value.remark,
      items: orderForm.value.items.map(item => ({
        row_no: item.row_no,
        product_code: item.product_code || item.product_id,
        spec_code: item.spec_code || item.spec_id,
        packaging: item.packaging,
        sales_spec: item.sales_spec,
        qty: item.qty,
        price: item.price,
        discount: item.discount,
        warehouse_id: item.warehouse_id,
        shipping_method: item.shipping_method
      }))
    }
```

- [ ] **Step 2: 确认 customer_name 已在 orderForm 中定义**

验证 `orderForm` 初始化（约第 328 行）包含 `customer_name: ''` 字段。已确认存在。

---

### Task 3: 前端 - 修复 SalesOrderCreate.vue 提交数据

**Files:**
- Modify: `web/src/components/workspace/SalesOrderCreate.vue:593-612`

- [ ] **Step 1: 在 data 中添加 customer_name 字段**

找到 `handleSaveOrder` 函数中的 `data` 对象（约第 593 行），在 `customer_id` 后添加 `customer_name`：

```typescript
  formLoading.value = true
  try {
    const data = {
      order_date: orderForm.value.order_date,
      customer_id: orderForm.value.customer_id,
      customer_name: orderForm.value.customer_name,
      sale_user_id: orderForm.value.sale_user_id || undefined,
      deliver_info: orderForm.value.deliver_info,
      expect_deliver_date: orderForm.value.expect_deliver_date || undefined,
      settle_type: orderForm.value.settle_type,
      invoice_info: orderForm.value.invoice_info,
      remark: orderForm.value.remark,
      items: orderForm.value.items.map(item => ({
        row_no: item.row_no,
        product_code: item.product_code || item.product_id,
        spec_code: item.spec_code || item.spec_id,
        qty: item.qty,
        price: item.price,
        discount: item.discount,
        warehouse_id: item.warehouse_id || '',
        shipping_method: item.shipping_method
      }))
    }
```

- [ ] **Step 2: 确认 customer_name 已在 orderForm 中定义**

验证 `orderForm` 初始化（约第 168 行）包含 `customer_name: ''` 字段。已确认存在。

---

### Task 4: 验证修复

- [ ] **Step 1: 验证后端接口**

启动后端服务后，测试接口：
```bash
curl -X GET "http://localhost:8000/api/v1/products/specs/4/stock-detail" \
  -H "Authorization: Bearer <token>"
```

预期返回：
```json
{
  "status": "success",
  "message": "",
  "result": {
    "spec_id": 4,
    "items": [...],
    "total_quantity": 100
  }
}
```

- [ ] **Step 2: 验证前端订单提交**

1. 打开销售订单创建页面
2. 选择客户（确认 customer_name 被填充）
3. 添加商品明细
4. 提交订单
5. 确认不再出现 "customer_name is non nullable field" 错误

- [ ] **Step 3: 提交代码**

```bash
git add backend/app/routers/product.py web/src/components/workspace/SalesOrderWorkspace.vue web/src/components/workspace/SalesOrderCreate.vue
git commit -m "fix: 修复销售订单提交缺少customer_name和规格库存接口404问题"
```
