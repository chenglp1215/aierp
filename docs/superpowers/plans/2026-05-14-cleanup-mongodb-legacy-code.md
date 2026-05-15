# MongoDB 历史代码清理实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理 MongoDB 相关的客户管理和库存管理历史代码，确保所有模块使用 MySQL 实现。

**Architecture:** 按依赖关系从顶层到底层清理：先更新导入引用，再删除服务和模型文件，最后清理路由。

**Tech Stack:** Python, FastAPI, Tortoise ORM (MySQL), Pydantic

---

## 文件结构

**将删除的文件：**
- `backend/models/customer.py` - MongoDB 客户模型
- `backend/models/inventory.py` - MongoDB 库存模型
- `backend/models/province_city.py` - 省市数据模型（已无实际使用）
- `backend/services/customer_service.py` - MongoDB 客户服务
- `backend/services/inventory_service.py` - MongoDB 库存服务

**保留的文件（前端仍在使用）：**
- `backend/services/province_city_service.py` - 省市服务（数据硬编码，前端调用 `/api/province-city/`）
- `backend/app/routers/province_city.py` - 省市路由（前端使用）
- `backend/app/routers/prompts/province_city.py` - 省市提示词（被 customer.py 使用）

**将修改的文件：**
- `backend/models/__init__.py` - 移除 MongoDB 模型导出
- `backend/app/agent/tools/customer.py` - 更新服务导入
- `backend/app/agent/tools/customer.py` - 更新服务导入
- `backend/app/agent/tools/inventory.py` - 更新服务导入

---

### Task 1: 更新 models/__init__.py

**Files:**
- Modify: `backend/models/__init__.py`

- [ ] **Step 1: 移除 MongoDB 模型导入和导出**

修改 `backend/models/__init__.py`，删除以下内容：

删除导入：
```python
# 删除这些行
from .customer import (
    CustomerBase,
    CustomerType,
    CustomerStatus,
    CustomerDiscount,
)
from .inventory import (
    Warehouse,
    WarehouseListResponse,
    WarehouseStatus,
    StockStatus,
    InboundBatch,
    OutboundBatch,
    Stock,
    StockListResponse,
)
```

删除 `__all__` 中的导出：
```python
# 从 __all__ 中删除这些项
"CustomerBase",
"CustomerType",
"CustomerStatus",
"CustomerDiscount",
"Warehouse",
"WarehouseCreate",
"WarehouseUpdate",
"WarehouseListResponse",
"WarehouseStatus",
"Stock",
"StockListResponse",
"InboundBatch",
"OutboundBatch",
```

最终文件内容：
```python
from .sales_order import (
    SalesOrder,
    SalesOrderCreate,
    SalesOrderUpdate,
    SalesOrderItem,
    OrderStatus,
    DeliveryStatus,
    ReceiveStatus,
    InvoiceStatus,
    SettleType,
    ShippingMethod,
    DeliverInfo,
    InvoiceInfo,
    OrderStatusInfo,
)
from .purchase_order import (
    PurchaseOrder,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseOrderListResponse,
    PurchaseStatus,
    InStatus,
    PayStatus,
    PurchaseType,
    SettleType as PurchaseSettleType,
    ReceiveInfo,
    PurchaseStatusInfo,
    PurchaseOrderItem,
    PurchaseStatusUpdate,
    InStatusUpdate,
    PayStatusUpdate,
)
from .accounts_receivable import (
    Receivable,
    ReceivableCreate,
    ReceivableUpdate,
    ReceivableListResponse,
    ReceivableStatus,
    ReceivableRecord,
    ReceivableRecordCreate,
    PaymentMethod,
)

__all__ = [
    "SalesOrder",
    "SalesOrderCreate",
    "SalesOrderUpdate",
    "SalesOrderItem",
    "OrderStatus",
    "DeliveryStatus",
    "ReceiveStatus",
    "InvoiceStatus",
    "SettleType",
    "ShippingMethod",
    "DeliverInfo",
    "InvoiceInfo",
    "OrderStatusInfo",
    "PurchaseOrder",
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderListResponse",
    "PurchaseStatus",
    "InStatus",
    "PayStatus",
    "PurchaseType",
    "PurchaseSettleType",
    "ReceiveInfo",
    "PurchaseStatusInfo",
    "PurchaseOrderItem",
    "PurchaseStatusUpdate",
    "InStatusUpdate",
    "PayStatusUpdate",
    "Receivable",
    "ReceivableCreate",
    "ReceivableUpdate",
    "ReceivableListResponse",
    "ReceivableStatus",
    "ReceivableRecord",
    "ReceivableRecordCreate",
    "PaymentMethod",
]
```

- [ ] **Step 2: 验证修改**

运行: `cd backend && python -c "from models import *; print('OK')"`
预期: 输出 "OK"，无错误

---

### Task 2: 更新 Agent Tools - customer.py（简化处理）

**Files:**
- Modify: `backend/app/agent/tools/customer.py`

**注意：** 简化处理，只需确保服务启动不报错。后续会重新对接 agent 模块。

- [ ] **Step 1: 更新服务导入**

修改 `backend/app/agent/tools/customer.py` 第 5-6 行：

