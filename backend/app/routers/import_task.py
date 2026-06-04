"""
导入任务 - API路由
"""
import os
import uuid
from fastapi import APIRouter, Query, UploadFile, File, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import Optional

from services.import_task_service import import_task_service
from .auth import require_permission
from app.decorators import wrap_response
from config import settings

import_task_router = APIRouter(prefix="/import-tasks", tags=["导入任务"])


@import_task_router.post("/", response_model=dict)
@wrap_response
async def create_import_task(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Excel文件"),
    user: dict = Depends(require_permission("import.create")),
):
    """创建导入任务（上传 Excel 文件）"""
    # 校验文件类型
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise ValueError("仅支持 .xlsx 格式文件")

    # 获取当前用户ID
    user_id = user.get("id") if user else None
    if not user_id:
        raise ValueError("用户未登录")

    # 保存上传文件
    file_id = uuid.uuid4().hex
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{file_id}.xlsx")

    # 写入文件
    content = await file.read()
    if not content or len(content) < 10:
        raise ValueError("文件为空或无有效数据")

    with open(temp_file_path, "wb") as f:
        f.write(content)

    # 创建任务记录
    task = await import_task_service.create_task(
        task_type="product_import",
        created_by=user_id,
    )

    # 延迟导入避免循环依赖
    from services.product_batch_import_service import product_batch_import_service

    # 添加后台任务
    background_tasks.add_task(
        product_batch_import_service.execute_import,
        task.id,
        temp_file_path,
    )

    return {
        "task_id": task.id,
        "status": task.status,
        "total_rows": 0,
    }


@import_task_router.get("/", response_model=dict)
@wrap_response
async def list_import_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤"),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    user: dict = Depends(require_permission("import.view")),
):
    """获取导入任务列表"""
    user_id = user.get("id") if user else None
    items, total = await import_task_service.list_tasks(
        page=page,
        page_size=page_size,
        status=status,
        task_type=task_type,
        created_by=user_id,
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@import_task_router.get("/{task_id}", response_model=dict)
@wrap_response
async def get_import_task(
    task_id: int,
    user: dict = Depends(require_permission("import.view")),
):
    """获取导入任务详情/进度"""
    task = await import_task_service.get_task_by_id(task_id)
    if not task:
        raise ValueError("任务不存在")
    return task


@import_task_router.get("/{task_id}/error-file")
async def download_error_file(
    task_id: int,
    user: dict = Depends(require_permission("import.view")),
):
    """下载错误详情文件"""
    task = await import_task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.get("error_count", 0) == 0:
        raise HTTPException(status_code=400, detail="该任务无错误数据")

    error_file_path = task.get("error_file_path")
    if not error_file_path or not os.path.exists(error_file_path):
        raise HTTPException(status_code=404, detail="错误文件不存在")

    filename = f"import_errors_{task_id}.xlsx"
    return FileResponse(
        path=error_file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@import_task_router.put("/{task_id}/cancel", response_model=dict)
@wrap_response
async def cancel_import_task(
    task_id: int,
    user: dict = Depends(require_permission("import.create")),
):
    """取消导入任务"""
    success = await import_task_service.cancel_task(task_id)
    if not success:
        raise ValueError("任务无法取消（仅 pending 状态可取消）")
    return "任务已取消"