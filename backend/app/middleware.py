import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from config import settings
from models.auth import TokenPayload
from services.auth_service import auth_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(f"请求: {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        logger.info(f"响应: {response.status_code} | 耗时: {process_time:.2f}ms")

        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.public_paths = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/data/uploads"
        ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        logger.info(f"AuthMiddleware: path={path}, ws_check={'/ws/' in path}")

        if request.method == "OPTIONS":
            return await call_next(request)

        if any(path.startswith(p) for p in self.public_paths):
            return await call_next(request)

        if "/ws/" in path:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "未提供认证令牌"}
            )

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_data = TokenPayload(**payload)

            user = await auth_service.get_user_by_id(token_data.sub)
            if not user:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=401,
                    content={"detail": "用户不存在"}
                )

            if user.get("status") != "active":
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=403,
                    content={"detail": "用户已被禁用"}
                )

            request.state.user = user
            request.state.token_data = token_data

        except JWTError as e:
            logger.error(f"JWT 验证失败: {e}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "无效的认证令牌"}
            )

        response = await call_next(request)
        return response
