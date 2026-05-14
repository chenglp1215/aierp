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
