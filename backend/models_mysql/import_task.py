"""
导入任务 - Tortoise ORM 模型
"""
from tortoise import fields
from tortoise.models import Model


class ImportTask(Model):
    """导入任务模型"""
    id = fields.IntField(pk=True, description="任务ID")
    task_type = fields.CharField(max_length=50, default="product_import", description="任务类型")
    status = fields.CharField(max_length=20, default="pending", description="任务状态")
    total_rows = fields.IntField(default=0, description="总行数")
    processed_rows = fields.IntField(default=0, description="已处理行数")
    success_count = fields.IntField(default=0, description="新建成功数")
    update_count = fields.IntField(default=0, description="更新成功数")
    error_count = fields.IntField(default=0, description="错误数")
    error_file_path = fields.CharField(max_length=500, null=True, description="错误文件路径")
    created_by = fields.IntField(description="创建用户ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    finished_at = fields.DatetimeField(null=True, description="完成时间")

    class Meta:
        table = "import_tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ImportTask({self.id}, {self.task_type}, {self.status})"

    def to_dict(self):
        """转换为字典格式"""
        progress_percent = 0
        if self.total_rows > 0:
            progress_percent = round(self.processed_rows / self.total_rows * 100, 1)

        return {
            "id": self.id,
            "task_type": self.task_type,
            "status": self.status,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "success_count": self.success_count,
            "update_count": self.update_count,
            "error_count": self.error_count,
            "error_file_path": self.error_file_path,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "progress_percent": progress_percent,
        }
