"""
客户管理 - 验证规则
"""

# ============ 客户验证配置 ============

CUSTOMER_CREATE_CONFIG = {
    'customer_name': {
        'required': True,
        'min_length': 1,
        'max_length': 200,
        'required_msg': '客户名称为必填'
    },
    'customer_code': {
        'required': False,
        'max_length': 50,
    },
    'customer_type': {
        'required': True,
        'enum': ['terminal', 'dealer'],
        'required_msg': '客户类型为必填，可选值：terminal(终端)、dealer(经销商)'
    },
    'customer_status': {
        'type': (int,),
        'enum': [1, 2],
    },
    'sales_user_id': {'type': (int,), },
    'sales_user_name': {'max_length': 50},
    'settlement_method': {
        'type': (int,),
        'enum': [1, 2, 3],
    },
    'credit_limit': {'type': (int, float), 'min': 0},
    'credit_days': {'type': (int,), 'min': 0},
    'member_account': {'max_length': 100},
    'contact_person': {'max_length': 50},
    'contact_phone': {
        'pattern': r'^1[3-9]\d{9}$',
        'msg': '联系电话格式不正确'
    },
    'province': {'max_length': 50},
    'city': {'max_length': 50},
    'district': {'max_length': 50},
    'address': {'max_length': 200},
    'remark': {'max_length': 1000},
    'default_shipping_address_id': {'type': (int,)},
    'default_invoice_info_id': {'type': (int,)},
    'default_tax_rate': {'type': (int, float), 'min': 0, 'max': 100},
    'research_groups': {
        'type': list,
        'items': {
            'research_group_name': {'required': True, 'min_length': 1, 'max_length': 100, 'required_msg': '课题组名称为必填'},
            'research_leader': {'max_length': 50},
            'contact_phone': {'max_length': 20},
        }
    },
    'invoice_infos': {
        'items': {
            'invoice_title': {'required': True, 'min_length': 1, 'max_length': 200, 'required_msg': '开票抬头为必填'},
            'tax_number': {'required': True, 'min_length': 1, 'max_length': 50, 'required_msg': '税务编码为必填'},
            'bank_name': {'required': True, 'min_length': 1, 'max_length': 200, 'required_msg': '银行为必填'},
            'bank_account': {'required': True, 'min_length': 1, 'max_length': 50, 'required_msg': '银行账号为必填'},
            'address_phone': {'max_length': 200},
            'is_default': {'type': (bool, int)},
        }
    },
    'shipping_addresses': {
        'items': {
            'receiver': {'required': True, 'min_length': 1, 'max_length': 50, 'required_msg': '收货人为必填'},
            'phone': {'required': True, 'min_length': 1, 'max_length': 20, 'required_msg': '联系电话为必填'},
            'province': {'required': True, 'min_length': 1, 'max_length': 100, 'required_msg': '收货省份为必填'},
            'province_code': {'max_length': 20},
            'city': {'required': True, 'min_length': 1, 'max_length': 100, 'required_msg': '收货城市为必填'},
            'city_code': {'max_length': 20},
            'district': {'max_length': 100},
            'address': {'required': True, 'min_length': 1, 'max_length': 500, 'required_msg': '详细地址为必填'},
            'is_default': {'type': (bool, int)},
        }
    },
}

CUSTOMER_UPDATE_CONFIG = {
    'customer_name': {
        'min_length': 1,
        'max_length': 200,
    },
    'customer_type': {
        'enum': ['terminal', 'dealer'],
    },
    'customer_status': {
        'type': (int,),
        'enum': [1, 2],
    },
    'sales_user_id': {'type': (int,)},
    'sales_user_name': {'max_length': 50},
    'settlement_method': {
        'type': (int,),
        'enum': [1, 2, 3],
    },
    'credit_limit': {'type': (int, float), 'min': 0},
    'credit_days': {'type': (int,), 'min': 0},
    'is_overdue': {'type': (int,), 'enum': [0, 1]},
    'member_account': {'max_length': 100},
    'contact_person': {'max_length': 50},
    'contact_phone': {
        'pattern': r'^1[3-9]\d{9}$',
        'msg': '联系电话格式不正确'
    },
    'province': {'max_length': 50},
    'city': {'max_length': 50},
    'district': {'max_length': 50},
    'address': {'max_length': 200},
    'remark': {'max_length': 1000},
    'default_shipping_address_id': {'type': (int,)},
    'default_invoice_info_id': {'type': (int,)},
    'default_tax_rate': {'type': (int, float), 'min': 0, 'max': 100},
    'research_groups': {
        'type': list,
        'items': {
            'research_group_name': {'required': True, 'min_length': 1, 'max_length': 100, 'required_msg': '课题组名称为必填'},
            'research_leader': {'max_length': 50},
            'contact_phone': {'max_length': 20},
        }
    },
    'invoice_infos': {
        'items': {
            'invoice_title': {'min_length': 1, 'max_length': 200},
            'tax_number': {'min_length': 1, 'max_length': 50},
            'bank_name': {'max_length': 200},
            'bank_account': {'max_length': 50},
            'address_phone': {'max_length': 200},
            'is_default': {'type': (bool, int)},
        }
    },
    'shipping_addresses': {
        'items': {
            'receiver': {'min_length': 1, 'max_length': 50},
            'phone': {'min_length': 1, 'max_length': 20},
            'province': {'max_length': 100},
            'province_code': {'max_length': 20},
            'city': {'max_length': 100},
            'city_code': {'max_length': 20},
            'district': {'max_length': 100},
            'address': {'max_length': 500},
            'is_default': {'type': (bool, int)},
        }
    },
}


