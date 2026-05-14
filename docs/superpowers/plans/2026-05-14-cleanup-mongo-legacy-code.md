# MongoDB 历史代码清理实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理 auth 和 product 模块的 MongoDB 版历史代码，迁移依赖模块到 MySQL 版本

**Architecture:** 分阶段清理 - 先删除无依赖文件，再重构服务层，最后迁移依赖模块

**Tech Stack:** Python, FastAPI, Tortoise ORM (MySQL), Motor (MongoDB)

---

## 1. 删除无依赖的 MongoDB 模型文件

**Files:**
- Delete: `backend/models/auth.py`
- Delete: `backend/models/product.py`

- [ ] **Step 1: 确认 models/auth.py 无外部依赖**

运行: `grep -r "from models.auth import" backend/ --include="*.py"`
预期: 仅 `backend/services/auth_service.py` 和 `backend/app/middleware.py` 引用

- [ ] **Step 2: 确认 models/product.py 无外部依赖**

运行: `grep -r "from models.product import" backend/ --include="*.py"`
预期: 仅 `backend/services/product_service.py` 引用

- [ ] **Step 3: 删除 models/auth.py**

```bash
rm backend/models/auth.py
```

- [ ] **Step 4: 删除 models/product.py**

```bash
rm backend/models/product.py
```

- [ ] **Step 5: 提交删除**

```bash
git add backend/models/auth.py backend/models/product.py
git commit -m "chore: 删除 MongoDB 版 auth 和 product Pydantic 模型"
```

---

## 2. 删除 MongoDB 版商品服务

**Files:**
- Delete: `backend/services/product_service.py`

- [ ] **Step 1: 确认 product_service.py 的依赖方**

运行: `grep -r "from services.product_service import" backend/ --include="*.py"`
预期输出:
- `backend/services/__init__.py`
- `backend/services/sales_order_service.py`
- `backend/services/customer_service.py`
- `backend/services/inventory_service.py`
- `backend/app/agent/tools/product.py`

- [ ] **Step 2: 删除 product_service.py**

```bash
rm backend/services/product_service.py
```

- [ ] **Step 3: 提交删除**

```bash
git add backend/services/product_service.py
git commit -m "chore: 删除 MongoDB 版 product_service"
```

---

## 3. 重构 auth_service.py

**Files:**
- Modify: `backend/services/auth_service.py`

- [ ] **Step 1: 读取当前 auth_service.py 内容**

确认需要删除的类和实例位置

- [ ] **Step 2: 删除 AuthService 类（第 25-295 行）**

删除从 `class AuthService(BaseService):` 到 `class RoleService(BaseService):` 之前的所有代码

- [ ] **Step 3: 删除 RoleService 类（第 297-401 行）**

删除从 `class RoleService(BaseService):` 到 `class PermissionService(BaseService):` 之前的所有代码

- [ ] **Step 4: 删除 PermissionService 类（第 403-440 行）**

删除从 `class PermissionService(BaseService):` 到 `# ============ MySQL 版服务` 之前的所有代码

- [ ] **Step 5: 删除 MongoDB 版服务实例**

删除以下行:
```python
auth_service = AuthService()
role_service = RoleService()
permission_service = PermissionService()
```

- [ ] **Step 6: 验证文件结构**

确保文件仅包含:
- 导入语句
- `MySQLUserService` 类
- `MySQLRoleService` 类
- `MySQLPermissionService` 类
- `mysql_user_service` 实例
- `mysql_role_service` 实例
- `mysql_permission_service` 实例

- [ ] **Step 7: 提交重构**

```bash
git add backend/services/auth_service.py
git commit -m "refactor: 移除 auth_service.py 中的 MongoDB 版服务类"
```

---

## 4. 更新服务导出

**Files:**
- Modify: `backend/services/__init__.py`

- [ ] **Step 1: 更新导入语句**

将:
```python
from .auth_service import AuthService, RoleService, PermissionService, auth_service, role_service, permission_service
from .product_service import product_service, category_service, brand_service
```

改为:
```python
from .auth_service import mysql_user_service, mysql_role_service, mysql_permission_service
from .product_service_mysql import product_service, category_service, brand_service, product_spec_service
```

- [ ] **Step 2: 更新 __all__ 列表**

将:
```python
__all__ = [
    "BaseService",
    "SalesOrderService",
    "sales_order_service",
    "PurchaseOrderService",
    "purchase_order_service",
    "CustomerService",
    "customer_service",
    "customer_discount_service",
    "AuthService",
    "RoleService",
    "PermissionService",
    "auth_service",
    "role_service",
    "permission_service",
    "warehouse_service",
    "stock_service",
    "product_service",
    "category_service",
    "brand_service",
    "accounts_receivable_service",
    "ws_manager",
    "llm_service",
    "llm_config_service",
    "knowledge_base_service",
    "mcp_service",
    "skill_service",
    "agent_service",
]
```

