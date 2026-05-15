# 盘库功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现库存盘点功能，支持单个盘库、批量盘库（Excel上传）、盘库记录查询和模板下载。

**Architecture:** 后端使用 Tortoise ORM + MySQL，新增 StockCheckBatch 和 StockCheckRecord 模型；前端在 InventoryWorkspace.vue 中新增盘库相关 UI 组件。

**Tech Stack:** Python/FastAPI, Tortoise ORM, Vue 3, TypeScript, vxe-table, openpyxl

---

## 1. 后端数据模型

**Files:**
- Create: `backend/models_mysql/stock_check.py`
- Modify: `backend/models_mysql/__init__.py`

- [ ] **Step 1: 创建盘库数据模型文件**

创建 `backend/models_mysql/stock_check.py`：

```python
"""
盘库管理 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class StockCheckBatch(Model):
    """盘库批次模型"""
    id = fields.IntField(pk=True, description="批次ID")
    batch_code = fields.CharField(max_length=50, unique=True, description="批次编号")
    warehouse_id = fields.IntField(description="仓库ID")
    warehouse_name = fields.CharField(max_length=100, description="仓库名称")
    check_type = fields.CharField(max_length=20, description="盘库类型: single/batch")
    total_count = fields.IntField(default=0, description="总记录数")
    success_count = fields.IntField(default=0, description="成功数")
    fail_count = fields.IntField(default=0, description="失败数")
    user_id = fields.IntField(description="操作用户ID")
    user_name = fields.CharField(max_length=100, description="操作用户名")
    remarks = fields.CharField(max_length=500, null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "stock_check_batches"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.batch_code}: {self.warehouse_name}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "batch_code": self.batch_code,
            "warehouse_id": self.warehouse_id,
            "warehouse_name": self.warehouse_name,
            "check_type": self.check_type,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StockCheckRecord(Model):
    """盘库记录模型"""
    id = fields.IntField(pk=True, description="记录ID")
    batch_id = fields.IntField(description="批次ID")
    stock_id = fields.IntField(null=True, description="库存ID（新建时为空）")
    warehouse_id = fields.IntField(description="仓库ID")
    product_id = fields.IntField(description="商品ID")
    product_code = fields.CharField(max_length=50, description="商品编号")
    product_name = fields.CharField(max_length=200, description="商品名称")
    spec_id = fields.IntField(description="规格ID")
    spec_code = fields.CharField(max_length=50, description="规格编号")
    before_quantity = fields.FloatField(description="盘点前数量")
    check_quantity = fields.FloatField(description="盘点数量")
    difference = fields.FloatField(description="差异")
    is_new_stock = fields.BooleanField(default=False, description="是否新建库存")
    user_id = fields.IntField(description="操作用户ID")
    user_name = fields.CharField(max_length=100, description="操作用户名")
    remarks = fields.CharField(max_length=500, null=True, description="备注")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "stock_check_records"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Check {self.id}: {self.spec_code} - {self.difference}"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "stock_id": self.stock_id,
            "warehouse_id": self.warehouse_id,
            "product_id": self.product_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "spec_id": self.spec_id,
            "spec_code": self.spec_code,
            "before_quantity": self.before_quantity,
            "check_quantity": self.check_quantity,
            "difference": self.difference,
            "is_new_stock": self.is_new_stock,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
```

- [ ] **Step 2: 在 __init__.py 中注册新模型**

修改 `backend/models_mysql/__init__.py`，添加导入：

```python
from .stock_check import StockCheckBatch, StockCheckRecord
```

并在 `__all__` 列表中添加：
```python
"StockCheckBatch",
"StockCheckRecord",
```

- [ ] **Step 3: 提交数据模型**

```bash
git add backend/models_mysql/stock_check.py backend/models_mysql/__init__.py
git commit -m "feat(stock-check): add StockCheckBatch and StockCheckRecord models"
```

---

## 2. 后端服务层

**Files:**
- Create: `backend/services/stock_check_service.py`

- [ ] **Step 4: 创建盘库服务文件**

创建 `backend/services/stock_check_service.py`：

