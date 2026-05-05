"""
供应商管理 - 数据校验
"""
from typing import Dict, Any, List, Union
from pydantic import BaseModel


# 创建供应商校验配置
SUPPLIER_CREATE_CONFIG = {
    "required": ["name"],
    "fields": {
        "name": {
            "type": "string",
            "min_length": 1,
            "max_length": 200,
            "message": "供应商名称不能为空，且长度不能超过200字符"
        },
        "contact_person": {
            "type": "string",
            "max_length": 100,
            "message": "联系人长度不能超过100字符"
        },
        "contact_phone": {
            "type": "string",
            "max_length": 50,
            "message": "联系电话长度不能超过50字符"
        },
        "contact_email": {
            "type": "string",
            "max_length": 200,
            "message": "联系邮箱长度不能超过200字符"
        },
        "remark": {
            "type": "string",
            "max_length": 500,
            "message": "备注长度不能超过500字符"
        }
    }
}


# 更新供应商校验配置
SUPPLIER_UPDATE_CONFIG = {
    "fields": {
        "name": {
            "type": "string",
            "min_length": 1,
            "max_length": 200,
            "message": "供应商名称不能为空，且长度不能超过200字符"
        },
        "contact_person": {
            "type": "string",
            "max_length": 100,
            "message": "联系人长度不能超过100字符"
        },
        "contact_phone": {
            "type": "string",
            "max_length": 50,
            "message": "联系电话长度不能超过50字符"
        },
        "contact_email": {
            "type": "string",
            "max_length": 200,
            "message": "联系邮箱长度不能超过200字符"
        },
        "remark": {
            "type": "string",
            "max_length": 500,
            "message": "备注长度不能超过500字符"
        }
    }
}


def validate_supplier_brands(brands: List[Union[Dict[str, Any], BaseModel]]) -> tuple[bool, str]:
    """校验供货品牌列表"""
    if not brands:
        return True, ""

    for idx, brand in enumerate(brands):
        # Handle both dict and Pydantic objects
        if hasattr(brand, "brand_id"):
            brand_id = brand.brand_id
            discount = getattr(brand, "discount", 1.0)
        else:
            brand_id = brand.get("brand_id")
            discount = brand.get("discount", 1.0)

        if not brand_id:
            return False, f"第{idx + 1}条供货品牌缺少品牌ID"
        if discount < 0 or discount > 1:
            return False, f"第{idx + 1}条供货品牌的折扣率必须在0-1之间"

    return True, ""