修改前：
```python
from services.customer_service import customer_service
from models.customer import CustomerCreate, CustomerUpdate, ShippingAddressCreate, ShippingAddressUpdate, CustomerType
```

修改后：
```python
from services.customer_service_mysql import customer_service
# 注意：MySQL 版本不再使用 Pydantic 模型，后续会重新对接
```

- [ ] **Step 2: 验证修改**

运行: `cd backend && python -c "from app.agent.tools.customer import *; print('OK')"`
预期: 输出 "OK"，无错误

---

### Task 3: 更新 Agent Tools - inventory.py（简化处理）

**Files:**
- Modify: `backend/app/agent/tools/inventory.py`

**注意：** 简化处理，只需确保服务启动不报错。后续会重新对接 agent 模块。

- [ ] **Step 1: 更新服务导入**

修改 `backend/app/agent/tools/inventory.py` 第 5 行：

修改前：
```python
from services.inventory_service import warehouse_service, stock_service
```

修改后：
```python
from services.inventory_service_mysql import warehouse_service, stock_service
```

- [ ] **Step 2: 验证修改**

运行: `cd backend && python -c "from app.agent.tools.inventory import *; print('OK')"`
预期: 输出 "OK"，无错误

---

### Task 4: 删除 MongoDB 服务文件

**Files:**
- Delete: `backend/services/customer_service.py`
- Delete: `backend/services/inventory_service.py`

**注意：** `backend/services/province_city_service.py` 保留，前端仍在使用省市接口。

- [ ] **Step 1: 删除 customer_service.py**

运行: `rm backend/services/customer_service.py`

- [ ] **Step 2: 删除 inventory_service.py**

运行: `rm backend/services/inventory_service.py`

- [ ] **Step 3: 验证删除**

运行: `ls backend/services/customer_service.py backend/services/inventory_service.py 2>&1`
预期: 输出 "No such file or directory"

---

### Task 5: 删除 MongoDB 模型文件

**Files:**
- Delete: `backend/models/customer.py`
- Delete: `backend/models/inventory.py`
- Delete: `backend/models/province_city.py`（已无实际使用，数据在 service 中硬编码）

- [ ] **Step 1: 删除 customer.py**

运行: `rm backend/models/customer.py`

- [ ] **Step 2: 删除 inventory.py**

运行: `rm backend/models/inventory.py`

- [ ] **Step 3: 删除 province_city.py**

运行: `rm backend/models/province_city.py`

- [ ] **Step 4: 验证删除**

运行: `ls backend/models/customer.py backend/models/inventory.py backend/models/province_city.py 2>&1`
预期: 输出 "No such file or directory"

---

### Task 6: 验证清理结果

**Files:**
- None (验证任务)

- [ ] **Step 1: 全局搜索确认无遗漏引用**

运行:
```bash
cd backend && grep -r "from models.customer" --include="*.py" .
cd backend && grep -r "from models.inventory" --include="*.py" .
cd backend && grep -r "from services.customer_service import" --include="*.py" .
cd backend && grep -r "from services.inventory_service import" --include="*.py" .
```
预期: 无输出（表示无遗漏引用）

- [ ] **Step 2: 启动后端服务验证**

运行: `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
预期: 服务正常启动，无导入错误

- [ ] **Step 3: 测试客户管理 API**

运行:
```bash
curl -X GET "http://localhost:8000/api/customers/" -H "Authorization: Bearer <token>"
```
预期: 返回客户列表，无错误

- [ ] **Step 4: 测试库存管理 API**

运行:
```bash
curl -X GET "http://localhost:8000/api/warehouse/" -H "Authorization: Bearer <token>"
curl -X GET "http://localhost:8000/api/stock/" -H "Authorization: Bearer <token>"
```
预期: 返回仓库和库存列表，无错误

- [ ] **Step 5: 测试省市 API（确认保留正常）**

运行:
```bash
curl -X GET "http://localhost:8000/api/province-city/"
```
预期: 返回省市数据，无错误

---

### Task 7: 提交清理变更

**Files:**
- None (提交任务)

- [ ] **Step 1: 查看变更状态**

运行: `git status`
预期: 显示删除的文件和修改的文件

- [ ] **Step 2: 添加变更到暂存区**

运行:
```bash
git add backend/models/__init__.py
git add backend/app/agent/tools/customer.py
git add backend/app/agent/tools/inventory.py
git add -u backend/models/customer.py
git add -u backend/models/inventory.py
git add -u backend/models/province_city.py
git add -u backend/services/customer_service.py
git add -u backend/services/inventory_service.py
```

- [ ] **Step 3: 提交变更**

运行:
```bash
git commit -m "$(cat <<'EOF'
chore: 清理 MongoDB 历史代码

- 删除 MongoDB 客户/库存模型文件
- 删除 MongoDB 客户/库存服务文件
- 删除无用的 province_city.py 模型
- 更新 Agent Tools 使用 MySQL 服务
- 更新 models/__init__.py 移除 MongoDB 模型导出

客户管理和库存管理模块已完全迁移到 MySQL
省市接口保留（前端仍在使用）

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: 验证提交**

运行: `git log -1 --oneline`
预期: 显示最新提交记录