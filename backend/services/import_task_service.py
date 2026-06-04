"""
导入任务服务层
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from tortoise.expressions import Q

from models_mysql.import_task import ImportTask

logger = logging.getLogger(__name__)


class ImportTaskService:
    """导入任务服务"""

    async def create_task(self, task_type: str, created_by: int) -> ImportTask:
        """创建导入任务"""
        task = await ImportTask.create(
            task_type=task_type,
            status="pending",
            created_by=created_by,
        )
        return task

    async def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取任务"""
        task = await ImportTask.get_or_none(id=task_id)
        if not task:
            return None
        return task.to_dict()

    async def update_task(
        self,
        task_id: int,
        status: Optional[str] = None,
        total_rows: Optional[int] = None,
        processed_rows: Optional[int] = None,
        success_count: Optional[int] = None,
        update_count: Optional[int] = None,
        error_count: Optional[int] = None,
        error_file_path: Optional[str] = None,
    ) -> bool:
        """更新任务状态和进度"""
        task = await ImportTask.get_or_none(id=task_id)
        if not task:
            return False

        if status is not None:
            task.status = status
            if status in ("completed", "failed", "cancelled"):
                task.finished_at = datetime.now()

        if total_rows is not None:
            task.total_rows = total_rows
        if processed_rows is not None:
            task.processed_rows = processed_rows
        if success_count is not None:
            task.success_count = success_count
        if update_count is not None:
            task.update_count = update_count
        if error_count is not None:
            task.error_count = error_count
        if error_file_path is not None:
            task.error_file_path = error_file_path

        await task.save()
        return True

    async def increment_progress(
        self,
        task_id: int,
        processed: int = 1,
        success: int = 0,
        update: int = 0,
        error: int = 0,
    ) -> bool:
        """增量更新任务进度"""
        task = await ImportTask.get_or_none(id=task_id)
        if not task:
            return False

        task.processed_rows += processed
        task.success_count += success
        task.update_count += update
        task.error_count += error
        await task.save()
        return True

    async def list_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取任务列表"""
        query = ImportTask.all()

        if status:
            query = query.filter(status=status)
        if task_type:
            query = query.filter(task_type=task_type)
        if created_by:
            query = query.filter(created_by=created_by)

        total = await query.count()
        tasks = await query.offset((page - 1) * page_size).limit(page_size)

        return [t.to_dict() for t in tasks], total

    async def cancel_task(self, task_id: int) -> bool:
        """取消任务（仅 pending 状态可取消）"""
        task = await ImportTask.get_or_none(id=task_id)
        if not task:
            return False

        if task.status != "pending":
            return False

        task.status = "cancelled"
        task.finished_at = datetime.now()
        await task.save()
        return True


# 服务实例
import_task_service = ImportTaskService()