```python
"""
盘库管理服务层
"""
import io
import random
import string
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

from tortoise.expressions import Q

from models_mysql.stock_check import StockCheckBatch, StockCheckRecord
from models_mysql.warehouse import Stock
from models_mysql.product import ProductSpec
from services.inventory_service_mysql import stock_service, warehouse_service
from services.product_service_mysql import product_spec_service

logger = logging.getLogger(__name__)


def _generate_batch_code(prefix: str = "SC") -> str:
    """生成批次编号"""
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}{date_str}{random_str}"


class StockCheckService:
    """盘库服务"""

    async def create_single_check(
        self,
        stock_id: int,
        check_quantity: float,
        user_id: int,
        user_name: str,
        remarks: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建单个盘库"""
        # 获取库存记录
        stock = await Stock.get_or_none(id=stock_id)
        if not stock:
            raise ValueError("库存记录不存在")

        # 获取仓库信息
        warehouse = await warehouse_service.get_warehouse_by_id(stock.warehouse_id)
        warehouse_name = warehouse.get("name", "") if warehouse else ""

        # 计算差异
        before_quantity = stock.quantity
        difference = check_quantity - before_quantity

        # 创建批次
        batch = await StockCheckBatch.create(
            batch_code=_generate_batch_code(),
            warehouse_id=stock.warehouse_id,
            warehouse_name=warehouse_name,
            check_type="single",
            total_count=1,
            success_count=1,
            fail_count=0,
            user_id=user_id,
            user_name=user_name,
            remarks=remarks,
        )

        # 更新库存数量
        stock.quantity = check_quantity
        stock.status = stock_service._calculate_status(
            stock.quantity, stock.min_stock, stock.max_stock
        )
        await stock.save()

        # 创建盘库记录
        record = await StockCheckRecord.create(
            batch_id=batch.id,
            stock_id=stock.id,
            warehouse_id=stock.warehouse_id,
            product_id=stock.product_id,
            product_code=stock.product_code,
            product_name=stock.product_name,
            spec_id=stock.spec_id,
            spec_code=stock.spec_code,
            before_quantity=before_quantity,
            check_quantity=check_quantity,
            difference=difference,
            is_new_stock=False,
            user_id=user_id,
            user_name=user_name,
            remarks=remarks,
        )

        return {
            "batch_id": batch.id,
            "record_id": record.id,
            "before_quantity": before_quantity,
            "check_quantity": check_quantity,
            "difference": difference,
        }

    async def create_batch_check(
        self,
        warehouse_id: int,
        file_content: bytes,
        user_id: int,
        user_name: str,
        remarks: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建批量盘库（从Excel）"""
        from openpyxl import load_workbook

        # 获取仓库信息
        warehouse = await warehouse_service.get_warehouse_by_id(warehouse_id)
        if not warehouse:
            raise ValueError("仓库不存在")
        warehouse_name = warehouse.get("name", "")

        # 解析Excel
        try:
            wb = load_workbook(io.BytesIO(file_content))
            ws = wb.active
            rows = list(ws.iter_rows(min_row=2, values_only=True))  # 跳过表头
        except Exception as e:
            raise ValueError(f"Excel文件解析失败: {str(e)}")

        # 创建批次
        batch = await StockCheckBatch.create(
            batch_code=_generate_batch_code(),
            warehouse_id=warehouse_id,
            warehouse_name=warehouse_name,
            check_type="batch",
            total_count=len(rows),
            success_count=0,
            fail_count=0,
            user_id=user_id,
            user_name=user_name,
            remarks=remarks,
        )

        success_count = 0
        fail_count = 0
        failed_items = []

        for idx, row in enumerate(rows, start=2):  # 从第2行开始
            try:
                spec_code = str(row[0]).strip() if row[0] else None
                check_quantity = float(row[1]) if row[1] is not None else None
                row_remarks = str(row[2]).strip() if len(row) > 2 and row[2] else None

                if not spec_code:
                    raise ValueError("规格编码不能为空")
                if check_quantity is None or check_quantity < 0:
                    raise ValueError("盘点数量必须为非负数")

                # 查找规格
                spec = await ProductSpec.filter(spec_code=spec_code).first()
                if not spec:
                    raise ValueError(f"规格编码 {spec_code} 不存在")

                # 查找库存
                stock = await Stock.filter(
                    warehouse_id=warehouse_id,
                    spec_id=spec.id
                ).first()

                # 获取商品信息
                product = await spec.product

                if stock:
                    # 更新现有库存
                    before_quantity = stock.quantity
                    difference = check_quantity - before_quantity
                    stock.quantity = check_quantity
                    stock.status = stock_service._calculate_status(
                        stock.quantity, stock.min_stock, stock.max_stock
                    )
                    await stock.save()
                    is_new_stock = False
                    stock_id = stock.id
                else:
                    # 创建新库存
                    before_quantity = 0
                    difference = check_quantity
                    new_stock = await Stock.create(
                        warehouse_id=warehouse_id,
                        product_id=spec.product_id,
                        product_code=product.product_code if product else "",
                        product_name=product.name if product else "",
                        spec_id=spec.id,
                        spec_code=spec.spec_code,
                        quantity=check_quantity,
                        min_stock=0,
                        max_stock=0,
                        status=stock_service._calculate_status(check_quantity, 0, 0),
                    )
                    is_new_stock = True
                    stock_id = new_stock.id

                # 创建盘库记录
                await StockCheckRecord.create(
                    batch_id=batch.id,
                    stock_id=stock_id,
                    warehouse_id=warehouse_id,
                    product_id=spec.product_id,
                    product_code=product.product_code if product else "",
                    product_name=product.name if product else "",
                    spec_id=spec.id,
                    spec_code=spec.spec_code,
                    before_quantity=before_quantity,
                    check_quantity=check_quantity,
                    difference=difference,
                    is_new_stock=is_new_stock,
                    user_id=user_id,
                    user_name=user_name,
                    remarks=row_remarks or remarks,
                )

                success_count += 1

            except Exception as e:
                fail_count += 1
                failed_items.append({
                    "row": idx,
                    "reason": str(e)
                })

        # 更新批次统计
        batch.success_count = success_count
        batch.fail_count = fail_count
        await batch.save()

        return {
            "batch_id": batch.id,
            "batch_code": batch.batch_code,
            "total_count": batch.total_count,
            "success_count": success_count,
            "fail_count": fail_count,
            "failed_items": failed_items,
        }

    async def generate_template(self) -> bytes:
        """生成盘库模板Excel"""
        wb = Workbook()
        ws = wb.active
        ws.title = "盘库模板"

        # 设置表头
        headers = ["规格编码", "盘点数量", "备注"]
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        header_alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
            cell.border = thin_border

        # 设置列宽
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 30

        # 添加示例数据
        example_data = [
            ["SP001-A", 100, "示例备注"],
            ["SP002-B", 50, ""],
        ]
        for row_idx, row_data in enumerate(example_data, start=2):
            for col_idx, value in enumerate(row_data, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="center", vertical="center")

        # 输出到字节流
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    async def get_records_by_stock_id(
        self, stock_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """根据库存ID获取盘库记录"""
        query = StockCheckRecord.filter(stock_id=stock_id)
        total = await query.count()
        records = await query.offset((page - 1) * page_size).limit(page_size)
        return [r.to_dict() for r in records], total

    async def get_records_by_batch_id(
        self, batch_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """根据批次ID获取盘库记录"""
        query = StockCheckRecord.filter(batch_id=batch_id)
        total = await query.count()
        records = await query.offset((page - 1) * page_size).limit(page_size)
        return [r.to_dict() for r in records], total

    async def list_records(
        self,
        page: int = 1,
        page_size: int = 20,
        stock_id: Optional[int] = None,
        batch_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取盘库记录列表"""
        query = StockCheckRecord.all()

        if stock_id:
            query = query.filter(stock_id=stock_id)
        if batch_id:
            query = query.filter(batch_id=batch_id)
        if warehouse_id:
            query = query.filter(warehouse_id=warehouse_id)

        total = await query.count()
        records = await query.offset((page - 1) * page_size).limit(page_size)
        return [r.to_dict() for r in records], total

    async def list_batches(
        self,
        page: int = 1,
        page_size: int = 20,
        warehouse_id: Optional[int] = None,
        check_type: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取盘库批次列表"""
        query = StockCheckBatch.all()

        if warehouse_id:
            query = query.filter(warehouse_id=warehouse_id)
        if check_type:
            query = query.filter(check_type=check_type)

        total = await query.count()
        batches = await query.offset((page - 1) * page_size).limit(page_size)
        return [b.to_dict() for b in batches], total

    async def get_batch_detail(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """获取批次详情"""
        batch = await StockCheckBatch.get_or_none(id=batch_id)
        if not batch:
            return None

        result = batch.to_dict()
        # 获取关联的盘库记录
        records = await StockCheckRecord.filter(batch_id=batch_id).all()
        result["records"] = [r.to_dict() for r in records]
        return result


# 创建服务实例
stock_check_service = StockCheckService()
```

