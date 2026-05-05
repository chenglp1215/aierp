from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from app.database import init_db, close_db
from app.middleware import LoggingMiddleware, AuthMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 数据库连接由 init_db 处理
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    from fastapi.staticfiles import StaticFiles
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    import os

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        redirect_slashes=False,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        errors = []
        for error in exc.errors():
            loc = error.get("loc", [])
            field = ".".join(str(l) for l in loc[1:] if l != "body")
            errors.append({
                "field": field,
                "message": error.get("msg", ""),
                "type": error.get("type", "")
            })
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "数据验证失败",
                "validation_errors": errors
            }
        )

    if settings.CORS_ORIGINS == ["*"]:
        allow_origins = ["*"]
        allow_credentials = False
    else:
        allow_origins = settings.CORS_ORIGINS
        allow_credentials = True

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(AuthMiddleware)
    app.add_middleware(LoggingMiddleware)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/data/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    from app.routers import api_router
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
