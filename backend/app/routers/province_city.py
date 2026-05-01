"""
省份城市 - API路由
提供中国省份城市数据查询接口
"""
from fastapi import APIRouter, Query
from typing import Optional

from models.province_city import (
    ProvinceListResponse,
    CityListResponse,
    DistrictListResponse,
)
from services.province_city_service import province_city_service
from app.decorators import success_response

province_city_router = APIRouter(prefix="/province-city", tags=["省份城市"])


@province_city_router.get("/provinces", response_model=dict)
async def get_provinces():
    """获取所有省份列表"""
    provinces = province_city_service.get_all_provinces()
    return success_response("获取省份列表成功", provinces)


@province_city_router.get("/cities", response_model=dict)
async def get_cities(
    province: str = Query(..., description="省份名称")
):
    """根据省份获取城市列表"""
    cities = province_city_service.get_cities_by_province(province)
    return success_response(result=cities)


@province_city_router.get("/districts", response_model=dict)
async def get_districts(
    province: str = Query(..., description="省份名称"),
    city: str = Query(..., description="城市名称")
):
    """根据省份和城市获取区县列表"""
    districts = province_city_service.get_districts_by_city(province, city)
    return success_response("获取区县列表成功", districts)


@province_city_router.get("/search", response_model=dict)
async def search_locations(
    keyword: str = Query(..., min_length=1, description="搜索关键词")
):
    """搜索省/市/区"""
    results = province_city_service.search_locations(keyword)
    return success_response("搜索地址成功", results)
