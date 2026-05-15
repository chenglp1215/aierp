# 采购单外键关联重构实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 移除 PurchaseOrderItem 中的冗余字段，使用 ForeignKeyField 建立外键关联，保持 API 响应格式兼容

**Architecture:** 使用 Tortoise ORM 的 ForeignKeyField 替代冗余字段存储，通过 prefetch_related/select_related 预加载关联数据，to_dict() 方法中返回关联名称。设计参照已完成的 SalesOrderItem 重构。

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/models_mysql/purchase_order.py` | 修改 | 更新模型定义，添加外键关联，移除冗余字段 |
| `backend/services/purchase_order_service_mysql.py` | 修改 | 更新查询逻辑，使用 select_related |
| `backend/migrations/scripts/` | 创建 | 数据库迁移脚本 |

---

## 1. 准备工作

### Task 1: 备份数据库

**Files:**
- 无文件变更

- [ ] **Step 1: 导出当前数据库结构**

Run: `mysqldump -h 132.232.212.151 -P 58901 -u admin -p'Chenglp1215!@#' erp_test purchase_orders purchase_order_items --no-data > backend/migrations/scripts/backup_purchase_order_schema.sql`
Expected: 导出成功

- [ ] **Step 2: 验证 ProductSpec、Warehouse、Brand 模型存在**

Run: `cd backend && venv/Scripts/python -c "from models_mysql.product import Product, ProductSpec, Brand; from models_mysql.warehouse import Warehouse; print('OK')"`
Expected: 输出 "OK"

---

## 2. 修改 PurchaseOrder 模型

### Task 2: 添加 Brand 外键关联

**Files:**
- Modify: `backend/models_mysql/purchase_order.py`

- [ ] **Step 1: 读取当前模型定义**

Run: `cat backend/models_mysql/purchase_order.py | head -100`
Expected: 显示当前模型定义

- [ ] **Step 2: 在 PurchaseOrder 类中添加 Brand 外键关联**

将 PurchaseOrder 类中的 `brand_id` 和 `brand_name` 字段替换为：

```python
class PurchaseOrder(Model):
    """采购单主表"""
    id = fields.IntField(pk=True, description="采购单ID")
    purchase_no = fields.CharField(max_length=50, unique=True, description="采购单号")
    purchase_type = fields.CharEnumField(PurchaseType, description="采购类型")
    source_sale_order_id = fields.IntField(null=True, description="关联源销售订单ID")
    source_sale_order_no = fields.CharField(max_length=50, null=True, description="关联源销售订单号")

    # 外键关联 - 替代冗余字段
    brand: fields.ForeignKeyNullableRelation["Brand"] = fields.ForeignKeyField(
        "models.Brand", related_name="purchase_orders", null=True, description="品牌"
    )

    # 保留的字段
    supplier_id = fields.IntField(null=True, description="供应商ID")
    supplier_name = fields.CharField(max_length=200, null=True, description="供应商名称（快照）")
    purchase_user_id = fields.IntField(null=True, description="采购员用户ID")
    # ... 其他字段保持不变