- [ ] **Step 5: 提交服务层代码**

```bash
git add backend/services/stock_check_service.py
git commit -m "feat(stock-check): add StockCheckService with single/batch check support"
```

---

## 3. 后端 API 路由

**Files:**
- Create: `backend/app/routers/stock_check.py`
- Modify: `backend/app/routers/__init__.py`

- [ ] **Step 6: 创建盘库 API 路由文件**

创建 `backend/app/routers/stock_check.py`：

```python
"""
盘库管理 - API路由
"""
from fastapi import APIRouter, Query, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import io

from services.stock_check_service import stock_check_service
from .auth import require_permission
from app.decorators import wrap_response

stock_check_router = APIRouter(prefix="/stock-checks", tags=["盘库管理"])


def to_int_id(id_str: str) -> int:
    """将字符串 ID 转换为整数 ID"""
    try:
        return int(id_str)
    except (ValueError, TypeError):
        raise ValueError("无效的ID格式")


@stock_check_router.post("/single", response_model=dict)
@wrap_response
async def create_single_check(
    data: Dict[str, Any],
    _: dict = Depends(require_permission("stock.edit"))
):
    """单个盘库"""
    stock_id = data.get("stock_id")
    check_quantity = data.get("check_quantity")
    remarks = data.get("remarks")

    if not stock_id:
        raise ValueError("库存ID不能为空")
    if check_quantity is None:
        raise ValueError("盘点数量不能为空")

    # 获取当前用户信息
    user_id = _.get("id", 0)
    user_name = _.get("username", _.get("name", "未知用户"))

    result = await stock_check_service.create_single_check(
        stock_id=to_int_id(stock_id),
        check_quantity=float(check_quantity),
        user_id=user_id,
        user_name=user_name,
        remarks=remarks,
    )
    return result


@stock_check_router.post("/batch", response_model=dict)
@wrap_response
async def create_batch_check(
    warehouse_id: str = Form(...),
    file: UploadFile = File(...),
    remarks: Optional[str] = Form(None),
    _: dict = Depends(require_permission("stock.edit"))
):
    """批量盘库"""
    if not warehouse_id:
        raise ValueError("请选择仓库")
    if not file:
        raise ValueError("请上传盘库文件")

    # 读取文件内容
    file_content = await file.read()

    # 获取当前用户信息
    user_id = _.get("id", 0)
    user_name = _.get("username", _.get("name", "未知用户"))

    result = await stock_check_service.create_batch_check(
        warehouse_id=to_int_id(warehouse_id),
        file_content=file_content,
        user_id=user_id,
        user_name=user_name,
        remarks=remarks,
    )
    return result


@stock_check_router.get("/template")
async def download_template(
    _: dict = Depends(require_permission("stock.view"))
):
    """下载盘库模板"""
    file_content = await stock_check_service.generate_template()
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=stock_check_template.xlsx"
        }
    )


@stock_check_router.get("/records", response_model=dict)
@wrap_response
async def list_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    stock_id: Optional[str] = Query(None, description="库存ID"),
    batch_id: Optional[str] = Query(None, description="批次ID"),
    warehouse_id: Optional[str] = Query(None, description="仓库ID"),
    _: dict = Depends(require_permission("stock.view"))
):
    """获取盘库记录列表"""
    records, total = await stock_check_service.list_records(
        page=page,
        page_size=page_size,
        stock_id=to_int_id(stock_id) if stock_id else None,
        batch_id=to_int_id(batch_id) if batch_id else None,
        warehouse_id=to_int_id(warehouse_id) if warehouse_id else None,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": records
    }


@stock_check_router.get("/batches", response_model=dict)
@wrap_response
async def list_batches(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    warehouse_id: Optional[str] = Query(None, description="仓库ID"),
    check_type: Optional[str] = Query(None, description="盘库类型"),
    _: dict = Depends(require_permission("stock.view"))
):
    """获取盘库批次列表"""
    batches, total = await stock_check_service.list_batches(
        page=page,
        page_size=page_size,
        warehouse_id=to_int_id(warehouse_id) if warehouse_id else None,
        check_type=check_type,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": batches
    }


@stock_check_router.get("/batches/{batch_id}", response_model=dict)
@wrap_response
async def get_batch_detail(
    batch_id: str,
    _: dict = Depends(require_permission("stock.view"))
):
    """获取批次详情"""
    batch = await stock_check_service.get_batch_detail(to_int_id(batch_id))
    if not batch:
        raise ValueError("批次不存在")
    return batch
```

