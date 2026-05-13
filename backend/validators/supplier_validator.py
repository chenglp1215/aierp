"""
供应商管理 - 数据校验
"""
from typing import Dict, Any, List


SUPPLIER_CREATE_CONFIG = {
    "required": ["name"],
    "fields": {
        "name": {
            "type": str,
            "min_length": 1,
            "max_length": 200,
            "required_msg": "供应商名称为必填",
        },
        "contact_person": {
            "type": str,
            "max_length": 100,
        },
        "contact_phone": {
            "type": str,
            "max_length": 50,
        },
        "contact_email": {
            "type": str,
            "max_length": 200,
        },
        "address": {
            "type": str,
        },
        "remark": {
            "type": str,
            "max_length": 500,
        },
        "is_active": {
            "type": bool,
        },
        "supplied_brands": {
            "type": list,
            "items": {
                "brand_id": {"required": True, "required_msg": "品牌ID为必填"},
                "discount": {"type": (int, float), "min": 0, "max": 1},
                "is_priority": {"type": bool},
            }
        },
        "bank_account": {
            "fields": {
                "bank_name": {"type": str, "max_length": 200},
                "account_name": {"type": str, "max_length": 200},
                "account_no": {"type": str, "max_length": 50},
            }
        },
    },
}


SUPPLIER_UPDATE_CONFIG = {
    "fields": {
        "name": {
            "type": str,
            "min_length": 1,
            "max_length": 200,
        },
        "contact_person": {
            "type": str,
            "max_length": 100,
        },
        "contact_phone": {
            "type": str,
            "max_length": 50,
        },
        "contact_email": {
            "type": str,
            "max_length": 200,
        },
        "address": {
            "type": str,
        },
        "remark": {
            "type": str,
            "max_length": 500,
        },
        "is_active": {
            "type": bool,
        },
        "supplied_brands": {
            "type": list,
            "items": {
                "brand_id": {"required": True, "required_msg": "品牌ID为必填"},
                "discount": {"type": (int, float), "min": 0, "max": 1},
                "is_priority": {"type": bool},
            }
        },
        "bank_account": {
            "fields": {
                "bank_name": {"type": str, "max_length": 200},
                "account_name": {"type": str, "max_length": 200},
                "account_no": {"type": str, "max_length": 50},
            }
        },
    },
}


def validate_supplier_brands(brands: List[Any]) -> tuple[bool, str]:
    """校验供货品牌列表"""
    if not brands:
        return True, ""

    for idx, brand in enumerate(brands):
        brand_dict = brand if isinstance(brand, dict) else brand.model_dump() if hasattr(brand, 'model_dump') else {}

        brand_id = brand_dict.get("brand_id")
        discount = brand_dict.get("discount", 1.0)

        if not brand_id:
            return False, f"第{idx + 1}条供货品牌缺少品牌ID"
        if discount < 0 or discount > 1:
            return False, f"第{idx + 1}条供货品牌的折扣率必须在0-1之间"

    return True, ""