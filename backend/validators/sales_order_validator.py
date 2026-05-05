"""
销售订单 - 验证规则
"""

# ============ 销售订单商品明细验证配置 ============

SALES_ORDER_ITEM_CREATE_CONFIG = {
    'row_no': {
        'required': True,
        'type': int,
        'min': 1,
        'required_msg': '行号为必填'
    },
    'product_id': {
        'required': True,
        'min_length': 1,
        'max_length': 50,
        'required_msg': '商品ID为必填'
    },
    'spec_id': {
        'max_length': 50,
    },
    'spec_code': {
        'max_length': 50,
    },
    'brand_id': {
        'max_length': 50,
    },
    'brand_name': {
        'max_length': 100,
    },
    'packaging': {
        'max_length': 100,
    },
    'sales_spec': {
        'max_length': 100,
    },
    'qty': {
        'required': True,
        'type': int,
        'min': 1,
        'required_msg': '订购数量为必填'
    },
    'price': {
        'required': True,
        'type': (int, float),
        'min': 0,
        'required_msg': '原始单价为必填'
    },
    'discount': {
        'required': True,
        'type': (int, float),
        'min': 0,
        'max': 1,
        'required_msg': '折扣率为必填'
    },
    'discounted_price': {
        'type': (int, float),
        'min': 0,
    },
    'amt': {
        'type': (int, float),
        'min': 0,
    },
    'warehouse_id': {
        'max_length': 50,
    },
    'shipping_method': {
        'required': True,
        'enum': ['直运', '物流', '自提', '送货'],
        'required_msg': '发货方式为必填'
    },
    'out_qty': {
        'type': int,
        'min': 0,
    },
    'return_qty': {
        'type': int,
        'min': 0,
    },
    'remain_out_qty': {
        'type': int,
        'min': 0,
    }
}

SALES_ORDER_ITEM_UPDATE_CONFIG = {
    'row_no': {
        'type': int,
        'min': 1,
    },
    'product_id': {
        'min_length': 1,
        'max_length': 50,
    },
    'spec_id': {
        'max_length': 50,
    },
    'spec_code': {
        'max_length': 50,
    },
    'brand_id': {
        'max_length': 50,
    },
    'brand_name': {
        'max_length': 100,
    },
    'packaging': {
        'max_length': 100,
    },
    'sales_spec': {
        'max_length': 100,
    },
    'qty': {
        'type': int,
        'min': 1,
    },
    'price': {
        'type': (int, float),
        'min': 0,
    },
    'discount': {
        'type': (int, float),
        'min': 0,
        'max': 1,
    },
    'discounted_price': {
        'type': (int, float),
        'min': 0,
    },
    'amt': {
        'type': (int, float),
        'min': 0,
    },
    'warehouse_id': {
        'max_length': 50,
    },
    'shipping_method': {
        'enum': ['直运', '物流', '自提', '送货'],
    },
    'out_qty': {
        'type': int,
        'min': 0,
    },
    'return_qty': {
        'type': int,
        'min': 0,
    },
    'remain_out_qty': {
        'type': int,
        'min': 0,
    }
}


# ============ 销售订单创建验证配置 ============

SALES_ORDER_CREATE_CONFIG = {
    'order_date': {
        'required': True,
        'pattern': r'^\d{4}-\d{2}-\d{2}$',
        'msg': '订单日期格式不正确',
        'required_msg': '订单日期为必填'
    },
    'customer_id': {
        'required': True,
        'min_length': 1,
        'max_length': 50,
        'required_msg': '客户ID为必填'
    },
    'sale_user_id': {
        'max_length': 50,
    },
    'deliver_info': {
        'fields': {
            'addr': {'max_length': 500},
            'province': {'max_length': 100},
            'city': {'max_length': 100},
            'person_name': {'max_length': 100},
            'person_tel': {'max_length': 20}
        }
    },
    'expect_deliver_date': {
        'pattern': r'^\d{4}-\d{2}-\d{2}$',
        'msg': '期望交货日格式不正确'
    },
    'settle_type': {
        'required': True,
        'enum': ['月结', '货到付款', '款到发货'],
        'required_msg': '结算方式为必填'
    },
    'total_amt': {
        'type': (int, float),
        'min': 0,
    },
    'tax_rate': {
        'type': (int, float),
        'min': 0,
        'max': 1,
    },
    'tax_amt': {
        'type': (int, float),
        'min': 0,
    },
    'total_tax_amt': {
        'type': (int, float),
        'min': 0,
    },
    'total_discount_amt': {
        'type': (int, float),
        'min': 0,
    },
    'invoice_info': {
        'fields': {
            'invoice_title': {'max_length': 200},
            'invoice_type': {'enum': ['增值税', '普通发票', '增值税专用发票', '不开票']},
            'tax_number': {'max_length': 50},
            'bank_name': {'max_length': 200},
            'bank_account': {'max_length': 50}
        }
    },
    'remark': {
        'max_length': 500,
    },
    'items': {
        'required': True,
        'items': SALES_ORDER_ITEM_CREATE_CONFIG,
        'required_msg': '商品明细为必填'
    }
}

SALES_ORDER_UPDATE_CONFIG = {
    'order_date': {
        'pattern': r'^\d{4}-\d{2}-\d{2}$',
        'msg': '订单日期格式不正确'
    },
    'customer_id': {
        'min_length': 1,
        'max_length': 50,
    },
    'sale_user_id': {
        'max_length': 50,
    },
    'deliver_info': {
        'fields': {
            'addr': {'max_length': 500},
            'province': {'max_length': 100},
            'city': {'max_length': 100},
            'person_name': {'max_length': 100},
            'person_tel': {'max_length': 20}
        }
    },
    'expect_deliver_date': {
        'pattern': r'^\d{4}-\d{2}-\d{2}$',
        'msg': '期望交货日格式不正确'
    },
    'settle_type': {
        'enum': ['月结', '货到付款', '款到发货'],
    },
    'total_amt': {
        'type': (int, float),
        'min': 0,
    },
    'tax_rate': {
        'type': (int, float),
        'min': 0,
        'max': 1,
    },
    'tax_amt': {
        'type': (int, float),
        'min': 0,
    },
    'total_tax_amt': {
        'type': (int, float),
        'min': 0,
    },
    'total_discount_amt': {
        'type': (int, float),
        'min': 0,
    },
    'invoice_info': {
        'fields': {
            'invoice_title': {'max_length': 200},
            'invoice_type': {'enum': ['增值税', '普通发票', '增值税专用发票', '不开票']},
            'tax_number': {'max_length': 50},
            'bank_name': {'max_length': 200},
            'bank_account': {'max_length': 50}
        }
    },
    'remark': {
        'max_length': 500,
    },
    'items': {
        'items': SALES_ORDER_ITEM_UPDATE_CONFIG,
    }
}