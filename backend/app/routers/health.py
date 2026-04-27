from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.database import db

health_router = APIRouter()


@health_router.get("/", response_model=Dict[str, Any])
async def health_check():
    """健康检查接口"""
    mongo_status = "connected"
    redis_status = "connected"
    
    try:
        await db.get_mongo_client().admin.command("ping")
    except Exception:
        mongo_status = "disconnected"
    
    try:
        await db.get_redis_client().ping()
    except Exception:
        redis_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "ai_mdr_platform_api",
        "version": "1.0.0",
        "database": {
            "mongodb": mongo_status,
            "redis": redis_status
        }
    }


@health_router.get("/ping")
async def ping():
    """简单的 ping 接口"""
    return {"message": "pong"}