- [ ] **Step 7: 在路由 __init__.py 中注册新路由**

修改 `backend/app/routers/__init__.py`，添加：

```python
from .stock_check import stock_check_router
```

并在 `api_router.include_router` 部分添加：

```python
api_router.include_router(stock_check_router, tags=["盘库管理"])
```

- [ ] **Step 8: 提交 API 路由代码**

```bash
git add backend/app/routers/stock_check.py backend/app/routers/__init__.py
git commit -m "feat(stock-check): add stock check API routes"
```

---

## 4. 前端 API 服务

**Files:**
- Modify: `web/src/services/api.ts`

- [ ] **Step 9: 在 api.ts 中添加盘库 API**

在 `web/src/services/api.ts` 文件末尾添加：

```typescript
export const stockCheckApi = {
  // 单个盘库
  createSingle: (data: { stock_id: string; check_quantity: number; remarks?: string }) => {
    return apiService.post<any>('/stock-checks/single', data)
  },

  // 批量盘库
  createBatch: async (warehouseId: string, file: File, remarks?: string) => {
    const formData = new FormData()
    formData.append('warehouse_id', warehouseId)
    formData.append('file', file)
    if (remarks) {
      formData.append('remarks', remarks)
    }

    const url = `${apiService['baseUrl']}/stock-checks/batch`
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '批量盘库失败' }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  },

  // 下载模板
  downloadTemplate: async () => {
    const url = `${apiService['baseUrl']}/stock-checks/template`
    const headers: Record<string, string> = {}
    const token = localStorage.getItem('token')
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(url, { headers })
    if (!response.ok) {
      throw new Error('下载模板失败')
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = 'stock_check_template.xlsx'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(downloadUrl)
  },

  // 获取盘库记录列表
  listRecords: (params: { page?: number; page_size?: number; stock_id?: string; batch_id?: string; warehouse_id?: string }) => {
    return apiService.get<any>('/stock-checks/records', params)
  },

  // 获取盘库批次列表
  listBatches: (params: { page?: number; page_size?: number; warehouse_id?: string; check_type?: string }) => {
    return apiService.get<any>('/stock-checks/batches', params)
  },

  // 获取批次详情
  getBatchDetail: (batchId: string) => {
    return apiService.get<any>(`/stock-checks/batches/${batchId}`)
  }
}
```

