"""
省份城市 - 数据模型
提供中国省份城市数据支持
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ProvinceCityBase(BaseModel):
    """省份城市基础模型"""
    province: str = Field(..., description="省份/直辖市/自治区")
    city: str = Field(..., description="城市")
    district: Optional[str] = Field(None, description="区县")


class Province(BaseModel):
    """省份信息"""
    code: str = Field(..., description="省份代码")
    name: str = Field(..., description="省份名称")
    cities: List[str] = Field(default_factory=list, description="城市列表")


class City(BaseModel):
    """城市信息"""
    name: str = Field(..., description="城市名称")
    districts: List[str] = Field(default_factory=list, description="区县列表")


class ProvinceListResponse(BaseModel):
    """省份列表响应"""
    items: List[Province] = Field(..., description="省份列表")


class CityListResponse(BaseModel):
    """城市列表响应"""
    items: List[str] = Field(..., description="城市列表")


class DistrictListResponse(BaseModel):
    """区县列表响应"""
    items: List[str] = Field(..., description="区县列表")
