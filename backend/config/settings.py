from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus
import os


class Settings(BaseSettings):
    APP_NAME: str = "AI MDR Platform API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOCAL_DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    MONGODB_URL: str = "mongodb://132.232.212.151:58902"
    MONGODB_DB_NAME: str = "oai_erp_test"

    # MySQL 配置
    MYSQL_HOST: str = "132.232.212.151"
    MYSQL_PORT: int = 58901
    MYSQL_USER: str = "admin"
    MYSQL_PASSWORD: str = "Chenglp1215!@#"
    MYSQL_DATABASE: str = "erp_test"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: list = ["http://localhost:5174", "http://localhost:3000"]

    LOG_LEVEL: str = "INFO"

    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "uploads")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_DOCUMENT_TYPES: list = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "text/markdown"
    ]
    ALLOWED_EXTENSIONS: dict = {
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".md"]
    }
    FILE_URL_PREFIX: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Tortoise ORM 配置（用于 Aerich 迁移）
# URL 编码密码中的特殊字符
_MYSQL_ENCODED_PASSWORD = quote_plus(settings.MYSQL_PASSWORD)
TORTOISE_ORM = {
    "connections": {
        "default": f"mysql://{settings.MYSQL_USER}:{_MYSQL_ENCODED_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    },
    "apps": {
        "models": {
            "models": ["models_mysql.auth", "aerich.models"],
            "default_connection": "default",
        }
    },
}
