"""
客户管理 - 验证规则
全新设计的客户验证规则
"""

# ============ 客户验证配置 ============

CUSTOMER_CREATE_CONFIG = {
    'name': {
        'required': True,
        'min_length': 1,
        'max_length': 200,
        'required_msg': '客户名称为必填'
    },
    'customer_type': {
        'required': True,
        'enum': ['terminal', 'dealer'],
        'required_msg': '客户类型为必填，可选值：terminal(终端)、dealer(经销商)'
    },
    'research_group': {
        'max_length': 200,
    },
    'contact_info': {
        'fields': {
            'contact_person': {'max_length': 100},
            'contact_phone': {
                'pattern': r'^1[3-9]\d{9}$',
                'msg': '联系人手机号格式不正确'
            },
            'contact_email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'msg': '电子邮箱格式不正确'
            }
        }
    },
    'invoice_infos': {
        'items': {
            'invoice_title': {
                'required': True,
                'min_length': 1,
                'max_length': 200,
                'required_msg': '开票抬头为必填'
            },
            'invoice_type': {
                'required': True,
                'enum': ['增值税', '普通发票', '增值税专用发票', '不开票'],
                'required_msg': '开票类型为必填'
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
                'required_msg': '银行为必填'
            },
            'bank_account': {
                'required': True,
                'min_length': 1,
                'max_length': 50,
                'required_msg': '银行账号为必填'
            }
        }
    },
    'shipping_addresses': {
        'items': {
            'recipient_name': {
                'required': True,
                'min_length': 1,
                'max_length': 100,
                'required_msg': '收货人为必填'
            },
            'recipient_phone': {
                'required': True,
                'pattern': r'^1[3-9]\d{9}$',
                'msg': '收货电话格式不正确'
            },
            'province': {
                'required': True,
                'min_length': 1,
                'max_length': 100,
                'required_msg': '收货省份为必填'
            },
            'city': {
                'required': True,
                'min_length': 1,
                'max_length': 100,
                'required_msg': '收货城市为必填'
            },
            'address': {
                'required': True,
                'min_length': 1,
                'max_length': 500,
                'required_msg': '详细地址为必填'
            }
        }
    },
    '__conditional__': [
        {
            'depends_on': 'customer_type',
            'required_value': 'terminal',
            'field': 'research_group',
            'message': '客户类型为终端时，课题组信息不能为空'
        }
    ]
}

CUSTOMER_UPDATE_CONFIG = {
    'name': {
        'min_length': 1,
        'max_length': 200,
    },
    'customer_type': {
        'enum': ['terminal', 'dealer'],
    },
    'research_group': {
        'max_length': 200,
    },
    'contact_info': {
        'fields': {
            'contact_person': {'max_length': 100},
            'contact_phone': {
                'pattern': r'^1[3-9]\d{9}$',
                'msg': '联系人手机号格式不正确'
            },
            'contact_email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'msg': '电子邮箱格式不正确'
            }
        }
    }
}


# ============ 开票信息验证配置 ============

INVOICE_INFO_CREATE_CONFIG = {
    'invoice_title': {
        'required': True,
        'min_length': 1,
        'max_length': 200,
        'required_msg': '开票抬头为必填'
    },
    'invoice_type': {
        'required': True,
        'enum': ['增值税', '普通发票', '增值税专用发票', '不开票'],
        'required_msg': '开票类型为必填'
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
    }
}

INVOICE_INFO_UPDATE_CONFIG = {
    'invoice_title': {
        'min_length': 1,
        'max_length': 200,
    },
    'invoice_type': {
        'enum': ['增值税', '普通发票', '增值税专用发票', '不开票'],
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
    }
}


# ============ 收货地址验证配置 ============

SHIPPING_ADDRESS_CREATE_CONFIG = {
    'recipient_name': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'required_msg': '收货人为必填'
    },
    'recipient_phone': {
        'required': True,
        'pattern': r'^1[3-9]\d{9}$',
        'msg': '收货电话格式不正确'
    },
    'province': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'required_msg': '收货省份为必填'
    },
    'city': {
        'required': True,
        'min_length': 1,
        'max_length': 100,
        'required_msg': '收货城市为必填'
    },
    'address': {
        'required': True,
        'min_length': 1,
        'max_length': 500,
        'required_msg': '详细地址为必填'
    }
}

SHIPPING_ADDRESS_UPDATE_CONFIG = {
    'recipient_name': {
        'min_length': 1,
        'max_length': 100,
    },
    'recipient_phone': {
        'pattern': r'^1[3-9]\d{9}$',
        'msg': '收货电话格式不正确'
    },
    'province': {
        'min_length': 1,
        'max_length': 100,
    },
    'city': {
        'min_length': 1,
        'max_length': 100,
    },
    'address': {
        'min_length': 1,
        'max_length': 500,
    }
}


# ============ 联系人信息验证配置 ============

CONTACT_INFO_UPDATE_CONFIG = {
    'contact_person': {
        'max_length': 100,
    },
    'contact_phone': {
        'pattern': r'^1[3-9]\d{9}$',
        'msg': '联系人手机号格式不正确'
    },
    'contact_email': {
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'msg': '电子邮箱格式不正确'
    }
}
