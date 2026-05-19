# 销售单列表增强实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强销售单列表功能，新增成本明细管理、展开行查看商品明细、行选中批量操作功能

**Architecture:** 后端新增 SalesOrderCostItem 模型记录成本明细，列表接口实时计算成本和利润；前端改造列表组件支持展开行和选中功能

**Tech Stack:** Python/FastAPI/Tortoise ORM (后端), Vue 3/TypeScript (前端), MySQL (数据库)

---

## 文件结构

### 后端
- **修改**: `backend/models_mysql/sales_order.py` - 新增枚举和模型
- **修改**: `backend/services/sales_order_service_mysql.py` - 列表接口增强，成本明细服务
- **修改**: `backend/services/purchase_order_service_mysql.py` - 付款完成触发成本创建
- **修改**: `backend/app/routers/sales_order.py` - 新增成本明细和财务状态 API
- **修改**: `backend/app/routers/purchase_order.py` - 新增付款完成接口
- **新增**: `backend/scripts/migrate_sales_order_cost_fields.py` - 数据库迁移脚本

### 前端
- **修改**: `web/src/services/api.ts` - 新增 API 方法
- **修改**: `web/src/components/workspace/SalesOrderList.vue` - 列表改造

---

## Task 1: 数据库模型 - 新增枚举类型

**Files:**
- Modify: `backend/models_mysql/sales_order.py:1-40`

- [ ] **Step 1: 新增 CostType 枚举**

在 `backend/models_mysql/sales_order.py` 文件中，在 `InvoiceStatus` 枚举后添加：

```python
class CostType(str, Enum):
    """成本类型枚举"""
    PURCHASE = "purchase"      # 采购成本
    FREIGHT = "freight"        # 运费
    TRANSFER = "transfer"      # 调货费
    OTHER = "other"            # 其他


class CostSourceType(str, Enum):
    """成本来源类型枚举"""
    PURCHASE_ORDER = "purchase_order"  # 采购单
    MANUAL = "manual"                  # 手动添加


class FinanceStatus(str, Enum):
    """财务状态枚举"""
    UNPAID = "unpaid"                  # 未付款
    PARTIAL_PAID = "partial_paid"      # 部分付款
    PAID = "paid"                      # 已付款
    RECONCILED = "reconciled"          # 已对账
```

- [ ] **Step 2: 提交代码**

```bash
git add backend/models_mysql/sales_order.py
git commit -m "feat: 新增成本类型、来源类型、财务状态枚举"
```

---

## Task 2: 数据库模型 - SalesOrderCostItem 模型

**Files:**
- Modify: `backend/models_mysql/sales_order.py`

- [ ] **Step 1: 新增 SalesOrderCostItem 模型**

在 `SalesOrderItem` 模型后添加：

```python
class SalesOrderCostItem(Model):
    """销售订单成本明细"""
    id = fields.IntField(pk=True, description="成本明细ID")
    sales_order = fields.ForeignKeyField("models.SalesOrder", related_name="cost_items", on_delete=fields.CASCADE)
    cost_type = fields.CharEnumField(CostType, description="成本类型")
    amount = fields.DecimalField(max_digits=12, decimal_places=2, description="金额（未税）")
    source_type = fields.CharEnumField(CostSourceType, description="来源类型")
    source_no = fields.CharField(max_length=50, null=True, description="来源单号")
    purchase_order_id = fields.IntField(null=True, description="关联采购单ID")
    remark = fields.TextField(null=True, description="备注")
    creator_id = fields.IntField(null=True, description="创建人ID")
    creator_name = fields.CharField(max_length=100, null=True, description="创建人名称")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "sales_order_cost_items"
        ordering = ["-created_at"]

    def to_dict(self):
        return {
            "id": self.id,
            "sales_order_id": self.sales_order_id,
            "cost_type": self.cost_type.value if self.cost_type else None,
            "amount": float(self.amount),
            "source_type": self.source_type.value if self.source_type else None,
            "source_no": self.source_no,
            "purchase_order_id": self.purchase_order_id,
            "remark": self.remark,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
```

- [ ] **Step 2: 提交代码**

```bash
git add backend/models_mysql/sales_order.py
git commit -m "feat: 新增 SalesOrderCostItem 成本明细模型"
```

---

## Task 3: 数据库模型 - SalesOrder 新增字段

**Files:**
- Modify: `backend/models_mysql/sales_order.py:47-105`

- [ ] **Step 1: 在 SalesOrder 模型新增 finance_status 字段**

在 `invoice_status` 字段后添加：

```python
    finance_status = fields.CharEnumField(FinanceStatus, default=FinanceStatus.UNPAID, description="财务状态")
```

