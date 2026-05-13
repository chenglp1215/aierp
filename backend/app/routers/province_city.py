"""
省份城市 - API路由
提供中国省份城市数据查询接口，无需认证
"""
from fastapi import APIRouter, Query

from services.province_city_service import province_city_service
from app.decorators import wrap_response

province_city_router = APIRouter(prefix="/province-city", tags=["省份城市"])


@province_city_router.get("/", response_model=dict)
@wrap_response
async def get_provinces_cities():
    """获取所有省份城市数据列表"""
    result = await province_city_service.get_all_provinces_cities()
    return result