# ============ 开票信息验证配置 ============

INVOICE_INFO_CREATE_CONFIG = {
    'invoice_title': {
        'required': True,
        'min_length': 1,
        'max_length': 200,
        'required_msg': '开票抬头为必填'
    },
    'tax_number': {
        'required': True,
        'min_length': 1,
        'max_length': 50,
        'required_msg': '税务编码为必填'
    },
    'bank_name': {
        'required': True,
        'min_length': 1,
        'max_length': 200,
        'required_msg': '银行开户行为必填'
    },
    'bank_account': {
        'required': True,
        'min_length': 1,
        'max_length': 50,
        'required_msg': '银行账号为必填'
    },
    'address_phone': {
        'max_length': 200,
    }
}

INVOICE_INFO_UPDATE_CONFIG = {
    'invoice_title': {
        'min_length': 1,
        'max_length': 200,
    },
    'tax_number': {
        'min_length': 1,
        'max_length': 50,
    },
    'bank_name': {
        'min_length': 1,
        'max_length': 200,
    },
    'bank_account': {
        'min_length': 1,
        'max_length': 50,
    },
    'address_phone': {
        'max_length': 200,
    }
}


# ============ 收货地址验证配置 ============

SHIPPING_ADDRESS_CREATE_CONFIG = {
    'receiver': {
        'required': True,
        'min_length': 1,
        'max_length': 50,
        'required_msg': '收货人为必填'
    },
    'phone': {
        'required': True,
        'min_length': 1,
        'max_length': 20,
        'required_msg': '联系电话为必填'
    },
    'province': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'required_msg': '收货省份为必填'
    },
    'province_code': {
        'max_length': 20,
    },
    'city': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'required_msg': '收货城市为必填'
    },
    'city_code': {
        'max_length': 20,
    },
    'district': {
        'max_length': 100,
    },
    'address': {
        'required': True,
        'min_length': 1,
        'max_length': 500,
        'required_msg': '详细地址为必填'
    }
}

SHIPPING_ADDRESS_UPDATE_CONFIG = {
    'receiver': {
        'min_length': 1,
        'max_length': 50,
    },
    'phone': {
        'min_length': 1,
        'max_length': 20,
    },
    'province': {
        'min_length': 1,
        'max_length': 100,
    },
    'province_code': {
        'min_length': 1,
        'max_length': 20,
    },
    'city': {
        'min_length': 1,
        'max_length': 100,
    },
    'city_code': {
        'min_length': 1,
        'max_length': 20,
    },
    'district': {
        'min_length': 1,
        'max_length': 100,
    },
    'address': {
        'min_length': 1,
        'max_length': 500,
    }
}


# ============ 客户折扣验证配置 ============

CUSTOMER_DISCOUNT_CREATE_CONFIG = {
    'customer_id': {
        'required': True,
        'required_msg': '客户ID为必填'
    },
    'brand_id': {
        'required': True,
        'required_msg': '品牌ID为必填'
    },
    'discount_value': {
        'required': True,
        'type': (int, float),
        'min': 0,
        'max': 1,
        'required_msg': '折扣值为必填'
    }
}

CUSTOMER_DISCOUNT_UPDATE_CONFIG = {
    'discount_value': {
        'type': (int, float),
        'min': 0,
        'max': 1,
    }
}

# ============ 新增API专用校验配置 ============

# 客户认领
CLAIM_CONFIG = {
    'customer_id': {
        'required': True,
        'type': (int,),
        'required_msg': '客户ID为必填'
    },
}

# 注册会员
MEMBER_CONFIG = {
    'member_account': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'required_msg': '会员账号为必填'
    },
}

# 订单默认值
ORDER_DEFAULTS_CONFIG = {
    'default_shipping_address_id': {'type': (int,)},
    'default_invoice_info_id': {'type': (int,)},
    'settlement_method': {'type': (int,), 'enum': [1, 2, 3]},
    'default_tax_rate': {'type': (int, float), 'min': 0, 'max': 100},
}

# 账期额度
CREDIT_CONFIG = {
    'credit_days': {
        'required': True,
        'type': (int,),
        'min': 0,
        'required_msg': '账期天数为必填'
    },
    'credit_limit': {
        'required': True,
        'type': (int, float),
        'min': 0,
        'required_msg': '信用额度为必填'
    },
}

# 批量导出
EXPORT_CONFIG = {
    'customer_ids': {'type': list},
    'customer_status': {'type': (int,), 'enum': [1, 2]},
    'sales_user_id': {'type': (int,)},
    'customer_type': {'enum': ['terminal', 'dealer']},
    'created_at_start': {'type': str},
    'created_at_end': {'type': str},
}