- [ ] **Step 2: 更新 SalesOrder.to_dict() 方法**

在 `to_dict()` 方法中添加 `finance_status` 字段返回：

```python
    def to_dict(self):
        return {
            # ... 现有字段 ...
            "invoice_status": self.invoice_status.value if self.invoice_status else None,
            "finance_status": self.finance_status.value if self.finance_status else None,  # 新增
            # ... 其他字段 ...
        }
```

- [ ] **Step 3: 提交代码**

```bash
git add backend/models_mysql/sales_order.py
git commit -m "feat: SalesOrder 模型新增 finance_status 字段"
```

---

## Task 4: 数据库模型 - SalesOrderItem 新增字段

**Files:**
- Modify: `backend/models_mysql/sales_order.py:108-221`

- [ ] **Step 1: 在 SalesOrderItem 模型新增字段**

在 `return_qty` 字段后添加：

```python
    exchange_qty = fields.IntField(default=0, description="换货数量")
    supplement_qty = fields.IntField(default=0, description="补货数量")
```

- [ ] **Step 2: 更新 SalesOrderItem.to_dict() 方法**

在 `to_dict()` 方法中添加新字段返回：

```python
    async def to_dict(self):
        # ... 现有代码 ...
        return {
            # ... 现有字段 ...
            "return_qty": self.return_qty,
            "exchange_qty": self.exchange_qty,      # 新增
            "supplement_qty": self.supplement_qty,  # 新增
            # ... 其他字段 ...
        }
```

- [ ] **Step 3: 提交代码**

```bash
git add backend/models_mysql/sales_order.py
git commit -m "feat: SalesOrderItem 模型新增 exchange_qty、supplement_qty 字段"
```

---

## Task 5: 数据库迁移脚本

**Files:**
- Create: `backend/scripts/migrate_sales_order_cost_fields.py`

- [ ] **Step 1: 创建迁移脚本**

```python
"""
销售单成本明细字段迁移脚本
- 创建 sales_order_cost_items 表
- sales_orders 表新增 finance_status 字段
- sales_order_items 表新增 exchange_qty、supplement_qty 字段
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.database import init_db


async def migrate():
    """执行迁移"""
    await init_db()
    conn = Tortoise.get_connection("default")

    # 1. 创建 sales_order_cost_items 表
    await conn.execute_script("""
        CREATE TABLE IF NOT EXISTS sales_order_cost_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sales_order_id INT NOT NULL,
            cost_type VARCHAR(20) NOT NULL,
            amount DECIMAL(12, 2) NOT NULL,
            source_type VARCHAR(20) NOT NULL,
            source_no VARCHAR(50),
            purchase_order_id INT,
            remark TEXT,
            creator_id INT,
            creator_name VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id) ON DELETE CASCADE,
            INDEX idx_sales_order_id (sales_order_id),
            INDEX idx_purchase_order_id (purchase_order_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    print("✓ 创建 sales_order_cost_items 表成功")

    # 2. sales_orders 表新增 finance_status 字段
    await conn.execute_script("""
        ALTER TABLE sales_orders
        ADD COLUMN IF NOT EXISTS finance_status VARCHAR(20) DEFAULT 'unpaid';
    """)
    print("✓ sales_orders 表新增 finance_status 字段成功")

    # 3. sales_order_items 表新增字段
    await conn.execute_script("""
        ALTER TABLE sales_order_items
        ADD COLUMN IF NOT EXISTS exchange_qty INT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS supplement_qty INT DEFAULT 0;
    """)
    print("✓ sales_order_items 表新增 exchange_qty、supplement_qty 字段成功")

    await Tortoise.close_connections()
    print("\n迁移完成！")


if __name__ == "__main__":
    asyncio.run(migrate())
```

- [ ] **Step 2: 执行迁移脚本**

```bash
cd backend && venv/Scripts/python scripts/migrate_sales_order_cost_fields.py
```

Expected: 输出迁移成功信息

- [ ] **Step 3: 提交代码**

```bash
git add backend/scripts/migrate_sales_order_cost_fields.py
git commit -m "feat: 新增销售单成本明细字段迁移脚本"
```

---

## Task 6: 销售单服务层 - 成本计算方法

**Files:**
- Modify: `backend/services/sales_order_service_mysql.py`

- [ ] **Step 1: 导入新模型**

在文件顶部导入部分添加：

```python
from models_mysql.sales_order import (
    SalesOrder, SalesOrderItem, SalesDeliverInfo, SalesInvoiceInfo,
    SalesOrderCostItem,  # 新增
    OrderStatus, DeliveryStatus, ReceiveStatus, InvoiceStatus, ShippingMethod,
    CostType, CostSourceType, FinanceStatus  # 新增
)
```