改为:
```python
__all__ = [
    "BaseService",
    "SalesOrderService",
    "sales_order_service",
    "PurchaseOrderService",
    "purchase_order_service",
    "CustomerService",
    "customer_service",
    "customer_discount_service",
    "mysql_user_service",
    "mysql_role_service",
    "mysql_permission_service",
    "warehouse_service",
    "stock_service",
    "product_service",
    "category_service",
    "brand_service",
    "product_spec_service",
    "accounts_receivable_service",
    "ws_manager",
    "llm_service",
    "llm_config_service",
    "knowledge_base_service",
    "mcp_service",
    "skill_service",
    "agent_service",
]
```

- [ ] **Step 3: 提交更新**

```bash
git add backend/services/__init__.py
git commit -m "refactor: 更新服务导出，移除 MongoDB 版服务实例"
```

---

## 5. 更新中间件

**Files:**
- Modify: `backend/app/middleware.py`

- [ ] **Step 1: 更新导入语句**

将:
```python
from models.auth import TokenPayload
from services.auth_service import auth_service
```

改为:
```python
from models_mysql.auth import User, Role, Permission
from services.auth_service import mysql_user_service
```

- [ ] **Step 2: 添加 TokenPayload 模型**

在文件中添加 TokenPayload 类（或从 models_mysql 导入）:
```python
from pydantic import BaseModel
from typing import List

class TokenPayload(BaseModel):
    sub: str
    username: str
    roles: List[str] = []
    permissions: List[str] = []
    exp: int
```

- [ ] **Step 3: 更新用户查询调用**

将第 78 行:
```python
user = await auth_service.get_user_by_id(token_data.sub)
```

改为:
```python
user = await mysql_user_service.get_by_id(int(token_data.sub))
```

- [ ] **Step 4: 提交更新**

```bash
git add backend/app/middleware.py
git commit -m "refactor: 中间件迁移到 MySQL 版用户服务"
```

---

## 6. 更新 WebSocket 路由

**Files:**
- Modify: `backend/app/routers/ws.py`

- [ ] **Step 1: 更新导入语句**

将:
```python
from models.auth import TokenPayload
from services.auth_service import auth_service
```

改为:
```python
from models_mysql.auth import User, Role, Permission
from services.auth_service import mysql_user_service
```

- [ ] **Step 2: 添加 TokenPayload 模型**

在文件中添加:
```python
from pydantic import BaseModel
from typing import List

class TokenPayload(BaseModel):
    sub: str
    username: str
    roles: List[str] = []
    permissions: List[str] = []
    exp: int
```

- [ ] **Step 3: 更新用户查询调用**

将第 43 行:
```python
user = await auth_service.get_user_by_id(token_data.sub)
```

改为:
```python
user = await mysql_user_service.get_by_id(int(token_data.sub))
```

- [ ] **Step 4: 提交更新**

```bash
git add backend/app/routers/ws.py
git commit -m "refactor: WebSocket 路由迁移到 MySQL 版用户服务"
```

---

## 7. 更新 sales_order_service.py

**Files:**
- Modify: `backend/services/sales_order_service.py`

- [ ] **Step 1: 更新导入语句**

将第 10 行:
```python
from services.product_service import product_service, product_spec_service, brand_service
```

改为:
```python
from services.product_service_mysql import product_service, product_spec_service, brand_service
```

- [ ] **Step 2: 更新商品查询方法调用**

第 124-125 行的方法调用需要适配 MySQL 版 API:
- `product_service.get_product_by_codes` → 需要检查 MySQL 版是否有此方法
- `product_spec_service.get_spec_by_codes` → 需要检查 MySQL 版是否有此方法

MySQL 版 `product_service_mysql.py` 缺少 `get_product_by_codes` 和 `get_spec_by_codes` 方法，需要添加:

在 `ProductService` 类中添加:
```python
async def get_product_by_codes(self, codes: List[str]) -> List[Dict[str, Any]]:
    """根据编号列表获取商品"""
    products = await Product.filter(product_code__in=codes).all()
    return [await p.to_dict() for p in products]
```

在 `ProductSpecService` 类中添加:
```python
async def get_spec_by_codes(self, codes: List[str]) -> List[Dict[str, Any]]:
    """根据编号列表获取规格"""
    specs = await ProductSpec.filter(spec_code__in=codes).all()
    return [await s.to_dict() for s in specs]
```

