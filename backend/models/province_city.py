"""
省份城市 - 数据模型
提供中国省份城市数据支持
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ProvinceInfo(BaseModel):
    """省份信息"""
    code: str = Field(..., description="省份代码")
    name: str = Field(..., description="省份名称")
    cities: List[str] = Field(default_factory=list, description="城市名称列表")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "110000",
                "name": "北京市",
                "cities": ["北京市"]
            }
        }


class CityInfo(BaseModel):
    """城市信息"""
    code: str = Field(..., description="城市代码")
    name: str = Field(..., description="城市名称")
    province_code: str = Field(..., description="所属省份代码")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "11010001",
                "name": "东城区",
                "province_code": "110000"
            }
        }


class DistrictInfo(BaseModel):
    """区县信息"""
    code: str = Field(..., description="区县代码")
    name: str = Field(..., description="区县名称")
    province_code: str = Field(..., description="所属省份代码")
    city_code: str = Field(..., description="所属城市代码")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "110101001",
                "name": "东华门街道",
                "province_code": "110000",
                "city_code": "11010001"
            }
        }


class SearchLocationItem(BaseModel):
    """搜索结果项"""
    type: str = Field(..., description="类型：province/city/district")
    name: str = Field(..., description="名称")
    province: Optional[str] = Field(None, description="所属省份（区县级返回）")
    city: Optional[str] = Field(None, description="所属城市（区县级返回）")
    code: Optional[str] = Field(None, description="代码（省份返回）")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "city",
                "name": "东城区",
                "province": "北京市",
                "city": None
            }
        }


class ProvinceListResponse(BaseModel):
    """省份列表响应"""
    items: List[ProvinceInfo] = Field(..., description="省份列表")


class CityListResponse(BaseModel):
    """城市列表响应"""
    items: List[CityInfo] = Field(..., description="城市列表")


class DistrictListResponse(BaseModel):
    """区县列表响应"""
    items: List[DistrictInfo] = Field(..., description="区县列表")
