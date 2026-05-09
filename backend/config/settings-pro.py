from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "AI MDR Platform API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOCAL_DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "oai_erp"

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: list = ["http://132.232.212.151:9003"]

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
    FILE_URL_PREFIX: str = "http://132.232.212.151:9003"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