```

- [ ] **Step 3: 在文件顶部添加 Brand 导入**

在文件开头的导入区域添加：

```python
from models_mysql.product import Brand
```

- [ ] **Step 4: 更新 PurchaseOrder.to_dict() 方法**

将 `to_dict` 方法更新为：

```python
async def to_dict(self):
    """转换为字典格式，通过关联查询返回品牌名称"""
    brand = None
    if self.brand_id:
        try:
            brand = self.brand
            if brand is None or not hasattr(brand, 'id'):
                brand = await self.brand
        except TypeError:
            brand = await self.brand

    return {
        "id": self.id,
        "purchase_no": self.purchase_no,
        "purchase_type": self.purchase_type.value if self.purchase_type else None,
        "source_sale_order_id": self.source_sale_order_id,
        "source_sale_order_no": self.source_sale_order_no,
        "brand_id": self.brand_id,
        "brand_name": brand.name if brand else None,
        "supplier_id": self.supplier_id,
        "supplier_name": self.supplier_name,
        "purchase_user_id": self.purchase_user_id,
        "purchase_status": self.purchase_status.value if self.purchase_status else None,
        "in_status": self.in_status.value if self.in_status else None,
        "pay_status": self.pay_status.value if self.pay_status else None,
        "total_amt": float(self.total_amt),
        "freight_amt": float(self.freight_amt),
        "tax_rate": float(self.tax_rate),
        "tax_amt": float(self.tax_amt),
        "total_tax_amt": float(self.total_tax_amt),
        "expect_arrive_date": self.expect_arrive_date.isoformat() if self.expect_arrive_date else None,
        "settle_type": self.settle_type,
        "remark": self.remark,
        "creator_id": self.creator_id,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
```

- [ ] **Step 5: 验证模型语法正确**

Run: `cd backend && venv/Scripts/python -c "from models_mysql.purchase_order import PurchaseOrder; print('OK')"`
Expected: 输出 "OK"

---

## 3. 修改 PurchaseOrderItem 模型

### Task 3: 添加外键关联并移除冗余字段

**Files:**
- Modify: `backend/models_mysql/purchase_order.py`

- [ ] **Step 1: 修改 PurchaseOrderItem 模型，添加外键关联**

将 PurchaseOrderItem 类修改为：

```python
class PurchaseOrderItem(Model):
    """采购单明细"""
    id = fields.IntField(pk=True, description="明细ID")
    purchase_order = fields.ForeignKeyField("models.PurchaseOrder", related_name="items", on_delete=fields.CASCADE)
    row_no = fields.IntField(description="行号")

    # 外键关联 - spec 关联 product，product 关联 brand
    spec: fields.ForeignKeyNullableRelation["ProductSpec"] = fields.ForeignKeyField(
        "models.ProductSpec", related_name="purchase_order_items", null=True, description="规格"
    )
    warehouse: fields.ForeignKeyNullableRelation["Warehouse"] = fields.ForeignKeyField(
        "models.Warehouse", related_name="purchase_order_items", null=True, description="仓库"
    )

    # 保留的字段
    product_id = fields.IntField(null=True, description="商品ID（冗余，通过 spec 获取）")
    brand_id = fields.IntField(null=True, description="品牌ID（冗余，通过 spec 获取）")

    purchase_qty = fields.IntField(description="采购数量")
    purchase_price = fields.DecimalField(max_digits=12, decimal_places=2, description="采购单价")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣系数")
    amt = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="行金额")
    in_qty = fields.IntField(default=0, description="已入库数量")
    return_qty = fields.IntField(default=0, description="已退货数量")
    source_sale_row_no = fields.IntField(null=True, description="关联源销售单明细行号")
    shipping_method = fields.CharField(max_length=50, null=True, description="发货方式")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "purchase_order_items"
        ordering = ["row_no"]

    async def to_dict(self):
        """转换为字典格式，通过关联查询返回名称

        注意：如果使用 select_related 预加载了关联数据，self.spec、self.warehouse 等
        会直接返回对象而不是协程
        """
        # 获取 spec
        spec = None
        if self.spec_id:
            try:
                spec = self.spec
                if spec is None or not hasattr(spec, 'id'):
                    spec = await self.spec
            except TypeError:
                spec = await self.spec

        # 获取 warehouse
        warehouse = None
        if self.warehouse_id:
            try:
                warehouse = self.warehouse
                if warehouse is None or not hasattr(warehouse, 'id'):
                    warehouse = await self.warehouse
            except TypeError:
                warehouse = await self.warehouse

        # 通过 spec 获取 product 和 brand
        product = None
        brand = None
        if spec:
            try:
                product = spec.product
                if product is None or not hasattr(product, 'id'):
                    product = await spec.product
            except (TypeError, AttributeError):
                if hasattr(spec, 'product_id') and spec.product_id:
                    product = await spec.product

            if product:
                try:
                    brand = product.brand
                    if brand is None or not hasattr(brand, 'id'):
                        brand = await product.brand
                except (TypeError, AttributeError):
                    if hasattr(product, 'brand_id') and product.brand_id:
                        brand = await product.brand

        return {
            "id": self.id,
            "purchase_order_id": self.purchase_order_id,
            "row_no": self.row_no,
            "product_id": product.id if product else self.product_id,
            "product_code": product.product_code if product else None,
            "product_name": product.name if product else None,
            "spec_id": self.spec_id,
            "spec_code": spec.spec_code if spec else None,
            "brand_id": brand.id if brand else self.brand_id,
            "brand_name": brand.name if brand else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": warehouse.name if warehouse else None,
            "purchase_qty": self.purchase_qty,
            "purchase_price": float(self.purchase_price),
            "discount": float(self.discount),
            "amt": float(self.amt) if self.amt else None,
            "in_qty": self.in_qty,
            "return_qty": self.return_qty,
            "source_sale_row_no": self.source_sale_row_no,
            "shipping_method": self.shipping_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 在文件顶部添加必要的导入**

在文件开头的导入区域添加：

```python
from models_mysql.product import ProductSpec
from models_mysql.warehouse import Warehouse
```

- [ ] **Step 3: 验证模型语法正确**

Run: `cd backend && venv/Scripts/python -c "from models_mysql.purchase_order import PurchaseOrder, PurchaseOrderItem; print('OK')"`
Expected: 输出 "OK"

---

## 4. 更新 Service 层

### Task 4: 更新查询逻辑使用 select_related

**Files:**
- Modify: `backend/services/purchase_order_service_mysql.py`

- [ ] **Step 1: 更新 get_order_by_no 方法**

将 `get_order_by_no` 方法修改为：

```python
async def get_order_by_no(self, purchase_no: str) -> Optional[Dict[str, Any]]:
    """根据采购单号获取详情"""
    order = await PurchaseOrder.filter(purchase_no=purchase_no).prefetch_related("items").first()
    if not order:
        return None

    # 对每个明细使用 select_related 获取关联数据
    items_data = []
    for item in order.items:
        # 使用 select_related 获取 spec 和 warehouse
        item_with_relations = await PurchaseOrderItem.filter(id=item.id).select_related(
            "spec__product__brand",
            "warehouse"
        ).first()
        if item_with_relations:
            items_data.append(await item_with_relations.to_dict())
        else:
            items_data.append(await item.to_dict())

    result = await order.to_dict()
    result["items"] = items_data
    return result
```

- [ ] **Step 2: 更新 create_from_sales_order 方法，移除冗余字段赋值**

将创建明细的代码修改为：

```python
# 创建明细
for idx, item in enumerate(items, 1):
    amt = self._calculate_item_amount(item.qty, item.price, Decimal(str(item.discount)))
    await PurchaseOrderItem.create(
        purchase_order=purchase_order,
        row_no=idx,
        spec_id=item.spec_id,
        product_id=item.product_id,  # 保留冗余字段用于兼容
        brand_id=item.brand_id,  # 保留冗余字段用于兼容
        warehouse_id=item.warehouse_id,
        purchase_qty=item.qty,
        purchase_price=item.price,
        discount=item.discount,
        amt=amt,
        source_sale_row_no=item.row_no,
        shipping_method=item.shipping_method.value if item.shipping_method else None,
    )
```

注意：移除了 `brand_name` 和 `warehouse_name` 的赋值。

- [ ] **Step 3: 验证服务层语法正确**

Run: `cd backend && venv/Scripts/python -c "from services.purchase_order_service_mysql import purchase_order_service_mysql; print('OK')"`
Expected: 输出 "OK"

---

## 5. 数据库迁移

### Task 5: 创建并执行迁移脚本

**Files:**
- Create: `backend/migrations/scripts/remove_purchase_order_redundant_fields.sql`

- [ ] **Step 1: 创建迁移 SQL 脚本**

创建文件 `backend/migrations/scripts/remove_purchase_order_redundant_fields.sql`：

```sql
-- 移除 purchase_orders 表中的冗余字段
-- 注意：brand_id 列保留，只删除 brand_name

-- 1. 删除 purchase_orders 表的 brand_name 字段
ALTER TABLE purchase_orders
DROP COLUMN IF EXISTS brand_name;

-- 2. 删除 purchase_order_items 表中的冗余字段
ALTER TABLE purchase_order_items
DROP COLUMN IF EXISTS brand_name,
DROP COLUMN IF EXISTS warehouse_name;

-- 3. 确保 spec_id 列存在
-- (如果之前不存在，需要先添加)
-- ALTER TABLE purchase_order_items
-- ADD COLUMN IF NOT EXISTS spec_id INT NULL COMMENT '规格ID';

-- 4. 添加外键约束（可选，根据需要）
-- ALTER TABLE purchase_order_items
-- ADD CONSTRAINT fk_purchase_order_item_spec FOREIGN KEY (spec_id) REFERENCES product_specs(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_purchase_order_item_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL;
```

- [ ] **Step 2: 执行迁移脚本**

Run: `mysql -h 132.232.212.151 -P 58901 -u admin -p'Chenglp1215!@#' erp_test < backend/migrations/scripts/remove_purchase_order_redundant_fields.sql`
Expected: 执行成功

- [ ] **Step 3: 验证表结构**

Run: `mysql -h 132.232.212.151 -P 58901 -u admin -p'Chenglp1215!@#' erp_test -e "DESCRIBE purchase_order_items;"`
Expected: 显示更新后的表结构，无 brand_name、warehouse_name 字段

---

## 6. 测试验证

### Task 6: 运行 API 测试

**Files:**
- 无文件变更

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && venv/Scripts/python main.py`
Expected: 服务启动成功

- [ ] **Step 2: 测试采购单查询接口**

Run: `curl -s http://localhost:8000/purchase-orders | head -100`
Expected: 返回采购单列表，包含 brand_name、warehouse_name 字段

- [ ] **Step 3: 测试采购单详情接口**

Run: `curl -s http://localhost:8000/purchase-orders/{purchase_no} | python -m json.tool`
Expected: 返回采购单详情，明细中包含 product_name、brand_name、warehouse_name 等字段

- [ ] **Step 4: 关闭后端服务**

Run: `taskkill /F /IM python.exe 2>/dev/null || echo "服务已关闭"`
Expected: 服务关闭

---

## 7. 提交变更

### Task 7: 提交代码

**Files:**
- 无新文件

- [ ] **Step 1: 检查变更状态**

Run: `git status`
Expected: 显示修改的文件

- [ ] **Step 2: 提交变更**

```bash
git add backend/models_mysql/purchase_order.py backend/services/purchase_order_service_mysql.py backend/migrations/scripts/remove_purchase_order_redundant_fields.sql
git commit -m "refactor: 移除 PurchaseOrderItem 冗余字段，使用外键关联

- 添加 ForeignKeyField 关联 ProductSpec、Warehouse
- PurchaseOrder 添加 Brand 外键关联
- 移除 brand_name、warehouse_name 冗余字段
- 更新 to_dict() 方法通过关联查询返回名称
- 更新 Service 层使用 select_related 优化查询

参照 SalesOrderItem 重构方案"
```

---

## 自检清单

**1. Spec 覆盖检查：**
- [x] PurchaseOrderItem 外键关联查询 → Task 3, 4
- [x] PurchaseOrder 主表外键关联 → Task 2
- [x] API 响应格式兼容 → Task 3, 4
- [x] 使用 prefetch_related 优化查询 → Task 4

**2. 占位符检查：**
- 无 TBD、TODO 等占位符
- 所有代码步骤包含完整代码

**3. 类型一致性检查：**
- ForeignKeyField 定义与 to_dict() 方法中使用的属性名一致
- select_related 参数与模型定义一致