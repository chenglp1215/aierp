import os
import uuid
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from config import settings
from app.routers.auth import get_current_active_user

upload_router = APIRouter(prefix="/upload", tags=["文件上传"])


class UploadResponse(BaseModel):
    file_id: str
    file_name: str
    file_url: str
    file_path: str
    file_type: str
    file_size: int


ALLOWED_EXTENSIONS_SET = set()
for ext_list in settings.ALLOWED_EXTENSIONS.values():
    ALLOWED_EXTENSIONS_SET.update(ext_list)


def validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS_SET:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。支持的类型: {', '.join(sorted(ALLOWED_EXTENSIONS_SET))}"
        )

    content_type = file.content_type
    if ext in settings.ALLOWED_EXTENSIONS.get("image", []):
        if content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"图片格式不正确。请上传: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
            )
    elif ext in settings.ALLOWED_EXTENSIONS.get("document", []):
        if content_type not in settings.ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"文档格式不正确。请上传: {', '.join(settings.ALLOWED_DOCUMENT_TYPES)}"
            )


async def ensure_upload_dir():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@upload_router.post("/file", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    await ensure_upload_dir()

    validate_file(file)

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_FILE_SIZE:
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制({max_size_mb:.1f}MB)"
        )

    file_id = uuid.uuid4().hex
    original_filename = file.filename
    ext = os.path.splitext(original_filename)[1].lower()
    new_filename = f"{file_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, new_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/data/uploads/{new_filename}"
    full_url = f"{settings.FILE_URL_PREFIX}{relative_url}"
    is_image = ext in settings.ALLOWED_EXTENSIONS.get("image", [])

    return UploadResponse(
        file_id=file_id,
        file_name=original_filename,
        file_url=full_url,
        file_path=relative_url,
        file_type="image" if is_image else "document",
        file_size=file_size
    )


@upload_router.delete("/file/{file_id}")
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    for ext in settings.ALLOWED_EXTENSIONS.get("image", []) + settings.ALLOWED_EXTENSIONS.get("document", []):
        file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{ext}")
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"status": "success", "message": "文件已删除"}

    raise HTTPException(status_code=404, detail="文件不存在")
