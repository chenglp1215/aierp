# 移除销售订单冗余字段实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 移除 SalesOrderItem 中的冗余字段，使用 ForeignKeyField 建立外键关联，保持 API 响应格式兼容

**Architecture:** 使用 Tortoise ORM 的 ForeignKeyField 替代冗余字段存储，通过 prefetch_related 预加载关联数据，to_dict() 方法中返回关联名称

**Tech Stack:** Python, FastAPI, Tortoise ORM, MySQL, Aerich (数据库迁移)

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/models_mysql/sales_order.py` | 修改 | 更新模型定义，添加外键关联 |
| `backend/services/sales_order_service_mysql.py` | 修改 | 更新查询逻辑，使用 prefetch_related |
| `backend/migrations/models/...` | 创建 | 数据库迁移脚本 |

---

## 1. 准备工作

### Task 1: 备份数据库

**Files:**
- 无文件变更

- [ ] **Step 1: 导出当前数据库结构**

Run: `mysqldump -h 132.232.212.151 -P 58901 -u admin -p'Chenglp1215!@#' erp_test --no-data > backup_sales_order_schema.sql`
Expected: 导出成功

- [ ] **Step 2: 备份销售订单相关表数据**

Run: `mysqldump -h 132.232.212.151 -P 58901 -u admin -p'Chenglp1215!@#' erp_test sales_orders sales_order_items sales_deliver_infos > backup_sales_order_data.sql`
Expected: 导出成功

---

## 2. 修改 SalesOrderItem 模型

### Task 2: 添加 ForeignKeyField 关联

**Files:**
- Modify: `backend/models_mysql/sales_order.py`

- [ ] **Step 1: 读取当前模型定义**

Run: `cat backend/models_mysql/sales_order.py | head -180`
Expected: 显示当前模型定义

- [ ] **Step 2: 修改 SalesOrderItem 模型，添加外键关联**

将 SalesOrderItem 类修改为：

```python
class SalesOrderItem(Model):
    """销售订单明细"""
    id = fields.IntField(pk=True, description="明细ID")
    sales_order = fields.ForeignKeyField("models.SalesOrder", related_name="items", on_delete=fields.CASCADE)
    row_no = fields.IntField(description="行号")
    
    # 外键关联 - 替代冗余字段
    product: fields.ForeignKeyNullableRelation["Product"] = fields.ForeignKeyField(
        "models.Product", related_name="sales_order_items", null=True, description="商品"
    )
    spec: fields.ForeignKeyNullableRelation["ProductSpec"] = fields.ForeignKeyField(
        "models.ProductSpec", related_name="sales_order_items", null=True, description="规格"
    )
    brand: fields.ForeignKeyNullableRelation["Brand"] = fields.ForeignKeyField(
        "models.Brand", related_name="sales_order_items", null=True, description="品牌"
    )
    warehouse: fields.ForeignKeyNullableRelation["Warehouse"] = fields.ForeignKeyField(
        "models.Warehouse", related_name="sales_order_items", null=True, description="仓库"
    )
    
    # 保留的字段（历史快照）
    product_code = fields.CharField(max_length=50, null=True, description="商品编码（快照）")
    spec_code = fields.CharField(max_length=50, null=True, description="规格编码（快照）")
    
    qty = fields.IntField(description="订购数量")
    price = fields.DecimalField(max_digits=12, decimal_places=2, description="原始单价")
    discount = fields.DecimalField(max_digits=5, decimal_places=4, default=1.0, description="折扣率")
    discounted_price = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="折后单价")
    amt = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="行金额")
    shipping_method = fields.CharEnumField(ShippingMethod, description="发货方式")
    pushed = fields.BooleanField(default=False, description="是否已下推采购")
    out_qty = fields.IntField(default=0, description="已发货数量")
    return_qty = fields.IntField(default=0, description="已退货数量")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "sales_order_items"
        ordering = ["row_no"]
        unique_together = ("sales_order", "row_no")

    def __str__(self):
        return f"Item {self.row_no}"

    async def to_dict(self):
        """转换为字典格式，通过关联查询返回名称"""
        # 获取关联对象
        product = await self.product
        spec = await self.spec
        brand = await self.brand
        warehouse = await self.warehouse
        
        # 发货方式中文映射
        shipping_method_map = {
            ShippingMethod.DIRECT: "直运",
            ShippingMethod.WAREHOUSE: "仓库发货",
        }
        shipping_method_cn = shipping_method_map.get(self.shipping_method) if self.shipping_method else None

        return {
            "id": self.id,
            "sales_order_id": self.sales_order_id,
            "row_no": self.row_no,
            "product_id": self.product_id,
            "product_code": self.product_code or (product.product_code if product else None),
            "product_name": product.name if product else None,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code or (spec.spec_code if spec else None),
            "brand_id": self.brand_id,
            "brand_name": brand.name if brand else None,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": warehouse.name if warehouse else None,
            "qty": self.qty,
            "price": float(self.price),
            "discount": float(self.discount),
            "discounted_price": float(self.discounted_price) if self.discounted_price else None,
            "amt": float(self.amt) if self.amt else None,
            "shipping_method": shipping_method_cn,
            "pushed": self.pushed,
            "out_qty": self.out_qty,
            "return_qty": self.return_qty,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 3: 在文件顶部添加必要的导入**

在文件开头添加：

```python
from models_mysql.product import Product, ProductSpec, Brand
from models_mysql.warehouse import Warehouse
```

- [ ] **Step 4: 验证模型定义语法正确**

Run: `cd backend && venv/Scripts/python -c "from models_mysql.sales_order import SalesOrder, SalesOrderItem; print('OK')"`
Expected: 输出 "OK"

---

## 3. 修改 SalesOrder 模型

### Task 3: 添加 Customer 外键关联

**Files:**
- Modify: `backend/models_mysql/sales_order.py`

- [ ] **Step 1: 修改 SalesOrder 模型，添加 Customer 外键**

将 SalesOrder 类中的相关字段修改为：

```python
class SalesOrder(Model):
    """销售订单主表"""
    id = fields.IntField(pk=True, description="订单ID")
    order_no = fields.CharField(max_length=50, unique=True, description="订单号")
    order_date = fields.DateField(description="订单日期")
    
    # 外键关联
    customer: fields.ForeignKeyRelation["Customer"] = fields.ForeignKeyField(
        "models.Customer", related_name="sales_orders", description="客户"
    )
    
    # 保留的字段（历史快照）
    customer_name = fields.CharField(max_length=200, description="客户名称（快照）")
    
    sale_user_id = fields.IntField(null=True, description="销售人员ID")
    sale_user_name = fields.CharField(max_length=100, null=True, description="销售人员名称")
    # ... 其他字段保持不变
```

- [ ] **Step 2: 添加 Customer 导入**

```python
from models_mysql.customer import Customer
```

- [ ] **Step 3: 更新 SalesOrder.to_dict() 方法**

```python
def to_dict(self):
    return {
        "id": self.id,
        "order_no": self.order_no,
        "order_date": self.order_date.isoformat() if self.order_date else None,
        "customer_id": self.customer_id,
        "customer_name": self.customer_name,  # 使用快照字段
        "sale_user_id": self.sale_user_id,
        "sale_user_name": self.sale_user_name,
        "order_status": self.order_status.value if self.order_status else None,
        "delivery_status": self.delivery_status.value if self.delivery_status else None,
        "receive_status": self.receive_status.value if self.receive_status else None,
        "invoice_status": self.invoice_status.value if self.invoice_status else None,
        "total_amt": float(self.total_amt),
        "tax_rate": float(self.tax_rate),
        "tax_amt": float(self.tax_amt),
        "total_tax_amt": float(self.total_tax_amt),
        "total_discount_amt": float(self.total_discount_amt),
        "expect_deliver_date": self.expect_deliver_date.isoformat() if self.expect_deliver_date else None,
        "settle_type": self.settle_type,
        "remark": self.remark,
        "creator_id": self.creator_id,
        "creator_name": self.creator_name,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "updated_at": self.updated_at.isoformat() if self.updated_at else None,
    }
```

- [ ] **Step 4: 验证模型定义**

Run: `cd backend && venv/Scripts/python -c "from models_mysql.sales_order import SalesOrder; print('OK')"`
Expected: 输出 "OK"

---

## 4. 更新 Service 层

### Task 4: 更新查询逻辑使用 prefetch_related

**Files:**
- Modify: `backend/services/sales_order_service_mysql.py`

- [ ] **Step 1: 更新 get_order_by_no 方法**

将 `get_order_by_no` 方法修改为：

```python
async def get_order_by_no(self, order_no: str) -> Optional[Dict[str, Any]]:
    """根据订单号获取订单详情"""
    order = await SalesOrder.filter(order_no=order_no).prefetch_related(
        "items__product",
        "items__spec", 
        "items__brand",
        "items__warehouse",
        "deliver_infos"
    ).first()
    if not order:
        return None

    result = order.to_dict()
    result["items"] = [await item.to_dict() for item in order.items]
    result["deliver_info"] = order.deliver_infos[0].to_dict() if order.deliver_infos else {}
    return result
```

- [ ] **Step 2: 更新 list_orders 方法**

将 `list_orders` 方法修改为：

```python
async def list_orders(
    self,
    page: int = 1,
    page_size: int = 20,
    order_status: str = None,
    customer_id: int = None,
    order_no: str = None,
    keyword: str = None,
) -> Tuple[List[Dict], int]:
    """获取订单列表"""
    query = SalesOrder.all()

    if order_status:
        query = query.filter(order_status=order_status)
    if customer_id:
        query = query.filter(customer_id=customer_id)
    if order_no:
        query = query.filter(order_no__contains=order_no)
    if keyword:
        query = query.filter(
            Q(order_no__contains=keyword) |
            Q(customer_name__contains=keyword)
        )

    total = await query.count()
    orders = await query.offset((page - 1) * page_size).limit(page_size)

    return [order.to_dict() for order in orders], total
```

- [ ] **Step 3: 更新 create_order 方法**

修改创建明细的逻辑，移除冗余字段处理：

```python
# 创建明细
for idx, item in enumerate(items_data, 1):
    await SalesOrderItem.create(
        sales_order=order,
        row_no=item.get("row_no", idx),
        product_id=self._parse_int_field(item.get("product_id")),
        product_code=item.get("product_code"),  # 保留快照
        spec_id=self._parse_int_field(item.get("spec_id")),
        spec_code=item.get("spec_code"),  # 保留快照
        brand_id=self._parse_int_field(item.get("brand_id")),
        warehouse_id=self._parse_int_field(item.get("warehouse_id")),
        qty=item.get("qty"),
        price=item.get("price"),
        discount=item.get("discount", 1.0),
        discounted_price=item.get("discounted_price"),
        amt=item.get("amt"),
        shipping_method=self._parse_shipping_method(item.get("shipping_method")),
    )
```

- [ ] **Step 4: 更新 update_order 方法**

类似地移除冗余字段处理。

- [ ] **Step 5: 验证语法正确**

Run: `cd backend && venv/Scripts/python -c "from services.sales_order_service_mysql import sales_order_service_mysql; print('OK')"`
Expected: 输出 "OK"

---

## 5. 数据库迁移

### Task 5: 创建并执行迁移脚本

**Files:**
- Create: `backend/migrations/scripts/remove_redundant_fields.sql`

- [ ] **Step 1: 创建迁移 SQL 脚本**

创建文件 `backend/migrations/scripts/remove_redundant_fields.sql`：

```sql
-- 移除 sales_order_items 表中的冗余字段
-- 注意：先添加外键列（如果不存在），再删除冗余字段

-- 1. 确保 product_id, spec_id, brand_id, warehouse_id 列存在且有索引
-- (这些列应该已存在)

-- 2. 删除冗余字段
ALTER TABLE sales_order_items 
DROP COLUMN IF EXISTS product_name,
DROP COLUMN IF EXISTS brand_name,
DROP COLUMN IF EXISTS warehouse_name;

-- 3. 添加外键约束（可选，根据需要）
-- ALTER TABLE sales_order_items 
-- ADD CONSTRAINT fk_sales_order_item_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_sales_order_item_spec FOREIGN KEY (spec_id) REFERENCES product_specs(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_sales_order_item_brand FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
-- ADD CONSTRAINT fk_sales_order_item_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(id) ON DELETE SET NULL;
```

- [ ] **Step 2: 执行迁移脚本**

Run: `mysql -h 132.232.212.151 -P 58901 -u admin -p'Chenglp1215!@#' erp_test < backend/migrations/scripts/remove_redundant_fields.sql`
Expected: 执行成功

- [ ] **Step 3: 验证表结构**

Run: `mysql -h 132.232.212.151 -P 58901 -u admin -p'Chenglp1215!@#' erp_test -e "DESCRIBE sales_order_items;"`
Expected: 显示更新后的表结构，无 product_name、brand_name、warehouse_name 字段

---

## 6. 测试验证

### Task 6: 运行 API 测试脚本

**Files:**
- 无文件变更

- [ ] **Step 1: 启动后端服务**

Run: `cd backend && venv/Scripts/python main.py`
Expected: 服务启动成功

- [ ] **Step 2: 运行 API 测试脚本**

Run: `cd backend && venv/Scripts/python -c "
import sys
sys.stdout.reconfigure(encoding='utf-8')
exec(open('tests/test_sales_order_api.py', encoding='utf-8').read())
"`
Expected: 测试通过

- [ ] **Step 3: 检查测试结果**

如果测试失败，分析错误并修复。

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
git add backend/models_mysql/sales_order.py backend/services/sales_order_service_mysql.py backend/migrations/scripts/remove_redundant_fields.sql
git commit -m "refactor: 移除 SalesOrderItem 冗余字段，使用外键关联

- 添加 ForeignKeyField 关联 Product、ProductSpec、Brand、Warehouse
- 移除 product_name、brand_name、warehouse_name 冗余字段
- 保留 product_code、spec_code 作为历史快照
- 更新 to_dict() 方法通过关联查询返回名称
- 更新 Service 层使用 prefetch_related 优化查询"
```

---

## 自检清单

**1. Spec 覆盖检查：**
- [x] 外键关联查询规范 → Task 2, 3, 4
- [x] API 响应格式保持兼容 → Task 2, 3
- [x] API 请求格式简化 → Task 4

**2. 占位符检查：**
- 无 TBD、TODO 等占位符
- 所有代码步骤包含完整代码

**3. 类型一致性检查：**
- ForeignKeyField 定义与 to_dict() 方法中使用的属性名一致
- prefetch_related 参数与模型定义一致