- [ ] **Step 2: 新增成本计算方法**

在 `SalesOrderService` 类中添加：

```python
    async def _calculate_cost_amt(self, sales_order_id: int) -> float:
        """计算销售单成本总额"""
        result = await SalesOrderCostItem.filter(
            sales_order_id=sales_order_id
        ).annotate(total=Sum("amount")).first()
        return float(result.total) if result and result.total else 0.0

    async def _calculate_profit_amt(self, sales_order_id: int, total_amt: float) -> float:
        """计算销售单利润"""
        cost_amt = await self._calculate_cost_amt(sales_order_id)
        return round(total_amt - cost_amt, 2)
```

需要导入 `Sum`:

```python
from tortoise.functions import Sum
```

- [ ] **Step 3: 提交代码**

```bash
git add backend/services/sales_order_service_mysql.py
git commit -m "feat: 销售单服务新增成本和利润计算方法"
```

---

## Task 7: 销售单服务层 - 增强列表接口

**Files:**
- Modify: `backend/services/sales_order_service_mysql.py`

- [ ] **Step 1: 修改 list_orders 方法返回成本、利润和商品明细**

修改 `list_orders` 方法：

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

        # 获取每个订单的成本、利润和商品明细
        result = []
        for order in orders:
            order_dict = order.to_dict()

            # 计算成本和利润
            cost_amt = await self._calculate_cost_amt(order.id)
            order_dict["cost_amt"] = cost_amt
            order_dict["profit_amt"] = round(order.total_amt - cost_amt, 2)

            # 获取商品明细（用于展开行）
            items = await SalesOrderItem.filter(sales_order_id=order.id).select_related(
                "spec__product__brand",
                "warehouse"
            ).order_by("row_no")
            order_dict["items"] = [await item.to_dict() for item in items]

            result.append(order_dict)

        return result, total