- [ ] **Step 10: 提交前端 API 代码**

```bash
git add web/src/services/api.ts
git commit -m "feat(stock-check): add stockCheckApi to frontend"
```

---

## 5. 前端 UI 组件

**Files:**
- Modify: `web/src/components/workspace/InventoryWorkspace.vue`

- [ ] **Step 11: 在 InventoryWorkspace.vue 中添加盘库相关变量和接口**

在 `<script setup>` 部分的接口定义后添加：

```typescript
interface StockCheckRecord {
  id: string
  batch_id: string
  stock_id: string
  warehouse_id: string
  product_id: string
  product_code: string
  product_name: string
  spec_id: string
  spec_code: string
  before_quantity: number
  check_quantity: number
  difference: number
  is_new_stock: boolean
  user_id: string
  user_name: string
  remarks?: string
  created_at: string
}
```

在 `const` 变量声明部分添加：

```typescript
const showBatchCheckModal = ref(false)
const showCheckResultModal = ref(false)
const showSingleCheckModal = ref(false)
const batchCheckForm = ref({
  warehouse_id: '',
  remarks: ''
})
const batchCheckFile = ref<File | null>(null)
const batchCheckLoading = ref(false)
const batchCheckResult = ref<{
  batch_code: string
  total_count: number
  success_count: number
  fail_count: number
  failed_items: Array<{ row: number; reason: string }>
} | null>(null)
const singleCheckStock = ref<Stock | null>(null)
const singleCheckForm = ref({
  check_quantity: 0,
  remarks: ''
})
const singleCheckLoading = ref(false)
const checkRecords = ref<StockCheckRecord[]>([])
const detailActiveTab = ref<'inbound' | 'outbound' | 'check'>('inbound')
```

- [ ] **Step 12: 添加盘库相关方法**

在 `onMounted` 之前添加以下方法：

```typescript
const openBatchCheckModal = () => {
  batchCheckForm.value = {
    warehouse_id: filterWarehouse.value || '',
    remarks: ''
  }
  batchCheckFile.value = null
  showBatchCheckModal.value = true
}

const handleBatchCheckFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    batchCheckFile.value = target.files[0]
  }
}

const handleDownloadTemplate = async () => {
  try {
    const { stockCheckApi } = await import('../../services/api')
    await stockCheckApi.downloadTemplate()
    window.showToast('模板下载成功', 'success')
  } catch (error: any) {
    window.showToast(error.message || '下载模板失败', 'error')
  }
}

const handleBatchCheck = async () => {
  if (!batchCheckForm.value.warehouse_id) {
    window.showToast('请选择仓库', 'warning')
    return
  }
  if (!batchCheckFile.value) {
    window.showToast('请上传盘库文件', 'warning')
    return
  }

  batchCheckLoading.value = true
  try {
    const { stockCheckApi } = await import('../../services/api')
    const result = await stockCheckApi.createBatch(
      batchCheckForm.value.warehouse_id,
      batchCheckFile.value,
      batchCheckForm.value.remarks
    )
    batchCheckResult.value = result.result || result
    showBatchCheckModal.value = false
    showCheckResultModal.value = true
    loadStocks()
  } catch (error: any) {
    window.showToast(error.message || '批量盘库失败', 'error')
  } finally {
    batchCheckLoading.value = false
  }
}

const openSingleCheckModal = (row: any) => {
  const stock = stocks.value.find(s => s.id === row.stockId)
  if (!stock) return
  singleCheckStock.value = stock
  singleCheckForm.value = {
    check_quantity: stock.quantity,
    remarks: ''
  }
  showSingleCheckModal.value = true
}

const singleCheckDifference = computed(() => {
  if (!singleCheckStock.value) return 0
  return singleCheckForm.value.check_quantity - singleCheckStock.value.quantity
})

const handleSingleCheck = async () => {
  if (!singleCheckStock.value) return
  if (singleCheckForm.value.check_quantity < 0) {
    window.showToast('盘点数量不能为负数', 'warning')
    return
  }

  singleCheckLoading.value = true
  try {
    const { stockCheckApi } = await import('../../services/api')
    await stockCheckApi.createSingle({
      stock_id: singleCheckStock.value.id,
      check_quantity: singleCheckForm.value.check_quantity,
      remarks: singleCheckForm.value.remarks
    })
    window.showToast('盘库成功', 'success')
    showSingleCheckModal.value = false
    await updateStockInList(singleCheckStock.value.id)
    loadStocks()
  } catch (error: any) {
    window.showToast(error.message || '盘库失败', 'error')
  } finally {
    singleCheckLoading.value = false
  }
}

const loadCheckRecords = async (stockId: string) => {
  try {
    const { stockCheckApi } = await import('../../services/api')
    const res = await stockCheckApi.listRecords({ stock_id: stockId, page_size: 50 })
    checkRecords.value = res.items || []
  } catch (error) {
    console.error('加载盘库记录失败:', error)
    checkRecords.value = []
  }
}
```