- [ ] **Step 3: 提交更新**

```bash
git add backend/services/sales_order_service.py backend/services/product_service_mysql.py
git commit -m "refactor: sales_order_service 迁移到 MySQL 版商品服务"
```

---

## 8. 更新 customer_service.py

**Files:**
- Modify: `backend/services/customer_service.py`

- [ ] **Step 1: 更新用户服务导入**

将第 158-161 行:
```python
from services.auth_service import AuthService

auth_service = AuthService()
new_user = await auth_service.get_user_by_id(new_sales_user_id)
```

改为:
```python
from services.auth_service import mysql_user_service

new_user = await mysql_user_service.get_by_id(int(new_sales_user_id))
```

- [ ] **Step 2: 更新品牌服务导入**

将第 401、411 行:
```python
from services.product_service import brand_service
```

改为:
```python
from services.product_service_mysql import brand_service
```

- [ ] **Step 3: 更新品牌查询方法**

第 403 行 `brand_service.get_by_id` 需要改为 `brand_service.get_brand_by_id`:
```python
if brand := await brand_service.get_brand_by_id(int(brand_id)):
```

第 413 行 `brand_service.get_by_ids` 需要检查是否存在，MySQL 版缺少此方法，需要添加:

在 `BrandService` 类中添加:
```python
async def get_brand_by_ids(self, brand_ids: List[int]) -> List[Dict[str, Any]]:
    """根据ID列表获取品牌"""
    brands = await Brand.filter(id__in=brand_ids).all()
    return [b.to_dict() for b in brands]
```

- [ ] **Step 4: 提交更新**

```bash
git add backend/services/customer_service.py backend/services/product_service_mysql.py
git commit -m "refactor: customer_service 迁移到 MySQL 版服务"
```

---

## 9. 更新 inventory_service.py

**Files:**
- Modify: `backend/services/inventory_service.py`

- [ ] **Step 1: 更新导入语句**

将第 129、136、143、208、219 行:
```python
from .product_service import product_service, product_spec_service
```

改为:
```python
from .product_service_mysql import product_service, product_spec_service
```

- [ ] **Step 2: 更新方法调用**

MySQL 版方法签名略有不同，需要适配:
- `product_service.get_product_by_id(product_id, is_formatted=False)` → 签名相同
- `product_spec_service.get_spec_by_id(spec_id, is_formatted=False)` → 签名相同
- `product_service.get_product_by_ids(product_ids, is_formatted=False)` → 签名相同
- `product_spec_service.get_spec_by_ids(spec_ids, is_formatted=False)` → 签名相同

- [ ] **Step 3: 提交更新**

```bash
git add backend/services/inventory_service.py
git commit -m "refactor: inventory_service 迁移到 MySQL 版商品服务"
```

---

## 10. 删除 Agent 工具和脚本文件

**Files:**
- Delete: `backend/app/agent/tools/product.py`
- Delete: `backend/scripts/init_db.py`
- Delete: `backend/scripts/shell.py`

- [ ] **Step 1: 删除 Agent 工具**

```bash
rm backend/app/agent/tools/product.py
```

- [ ] **Step 2: 删除 MongoDB 版初始化脚本**

已有 MySQL 版初始化脚本 `init_db_mysql.py` 和 `init_db_sync.py`，删除 MongoDB 版:
```bash
rm backend/scripts/init_db.py
```

- [ ] **Step 3: 删除调试脚本**

```bash
rm backend/scripts/shell.py
```

- [ ] **Step 4: 提交删除**

```bash
git add backend/app/agent/tools/product.py backend/scripts/init_db.py backend/scripts/shell.py
git commit -m "chore: 删除不再使用的 Agent 工具和 MongoDB 版脚本"
```

---

## 11. 验证

- [ ] **Step 1: 检查导入错误**

```bash
cd backend && python -c "from services import *"
```

预期: 无错误输出

- [ ] **Step 2: 检查语法错误**

```bash
cd backend && python -m py_compile app/middleware.py app/routers/ws.py services/sales_order_service.py services/customer_service.py services/inventory_service.py
```

预期: 无错误输出

- [ ] **Step 3: 最终提交**

```bash
git add -A
git commit -m "refactor: 完成 MongoDB 历史代码清理

- 删除 models/auth.py 和 models/product.py
- 删除 services/product_service.py
- 删除 app/agent/tools/product.py、scripts/init_db.py、scripts/shell.py
- 重构 auth_service.py，移除 MongoDB 版服务类
- 更新 middleware.py 和 ws.py 使用 MySQL 版用户服务
- 迁移 sales_order_service.py、customer_service.py、inventory_service.py 到 MySQL 版商品服务"
```
