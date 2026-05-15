import uvicorn
from app import app
from config import settings


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        workers=settings.WORKERS if not settings.DEBUG else 1,
    )