- [ ] **Step 13: 修改 loadStockDetail 方法**

修改 `loadStockDetail` 方法，添加盘库记录加载：

```typescript
const loadStockDetail = async (stockId: string) => {
  detailLoading.value = true
  try {
    const [stockRes, inboundRes, outboundRes] = await Promise.all([
      stockApi.getById(stockId),
      inboundBatchApi.list({ stock_id: stockId, page_size: 50 }),
      outboundBatchApi.list({ stock_id: stockId, page_size: 50 })
    ])
    stockDetail.value = {
      ...stockRes,
      inbound_batches: inboundRes.items || [],
      outbound_batches: outboundRes.items || []
    }
    // 加载盘库记录
    await loadCheckRecords(stockId)
    detailActiveTab.value = 'inbound'
  } catch (error) {
    console.error('加载库存详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}
```

- [ ] **Step 14: 修改模板部分 - 添加批量盘库按钮**

在 `header-actions` div 中，在"新增入库"按钮后添加：

```html
<button class="primary-btn" @click="openBatchCheckModal">批量盘库</button>
```

- [ ] **Step 15: 修改模板部分 - 在操作列添加盘库按钮**

在表格操作列的 `btn-link` 按钮组中，在"详情"按钮前添加：

```html
<button class="btn-link" @click="openSingleCheckModal(row)">盘库</button>
```

- [ ] **Step 16: 添加批量盘库弹窗**

在 `showDetailModal` 弹窗之后添加批量盘库弹窗：

```html
<!-- 批量盘库弹窗 -->
<div class="modal-overlay" v-if="showBatchCheckModal">
  <div class="modal">
    <div class="modal-header">
      <h3>批量盘库</h3>
      <button class="modal-close" @click="showBatchCheckModal = false">&times;</button>
    </div>
    <div class="modal-body">
      <div class="form-group">
        <label>仓库 *</label>
        <select v-model="batchCheckForm.warehouse_id">
          <option value="">请选择仓库</option>
          <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
        </select>
      </div>
      <div class="form-group">
        <label>盘库文件 *</label>
        <div class="file-upload-area">
          <input type="file" accept=".xlsx,.xls" @change="handleBatchCheckFileChange" />
          <button class="link-btn" @click="handleDownloadTemplate" type="button">下载模板</button>
        </div>
      </div>
      <div class="form-group">
        <label>备注</label>
        <input type="text" v-model="batchCheckForm.remarks" placeholder="可选填写备注信息" />
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn-secondary" @click="showBatchCheckModal = false">取消</button>
      <button class="btn-primary" @click="handleBatchCheck" :disabled="batchCheckLoading">
        {{ batchCheckLoading ? '处理中...' : '开始盘库' }}
      </button>
    </div>
  </div>
</div>
```

- [ ] **Step 17: 添加盘库结果弹窗**

在批量盘库弹窗之后添加：

```html
<!-- 盘库结果弹窗 -->
<div class="modal-overlay" v-if="showCheckResultModal">
  <div class="modal">
    <div class="modal-header">
      <h3>盘库结果</h3>
      <button class="modal-close" @click="showCheckResultModal = false">&times;</button>
    </div>
    <div class="modal-body" v-if="batchCheckResult">
      <div class="result-summary">
        <div class="result-item">
          <span class="result-label">批次号:</span>
          <span class="result-value">{{ batchCheckResult.batch_code }}</span>
        </div>
        <div class="result-item">
          <span class="result-label">处理成功:</span>
          <span class="result-value success">{{ batchCheckResult.success_count }} 条</span>
        </div>
        <div class="result-item">
          <span class="result-label">处理失败:</span>
          <span class="result-value" :class="{ danger: batchCheckResult.fail_count > 0 }">
            {{ batchCheckResult.fail_count }} 条
          </span>
        </div>
      </div>
      <div class="failed-items" v-if="batchCheckResult.failed_items && batchCheckResult.failed_items.length > 0">
        <h4>失败详情:</h4>
        <div class="failed-list">
          <div class="failed-item" v-for="item in batchCheckResult.failed_items" :key="item.row">
            <span class="failed-row">第 {{ item.row }} 行:</span>
            <span class="failed-reason">{{ item.reason }}</span>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn-primary" @click="showCheckResultModal = false">关闭</button>
    </div>
  </div>
</div>
```

- [ ] **Step 18: 添加单个盘库弹窗**

在盘库结果弹窗之后添加：

