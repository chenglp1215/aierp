import logging
import uvicorn
from app import app
from config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 设置关键模块的日志级别
logging.getLogger('services').setLevel(logging.DEBUG)
logging.getLogger('services.product_batch_import_service').setLevel(logging.DEBUG)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        workers=settings.WORKERS if not settings.DEBUG else 1,
    )