```

- [ ] **Step 2: 提交代码**

```bash
git add backend/services/sales_order_service_mysql.py
git commit -m "feat: 销售单列表接口返回成本、利润和商品明细"
```

---

## Task 8: 销售单服务层 - 成本明细 CRUD 方法

**Files:**
- Modify: `backend/services/sales_order_service_mysql.py`

- [ ] **Step 1: 新增成本明细 CRUD 方法**

在 `SalesOrderService` 类末尾添加：

```python
    # ============ 成本明细管理 ============

    async def create_cost_item(
        self,
        order_no: str,
        data: Dict[str, Any],
        current_user: Dict = None
    ) -> Dict[str, Any]:
        """手动创建成本明细"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        current_user = current_user or {}
        cost_item = await SalesOrderCostItem.create(
            sales_order_id=order.id,
            cost_type=data.get("cost_type"),
            amount=data.get("amount"),
            source_type=CostSourceType.MANUAL,
            remark=data.get("remark"),
            creator_id=current_user.get("id"),
            creator_name=current_user.get("full_name") or current_user.get("username"),
        )

        logger.info(f"销售单 {order_no} 创建成本明细: {cost_item.id}")
        return cost_item.to_dict()

    async def create_cost_item_from_purchase(
        self,
        sales_order_id: int,
        purchase_order_id: int,
        purchase_no: str,
        amount: float,
        current_user: Dict = None
    ) -> Optional[Dict[str, Any]]:
        """从采购单创建成本明细（采购付款完成时调用）"""
        # 检查是否已存在
        existing = await SalesOrderCostItem.filter(
            purchase_order_id=purchase_order_id
        ).first()
        if existing:
            logger.info(f"采购单 {purchase_no} 成本明细已存在，跳过创建")
            return None

        current_user = current_user or {}
        cost_item = await SalesOrderCostItem.create(
            sales_order_id=sales_order_id,
            cost_type=CostType.PURCHASE,
            amount=amount,
            source_type=CostSourceType.PURCHASE_ORDER,
            source_no=purchase_no,
            purchase_order_id=purchase_order_id,
            creator_id=current_user.get("id"),
            creator_name=current_user.get("full_name") or current_user.get("username"),
        )

        logger.info(f"销售单 {sales_order_id} 从采购单 {purchase_no} 创建成本明细")
        return cost_item.to_dict()

    async def list_cost_items(self, order_no: str) -> List[Dict[str, Any]]:
        """获取销售单成本明细列表"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        items = await SalesOrderCostItem.filter(
            sales_order_id=order.id
        ).order_by("-created_at")

        return [item.to_dict() for item in items]

    async def delete_cost_item(self, order_no: str, item_id: int) -> bool:
        """删除成本明细（仅 manual 类型可删除）"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        cost_item = await SalesOrderCostItem.filter(
            id=item_id,
            sales_order_id=order.id
        ).first()
        if not cost_item:
            raise ValueError("成本明细不存在")

        if cost_item.source_type == CostSourceType.PURCHASE_ORDER:
            raise ValueError("采购成本不可手动删除")

        await cost_item.delete()
        logger.info(f"销售单 {order_no} 删除成本明细: {item_id}")
        return True

    async def update_finance_status(self, order_no: str, finance_status: str) -> bool:
        """更新财务状态"""
        order = await SalesOrder.filter(order_no=order_no).first()
        if not order:
            raise ValueError(f"订单不存在: {order_no}")

        order.finance_status = FinanceStatus(finance_status)
        await order.save()

        logger.info(f"销售单 {order_no} 财务状态更新为: {finance_status}")
        return True
```

- [ ] **Step 2: 提交代码**

```bash
git add backend/services/sales_order_service_mysql.py
git commit -m "feat: 销售单服务新增成本明细 CRUD 和财务状态更新方法"
```

---

## Task 9: 采购单服务层 - 付款完成触发

**Files:**
- Modify: `backend/services/purchase_order_service_mysql.py`

- [ ] **Step 1: 导入销售单服务**

在文件顶部添加：

```python
from services.sales_order_service_mysql import sales_order_service_mysql as sales_order_service
```

- [ ] **Step 2: 新增付款完成方法**

在 `PurchaseOrderService` 类中添加：

```python
    async def complete_payment(
        self,
        purchase_no: str,
        current_user: Dict = None
    ) -> Dict[str, Any]:
        """付款完成 - 更新付款状态并创建成本明细"""
        purchase = await PurchaseOrder.filter(purchase_no=purchase_no).first()
        if not purchase:
            raise ValueError(f"采购单不存在: {purchase_no}")

        if purchase.pay_status == PayStatus.FULL:
            return {"message": "采购单已付款完成，无需重复操作"}

        # 更新付款状态
        old_status = purchase.pay_status
        purchase.pay_status = PayStatus.FULL
        await purchase.save()

        # 创建成本明细（如果有关联销售单）
        if purchase.source_sale_order_id:
            await sales_order_service.create_cost_item_from_purchase(
                sales_order_id=purchase.source_sale_order_id,
                purchase_order_id=purchase.id,
                purchase_no=purchase_no,
                amount=float(purchase.total_amt),
                current_user=current_user
            )

        logger.info(f"采购单 {purchase_no} 付款完成")
        return {
            "purchase_no": purchase_no,
            "pay_status": PayStatus.FULL.value,
            "cost_item_created": purchase.source_sale_order_id is not None
        }
```

- [ ] **Step 3: 提交代码**

```bash
git add backend/services/purchase_order_service_mysql.py
git commit -m "feat: 采购单服务新增付款完成方法，自动创建成本明细"
```

---

## Task 10: API 路由 - 销售单成本明细

**Files:**
- Modify: `backend/app/routers/sales_order.py`

- [ ] **Step 1: 新增成本明细路由**

在文件末尾添加：

```python
# ============ 成本明细管理 ============

@sales_order_router.get("/{order_no}/cost-items", response_model=dict, description="获取成本明细列表")
@wrap_response
async def list_cost_items(
    order_no: str,
    _: dict = Depends(require_permission("order.view"))
):
    items = await sales_order_service.list_cost_items(order_no)
    return items


@sales_order_router.post("/{order_no}/cost-items", response_model=dict, description="手动添加成本明细")
@wrap_response
async def create_cost_item(
    order_no: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.edit"))
):
    result = await sales_order_service.create_cost_item(order_no, data, current_user)
    return result


@sales_order_router.delete("/{order_no}/cost-items/{item_id}", response_model=dict, description="删除成本明细")
@wrap_response
async def delete_cost_item(
    order_no: str,
    item_id: int,
    current_user: dict = Depends(require_permission("order.edit"))
):
    await sales_order_service.delete_cost_item(order_no, item_id)
    return "成本明细删除成功"


@sales_order_router.put("/{order_no}/finance-status", response_model=dict, description="更新财务状态")
@wrap_response
async def update_finance_status(
    order_no: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_permission("order.edit"))
):
    finance_status = data.get("finance_status")
    if not finance_status:
        raise ValueError("请提供财务状态")
    await sales_order_service.update_finance_status(order_no, finance_status)
    return "财务状态更新成功"
```

- [ ] **Step 2: 提交代码**

```bash
git add backend/app/routers/sales_order.py
git commit -m "feat: 销售单路由新增成本明细和财务状态 API"
```

---

## Task 11: API 路由 - 采购单付款完成

**Files:**
- Modify: `backend/app/routers/purchase_order.py`

- [ ] **Step 1: 新增付款完成路由**

在文件末尾添加：

```python
@purchase_order_router.post("/{purchase_no}/complete-payment", response_model=dict, description="付款完成")
@wrap_response
async def complete_payment(
    purchase_no: str,
    current_user: dict = Depends(require_permission("order.edit"))
):
    result = await purchase_order_service.complete_payment(purchase_no, current_user)
    return result
```

- [ ] **Step 2: 提交代码**

```bash
git add backend/app/routers/purchase_order.py
git commit -m "feat: 采购单路由新增付款完成接口"
```

---

## Task 12: 前端 API 服务 - 新增方法

**Files:**
- Modify: `web/src/services/api.ts`

- [ ] **Step 1: 在 salesOrderApi 中新增方法**

在 `salesOrderApi` 对象中添加：

```typescript
  // 获取成本明细列表
  getCostItems: (orderNo: string) => {
    return apiService.get<any>(`/sales-orders/${orderNo}/cost-items`)
  },

  // 手动添加成本明细
  createCostItem: (orderNo: string, data: { cost_type: string; amount: number; remark?: string }) => {
    return apiService.post<any>(`/sales-orders/${orderNo}/cost-items`, data)
  },

  // 删除成本明细
  deleteCostItem: (orderNo: string, itemId: number) => {
    return apiService.delete<any>(`/sales-orders/${orderNo}/cost-items/${itemId}`)
  },

  // 更新财务状态
  updateFinanceStatus: (orderNo: string, financeStatus: string) => {
    return apiService.put<any>(`/sales-orders/${orderNo}/finance-status`, { finance_status: financeStatus })
  },
```

- [ ] **Step 2: 在 purchaseOrderApi 中新增方法**

在 `purchaseOrderApi` 对象中添加：

```typescript
  // 付款完成
  completePayment: (purchaseNo: string) => {
    return apiService.post<any>(`/purchase-orders/${purchaseNo}/complete-payment`)
  },
```

- [ ] **Step 3: 提交代码**

```bash
git add web/src/services/api.ts
git commit -m "feat: 前端 API 新增成本明细和付款完成方法"
```

---

## Task 13: 前端列表组件 - 新增列配置

**Files:**
- Modify: `web/src/components/workspace/SalesOrderList.vue`

- [ ] **Step 1: 更新接口类型定义**

修改 `SalesOrder` 接口：

```typescript
interface SalesOrderItem {
  id: number
  row_no: number
  product_id: number | null
  product_name: string | null
  product_code: string | null
  spec_id: number | null
  spec_code: string | null
  brand_id: number | null
  brand_name: string | null
  warehouse_id: number | null
  warehouse_name: string | null
  qty: number
  price: number
  discount: number
  discounted_price: number | null
  amt: number | null
  shipping_method: string | null
  pushed: boolean
  out_qty: number
  return_qty: number
  exchange_qty: number      // 新增
  supplement_qty: number    // 新增
  created_at: string
  updated_at: string
}

interface SalesOrder {
  id: number
  order_no: string
  order_date: string
  customer_id: number
  customer_name: string
  sale_user_id: number | null
  sale_user_name: string | null
  order_status: string
  delivery_status: string
  receive_status: string
  invoice_status: string
  finance_status: string    // 新增
  total_amt: number
  tax_rate: number
  tax_amt: number
  total_tax_amt: number
  total_discount_amt: number
  cost_amt: number         // 新增
  profit_amt: number       // 新增
  expect_deliver_date: string | null
  settle_type: string | null
  remark: string | null
  creator_id: number | null
  creator_name: string | null
  created_at: string
  updated_at: string
  items: SalesOrderItem[]  // 新增
}
```

- [ ] **Step 2: 新增财务状态映射**

在 `statusMap` 后添加：

```typescript
const financeStatusMap: Record<string, { label: string; class: string }> = {
  unpaid: { label: '未付款', class: 'none' },
  partial_paid: { label: '部分付款', class: 'partial' },
  paid: { label: '已付款', class: 'full' },
  reconciled: { label: '已对账', class: 'closed' }
}

const getFinanceStatusInfo = (status: string) => financeStatusMap[status] || { label: status, class: '' }
```

- [ ] **Step 3: 提交代码**

```bash
git add web/src/components/workspace/SalesOrderList.vue
git commit -m "feat: 前端销售单列表新增类型定义和状态映射"
```

---

## Task 14: 前端列表组件 - 表格列调整

**Files:**
- Modify: `web/src/components/workspace/SalesOrderList.vue`

- [ ] **Step 1: 修改表头列配置**

将 `<thead>` 部分替换为：

```html
<thead>
  <tr>
    <th style="width: 40px">
      <input type="checkbox" @change="handleSelectAll" :checked="isAllSelected" />
    </th>
    <th style="width: 40px"></th>
    <th style="width: 110px">订单日期</th>
    <th style="width: 130px">订单编号</th>
    <th>客户名称</th>
    <th style="width: 100px; text-align: right">订单金额</th>
    <th style="width: 80px">订单状态</th>
    <th style="width: 80px; text-align: right">成本</th>
    <th style="width: 80px; text-align: right">利润</th>
    <th style="width: 80px">财务状态</th>
    <th style="width: 80px">发票状态</th>
    <th style="width: 80px">发货状态</th>
    <th style="width: 80px">收货状态</th>
    <th style="width: 80px">业务员</th>
    <th style="width: 200px">操作</th>
  </tr>
</thead>
```

- [ ] **Step 2: 修改表格数据行**

将 `<tbody>` 中的数据行替换为：

```html
<tbody>
  <tr v-if="loading">
    <td colspan="15" class="loading-cell">加载中...</td>
  </tr>
  <tr v-else-if="orders.length === 0">
    <td colspan="15" class="empty-cell">暂无数据</td>
  </tr>
  <template v-else v-for="order in orders" :key="order.order_no">
    <tr :class="{ 'selected-row': selectedOrders.includes(order.order_no) }">
      <td>
        <input
          type="checkbox"
          :checked="selectedOrders.includes(order.order_no)"
          @change="handleSelectOrder(order.order_no)"
        />
      </td>
      <td>
        <button class="expand-btn" @click="toggleExpand(order.order_no)">
          {{ expandedRows.includes(order.order_no) ? '▼' : '▶' }}
        </button>
      </td>
      <td>{{ formatDate(order.order_date) }}</td>
      <td>{{ order.order_no }}</td>
      <td>{{ order.customer_name }}</td>
      <td style="text-align: right">{{ formatAmount(order.total_tax_amt) }}</td>
      <td>
        <span class="status-tag" :class="getStatusInfo(order.order_status).class">
          {{ getStatusInfo(order.order_status).label }}
        </span>
      </td>
      <td style="text-align: right">{{ formatAmount(order.cost_amt) }}</td>
      <td style="text-align: right" :class="{ 'profit-positive': order.profit_amt >= 0, 'profit-negative': order.profit_amt < 0 }">
        {{ formatAmount(order.profit_amt) }}
      </td>
      <td>
        <span class="status-tag" :class="getFinanceStatusInfo(order.finance_status).class">
          {{ getFinanceStatusInfo(order.finance_status).label }}
        </span>
      </td>
      <td>
        <span class="status-tag" :class="getStatusInfo(order.invoice_status).class">
          {{ getStatusInfo(order.invoice_status).label }}
        </span>
      </td>
      <td>
        <span class="status-tag" :class="getStatusInfo(order.delivery_status).class">
          {{ getStatusInfo(order.delivery_status).label }}
        </span>
      </td>
      <td>
        <span class="status-tag" :class="getStatusInfo(order.receive_status).class">
          {{ getStatusInfo(order.receive_status).label }}
        </span>
      </td>
      <td>{{ order.sale_user_name || '-' }}</td>
      <td>
        <div class="action-buttons">
          <button class="btn-link" @click="openDetail(order)">详情</button>
          <button class="btn-link" @click="openEditOrder(order)" v-if="order.order_status === 'draft'">编辑</button>
          <button class="btn-link highlight" @click="handleSubmitOrder(order.order_no)" v-if="order.order_status === 'draft'">提交审核</button>
          <button class="btn-link success" @click="handleApproveOrder(order.order_no)" v-if="order.order_status === 'pending'">审核通过</button>
          <button class="btn-link warning" @click="handleRejectOrder(order.order_no)" v-if="order.order_status === 'pending'">驳回</button>
          <button class="btn-link danger" @click="confirmDelete(order.order_no)" v-if="order.order_status === 'draft'">删除</button>
        </div>
      </td>
    </tr>
    <!-- 展开行 - 商品明细 -->
    <tr v-if="expandedRows.includes(order.order_no)" class="expanded-row">
      <td colspan="15">
        <div class="expanded-content">
          <table class="items-detail-table">
            <thead>
              <tr>
                <th>品牌名</th>
                <th>规格编号</th>
                <th>产品名称</th>
                <th>规格</th>
                <th>包装单位</th>
                <th style="text-align: right">数量</th>
                <th style="text-align: right">原价</th>
                <th style="text-align: right">退货数量</th>
                <th style="text-align: right">换货数量</th>
                <th style="text-align: right">补货数量</th>
                <th style="text-align: right">含税单价</th>
                <th style="text-align: right">合计</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in order.items" :key="item.id">
                <td>{{ item.brand_name || '-' }}</td>
                <td>{{ item.spec_code || '-' }}</td>
                <td>{{ item.product_name || '-' }}</td>
                <td>{{ item.sales_spec || '-' }}</td>
                <td>{{ item.packaging || '-' }}</td>
                <td style="text-align: right">{{ item.qty }}</td>
                <td style="text-align: right">{{ formatAmount(item.price) }}</td>
                <td style="text-align: right">{{ item.return_qty }}</td>
                <td style="text-align: right">{{ item.exchange_qty }}</td>
                <td style="text-align: right">{{ item.supplement_qty }}</td>
                <td style="text-align: right">{{ formatAmount(item.price * (1 + (order.tax_rate || 0.13))) }}</td>
                <td style="text-align: right">{{ formatAmount(item.amt || 0) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </td>
    </tr>
  </template>
</tbody>
```

- [ ] **Step 3: 提交代码**

```bash
git add web/src/components/workspace/SalesOrderList.vue
git commit -m "feat: 前端销售单列表表格列调整，新增展开行"
```

---

## Task 15: 前端列表组件 - 状态管理

**Files:**
- Modify: `web/src/components/workspace/SalesOrderList.vue`

- [ ] **Step 1: 新增状态变量**

在 `// State` 部分添加：

```typescript
// 展开行状态
const expandedRows = ref<string[]>([])

// 选中行状态
const selectedOrders = ref<string[]>([])

// 计算属性：是否全选
const isAllSelected = computed(() => {
  return orders.value.length > 0 && selectedOrders.value.length === orders.value.length
})
```

- [ ] **Step 2: 新增展开/选中方法**

在 `// Methods` 部分添加：

```typescript
// 展开/收起行
const toggleExpand = (orderNo: string) => {
  const index = expandedRows.value.indexOf(orderNo)
  if (index === -1) {
    expandedRows.value.push(orderNo)
  } else {
    expandedRows.value.splice(index, 1)
  }
}

// 选中/取消选中订单
const handleSelectOrder = (orderNo: string) => {
  const index = selectedOrders.value.indexOf(orderNo)
  if (index === -1) {
    selectedOrders.value.push(orderNo)
  } else {
    selectedOrders.value.splice(index, 1)
  }
}

// 全选/取消全选
const handleSelectAll = () => {
  if (isAllSelected.value) {
    selectedOrders.value = []
  } else {
    selectedOrders.value = orders.value.map(o => o.order_no)
  }
}

// 清除选择
const clearSelection = () => {
  selectedOrders.value = []
}

// 批量提交审核
const handleBatchSubmit = async () => {
  if (selectedOrders.value.length === 0) {
    window.showToast('请选择要提交的订单', 'warning')
    return
  }

  let successCount = 0
  let skipCount = 0

  for (const orderNo of selectedOrders.value) {
    const order = orders.value.find(o => o.order_no === orderNo)
    if (order && order.order_status === 'draft') {
      try {
        await salesOrderApi.submit(orderNo)
        successCount++
      } catch (error) {
        console.error(`提交订单 ${orderNo} 失败:`, error)
      }
    } else {
      skipCount++
    }
  }

  if (successCount > 0) {
    window.showToast(`成功提交 ${successCount} 个订单`, 'success')
    loadOrders()
    clearSelection()
  }
  if (skipCount > 0) {
    window.showToast(`跳过 ${skipCount} 个非草稿状态订单`, 'info')
  }
}
```

- [ ] **Step 3: 提交代码**

```bash
git add web/src/components/workspace/SalesOrderList.vue
git commit -m "feat: 前端销售单列表新增展开和选中状态管理"
```

---

## Task 16: 前端列表组件 - 批量操作按钮

**Files:**
- Modify: `web/src/components/workspace/SalesOrderList.vue`

- [ ] **Step 1: 在表头区域添加批量操作按钮**

在 `<div class="workspace-header">` 后添加：

```html
<div class="batch-actions" v-if="selectedOrders.length > 0">
  <span class="selected-count">已选择 {{ selectedOrders.length }} 条</span>
  <button class="batch-btn" @click="handleBatchSubmit">批量提交审核</button>
  <button class="batch-btn secondary" @click="clearSelection">取消选择</button>
</div>
```

- [ ] **Step 2: 添加样式**

在 `<style scoped>` 部分添加：

```css
/* 展开行样式 */
.expand-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  font-size: 12px;
}

.expand-btn:hover {
  color: var(--accent-blue);
}

.expanded-row {
  background-color: var(--bg-secondary);
}

.expanded-content {
  padding: 12px 20px;
}

.items-detail-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--bg-card);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.items-detail-table th,
.items-detail-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid var(--border-color);
  font-size: 12px;
}

.items-detail-table th {
  color: var(--text-muted);
  background-color: var(--bg-secondary);
}

.items-detail-table td {
  color: var(--text-primary);
}

/* 选中行样式 */
.selected-row {
  background-color: rgba(0, 120, 212, 0.05) !important;
}

/* 利润样式 */
.profit-positive {
  color: var(--accent-green);
}

.profit-negative {
  color: var(--accent-red);
}

/* 批量操作样式 */
.batch-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background-color: rgba(0, 120, 212, 0.1);
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}

.selected-count {
  font-size: 14px;
  color: var(--accent-blue);
  font-weight: 500;
}

.batch-btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  background-color: var(--accent-blue);
  color: white;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.batch-btn:hover {
  background-color: var(--accent-blue-hover);
}

.batch-btn.secondary {
  background-color: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.batch-btn.secondary:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}
```

- [ ] **Step 3: 提交代码**

```bash
git add web/src/components/workspace/SalesOrderList.vue
git commit -m "feat: 前端销售单列表新增批量操作按钮和样式"
```

---

## Task 17: 验证测试

**Files:**
- 无新增文件

- [ ] **Step 1: 启动后端服务**

```bash
cd backend && venv/Scripts/python -m uvicorn app.main:app --reload
```

Expected: 服务启动成功

- [ ] **Step 2: 验证数据库迁移**

检查数据库中：
- `sales_order_cost_items` 表存在
- `sales_orders` 表有 `finance_status` 字段
- `sales_order_items` 表有 `exchange_qty`、`supplement_qty` 字段

- [ ] **Step 3: 验证销售单列表接口**

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/sales-orders/
```

Expected: 返回数据包含 `cost_amt`、`profit_amt`、`items` 字段

- [ ] **Step 4: 验证成本明细 API**

```bash
# 创建成本明细
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"cost_type":"freight","amount":100,"remark":"运费"}' \
  http://localhost:8000/api/v1/sales-orders/<order_no>/cost-items

# 获取成本明细列表
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/sales-orders/<order_no>/cost-items
```

Expected: 成本明细创建和查询成功

- [ ] **Step 5: 验证前端列表显示**

启动前端开发服务器，访问销售单列表页面：
- 新列（成本、利润、财务状态等）正常显示
- 展开行功能正常
- 选中功能正常
- 批量操作功能正常

- [ ] **Step 6: 最终提交**

```bash
git add -A
git commit -m "feat: 销售单列表增强功能完成 - 成本明细、展开行、批量操作"
```

---

## Self-Review Checklist

**1. Spec Coverage:**
- [x] 成本明细模型结构 - Task 1, 2
- [x] 成本金额计算 - Task 6, 7
- [x] 利润计算 - Task 6, 7
- [x] 防止重复成本明细 - Task 8 (create_cost_item_from_purchase 检查)
- [x] 成本明细 CRUD API - Task 8, 10
- [x] 展开行 UI - Task 14
- [x] 商品明细列 - Task 14
- [x] 含税单价计算 - Task 14 (前端计算)
- [x] 列表 API 返回 items - Task 7
- [x] 列表列配置 - Task 14
- [x] 财务状态字段 - Task 3
- [x] 明细新字段 - Task 4
- [x] 行选中 UI - Task 14, 15
- [x] 批量操作 - Task 15, 16

**2. Placeholder Scan:**
- 无 TBD、TODO 等占位符
- 所有代码步骤包含完整代码

**3. Type Consistency:**
- `SalesOrderCostItem` 模型字段与 API 返回一致
- `SalesOrder` 新增字段 `finance_status` 与前端类型一致
- `SalesOrderItem` 新增字段 `exchange_qty`、`supplement_qty` 与前端一致
- 方法名 `create_cost_item_from_purchase` 在 Task 8 定义，Task 9 调用

---

计划完成并保存到 `docs/superpowers/plans/2026-05-19-enhance-sales-order-list-columns.md`。

**两种执行方式：**

**1. Subagent-Driven (推荐)** - 我为每个任务派发一个新的子代理，任务间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中使用 executing-plans 执行，批量执行并设置检查点审查

**选择哪种方式？**