```html
<!-- 单个盘库弹窗 -->
<div class="modal-overlay" v-if="showSingleCheckModal">
  <div class="modal">
    <div class="modal-header">
      <h3>盘库操作</h3>
      <button class="modal-close" @click="showSingleCheckModal = false">&times;</button>
    </div>
    <div class="modal-body" v-if="singleCheckStock">
      <div class="operate-info">
        <p>商品: {{ singleCheckStock.product_name || singleCheckStock.product_info?.name }}</p>
        <p>规格: {{ singleCheckStock.spec_code || singleCheckStock.spec_info?.spec_code }} ({{ singleCheckStock.spec_info?.packaging || '-' }})</p>
        <p>仓库: {{ singleCheckStock.warehouse_info?.name }}</p>
        <p>当前库存: <strong>{{ singleCheckStock.quantity }}</strong></p>
      </div>
      <div class="form-group">
        <label>盘点数量 *</label>
        <input type="number" v-model="singleCheckForm.check_quantity" min="0" step="0.01" />
      </div>
      <div class="form-group">
        <label>差异</label>
        <div class="difference-display" :class="{ positive: singleCheckDifference > 0, negative: singleCheckDifference < 0 }">
          {{ singleCheckDifference > 0 ? '+' : '' }}{{ singleCheckDifference.toFixed(2) }}
          <span v-if="singleCheckDifference > 0">(盘盈)</span>
          <span v-else-if="singleCheckDifference < 0">(盘亏)</span>
          <span v-else>(无差异)</span>
        </div>
      </div>
      <div class="form-group">
        <label>备注</label>
        <input type="text" v-model="singleCheckForm.remarks" placeholder="可选填写备注信息" />
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn-secondary" @click="showSingleCheckModal = false">取消</button>
      <button class="btn-primary" @click="handleSingleCheck" :disabled="singleCheckLoading">
        {{ singleCheckLoading ? '处理中...' : '确认盘库' }}
      </button>
    </div>
  </div>
</div>
```

- [ ] **Step 19: 修改库存详情弹窗，添加盘库记录 Tab**

找到库存详情弹窗的 `detail-batches` 部分，替换为：

```html
<div class="detail-tabs">
  <button class="tab-btn" :class="{ active: detailActiveTab === 'inbound' }" @click="detailActiveTab = 'inbound'">
    入库记录 ({{ stockDetail.inbound_batches?.length || 0 }})
  </button>
  <button class="tab-btn" :class="{ active: detailActiveTab === 'outbound' }" @click="detailActiveTab = 'outbound'">
    出库记录 ({{ stockDetail.outbound_batches?.length || 0 }})
  </button>
  <button class="tab-btn" :class="{ active: detailActiveTab === 'check' }" @click="detailActiveTab = 'check'">
    盘库记录 ({{ checkRecords.length }})
  </button>
</div>
<div class="detail-batches">
  <div class="detail-batch-section" v-show="detailActiveTab === 'inbound'">
    <div class="batch-scroll-list">
      <div class="batch-scroll-item" v-for="batch in stockDetail.inbound_batches" :key="batch.id">
        <span class="batch-user">{{ batch.user_name || '-' }}</span>
        <span class="batch-qty success">+{{ batch.quantity }}</span>
        <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
      </div>
      <div v-if="!stockDetail.inbound_batches?.length" class="batches-empty">暂无入库记录</div>
    </div>
  </div>
  <div class="detail-batch-section" v-show="detailActiveTab === 'outbound'">
    <div class="batch-scroll-list">
      <div class="batch-scroll-item" v-for="batch in stockDetail.outbound_batches" :key="batch.id">
        <span class="batch-user">{{ batch.user_name || '-' }}</span>
        <span class="batch-qty danger">-{{ batch.quantity }}</span>
        <span class="batch-time">{{ formatDate(batch.created_at) }}</span>
      </div>
      <div v-if="!stockDetail.outbound_batches?.length" class="batches-empty">暂无出库记录</div>
    </div>
  </div>
  <div class="detail-batch-section" v-show="detailActiveTab === 'check'">
    <div class="batch-scroll-list">
      <div class="batch-scroll-item" v-for="record in checkRecords" :key="record.id">
        <span class="batch-user">{{ record.user_name || '-' }}</span>
        <span class="batch-qty" :class="{ success: record.difference > 0, danger: record.difference < 0 }">
          {{ record.difference > 0 ? '+' : '' }}{{ record.difference.toFixed(2) }}
        </span>
        <span class="batch-time">{{ formatDate(record.created_at) }}</span>
      </div>
      <div v-if="!checkRecords.length" class="batches-empty">暂无盘库记录</div>
    </div>
  </div>
</div>
```

- [ ] **Step 20: 添加盘库相关样式**

在 `<style scoped>` 部分末尾添加：

```css
.file-upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-upload-area input[type="file"] {
  flex: 1;
  padding: 8px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
}

.link-btn {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 13px;
  cursor: pointer;
  text-decoration: underline;
}

.link-btn:hover {
  color: var(--accent-blue-hover);
}

.result-summary {
  background-color: var(--bg-secondary);
  padding: 16px;
  border-radius: var(--radius-md);
  margin-bottom: 16px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-item:last-child {
  margin-bottom: 0;
}

.result-label {
  font-size: 14px;
  color: var(--text-muted);
}

.result-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.result-value.success {
  color: var(--accent-green);
}

.result-value.danger {
  color: var(--accent-red);
}

.failed-items h4 {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.failed-list {
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.failed-item {
  display: flex;
  gap: 8px;
  padding: 10px;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.failed-row {
  color: var(--accent-red);
  font-weight: 500;
}

.failed-reason {
  color: var(--text-primary);
}

.difference-display {
  font-size: 18px;
  font-weight: 600;
  padding: 10px;
  background-color: var(--bg-secondary);
  border-radius: var(--radius-sm);
  text-align: center;
}

.difference-display.positive {
  color: var(--accent-green);
}

.difference-display.negative {
  color: var(--accent-red);
}

.detail-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tab-btn {
  padding: 8px 16px;
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
}

.tab-btn.active {
  background-color: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}
```

- [ ] **Step 21: 提交前端 UI 代码**

```bash
git add web/src/components/workspace/InventoryWorkspace.vue
git commit -m "feat(stock-check): add stock check UI to InventoryWorkspace"
```

---

## 6. 测试验证

**Files:**
- Create: `backend/tests/test_stock_check_api.py`

- [ ] **Step 22: 创建测试文件**

创建 `backend/tests/test_stock_check_api.py`：

```python
"""
盘库管理 API 测试
"""
import pytest
import io
from unittest.mock import AsyncMock, patch, MagicMock
from openpyxl import Workbook


@pytest.fixture
def mock_stock_check_service():
    """模拟盘库服务"""
    with patch("services.stock_check_service.stock_check_service") as mock:
        yield mock


@pytest.fixture
def mock_auth():
    """模拟认证"""
    with patch("app.routers.auth.require_permission") as mock:
        mock.return_value = AsyncMock(return_value={"id": 1, "username": "test_user"})
        yield mock


@pytest.mark.asyncio
async def test_create_single_check(async_client, mock_stock_check_service, mock_auth):
    """测试单个盘库"""
    mock_stock_check_service.create_single_check = AsyncMock(return_value={
        "batch_id": 1,
        "record_id": 1,
        "before_quantity": 100,
        "check_quantity": 95,
        "difference": -5,
    })

    response = await async_client.post(
        "/api/v1/stock-checks/single",
        json={
            "stock_id": "1",
            "check_quantity": 95,
            "remarks": "测试盘库"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["difference"] == -5


@pytest.mark.asyncio
async def test_create_batch_check(async_client, mock_stock_check_service, mock_auth):
    """测试批量盘库"""
    mock_stock_check_service.create_batch_check = AsyncMock(return_value={
        "batch_id": 1,
        "batch_code": "SC20260514001",
        "total_count": 2,
        "success_count": 2,
        "fail_count": 0,
        "failed_items": [],
    })

    # 创建测试 Excel 文件
    wb = Workbook()
    ws = wb.active
    ws.append(["规格编码", "盘点数量", "备注"])
    ws.append(["SP001-A", 100, "测试"])
    ws.append(["SP002-B", 50, ""])

    file_content = io.BytesIO()
    wb.save(file_content)
    file_content.seek(0)

    response = await async_client.post(
        "/api/v1/stock-checks/batch",
        data={"warehouse_id": "1"},
        files={"file": ("test.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["success_count"] == 2


@pytest.mark.asyncio
async def test_download_template(async_client, mock_stock_check_service, mock_auth):
    """测试下载模板"""
    mock_stock_check_service.generate_template = AsyncMock(return_value=b"test_content")

    response = await async_client.get("/api/v1/stock-checks/template")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.mark.asyncio
async def test_list_records(async_client, mock_stock_check_service, mock_auth):
    """测试获取盘库记录列表"""
    mock_stock_check_service.list_records = AsyncMock(return_value=(
        [{"id": 1, "batch_id": 1, "difference": -5}],
        1
    ))

    response = await async_client.get("/api/v1/stock-checks/records?stock_id=1")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_list_batches(async_client, mock_stock_check_service, mock_auth):
    """测试获取盘库批次列表"""
    mock_stock_check_service.list_batches = AsyncMock(return_value=(
        [{"id": 1, "batch_code": "SC20260514001"}],
        1
    ))

    response = await async_client.get("/api/v1/stock-checks/batches")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_get_batch_detail(async_client, mock_stock_check_service, mock_auth):
    """测试获取批次详情"""
    mock_stock_check_service.get_batch_detail = AsyncMock(return_value={
        "id": 1,
        "batch_code": "SC20260514001",
        "records": [{"id": 1, "difference": -5}]
    })

    response = await async_client.get("/api/v1/stock-checks/batches/1")

    assert response.status_code == 200
    data = response.json()
    assert data["batch_code"] == "SC20260514001"
    assert len(data["records"]) == 1
```

- [ ] **Step 23: 运行测试验证**

```bash
cd backend && venv/Scripts/python -m pytest tests/test_stock_check_api.py -v
```

- [ ] **Step 24: 提交测试代码**

```bash
git add backend/tests/test_stock_check_api.py
git commit -m "test(stock-check): add API tests for stock check module"
```

---

## 7. 最终提交

- [ ] **Step 25: 确保所有更改已提交**

```bash
git status
git log --oneline -5
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-14-stock-check-feature.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
