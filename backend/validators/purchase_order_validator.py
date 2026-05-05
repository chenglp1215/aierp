"""
采购单 - 验证规则
"""

# ============ 采购单商品明细验证配置 ============

PURCHASE_ORDER_ITEM_CREATE_CONFIG = {
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
    'brand_id': {
        'max_length': 50,
    },
    'brand_name': {
        'max_length': 100,
    },
    'purchase_qty': {
        'required': True,
        'type': int,
        'min': 1,
        'required_msg': '采购数量为必填'
    },
    'in_qty': {
        'type': int,
        'min': 0,
    },
    'return_qty': {
        'type': int,
        'min': 0,
    },
    'purchase_price': {
        'required': True,
        'type': (int, float),
        'min': 0,
        'required_msg': '采购单价为必填'
    },
    'discount': {
        'type': (int, float),
        'min': 0,
        'max': 1,
    },
    'amt': {
        'type': (int, float),
        'min': 0,
    },
    'shipping_method': {
        'enum': ['直运', '物流', '自提', '送货'],
    },
    'source_sale_row_no': {
        'type': int,
        'min': 1,
    },
    'warehouse_id': {
        'max_length': 50,
    }
}

PURCHASE_ORDER_ITEM_UPDATE_CONFIG = {
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
    'brand_id': {
        'max_length': 50,
    },
    'brand_name': {
        'max_length': 100,
    },
    'purchase_qty': {
        'type': int,
        'min': 1,
    },
    'in_qty': {
        'type': int,
        'min': 0,
    },
    'return_qty': {
        'type': int,
        'min': 0,
    },
    'purchase_price': {
        'type': (int, float),
        'min': 0,
    },
    'discount': {
        'type': (int, float),
        'min': 0,
        'max': 1,
    },
    'amt': {
        'type': (int, float),
        'min': 0,
    },
    'shipping_method': {
        'enum': ['直运', '物流', '自提', '送货'],
    },
    'source_sale_row_no': {
        'type': int,
        'min': 1,
    },
    'warehouse_id': {
        'max_length': 50,
    }
}


# ============ 采购单创建验证配置 ============

PURCHASE_ORDER_CREATE_CONFIG = {
    'purchase_type': {
        'required': True,
        'enum': ['direct', 'warehouse'],
        'required_msg': '采购类型为必填'
    },
    'source_sale_order_no': {
        'max_length': 50,
    },
    'source_sale_order_id': {
        'max_length': 50,
    },
    'brand_id': {
        'max_length': 50,
    },
    'supplier_id': {
        'required': True,
        'min_length': 1,
        'max_length': 50,
        'required_msg': '供应商ID为必填'
    },
    'purchase_user_id': {
        'max_length': 50,
    },
    'receive_info': {
        'fields': {
            'type': {'enum': ['customer', 'warehouse']},
            'warehouse_id': {'max_length': 50},
            'warehouse_name': {'max_length': 100},
            'customer_addr': {'max_length': 500},
            'province': {'max_length': 100},
            'city': {'max_length': 100},
            'contact_person': {'max_length': 100},
            'contact_tel': {'max_length': 20}
        }
    },
    'expect_arrive_date': {
        'pattern': r'^\d{4}-\d{2}-\d{2}$',
        'msg': '预计到货日期格式不正确'
    },
    'settle_type': {
        'required': True,
        'enum': ['月结', '货到付款', '款到发货'],
        'required_msg': '结算方式为必填'
    },
    'remark': {
        'max_length': 500,
    },
    'items': {
        'required': True,
        'items': PURCHASE_ORDER_ITEM_CREATE_CONFIG,
        'required_msg': '商品明细为必填'
    }
}

PURCHASE_ORDER_UPDATE_CONFIG = {
    'purchase_type': {
        'enum': ['direct', 'warehouse'],
    },
    'brand_id': {
        'max_length': 50,
    },
    'supplier_id': {
        'min_length': 1,
        'max_length': 50,
    },
    'purchase_user_id': {
        'max_length': 50,
    },
    'receive_info': {
        'fields': {
            'type': {'enum': ['customer', 'warehouse']},
            'warehouse_id': {'max_length': 50},
            'warehouse_name': {'max_length': 100},
            'customer_addr': {'max_length': 500},
            'province': {'max_length': 100},
            'city': {'max_length': 100},
            'contact_person': {'max_length': 100},
            'contact_tel': {'max_length': 20}
        }
    },
    'expect_arrive_date': {
        'pattern': r'^\d{4}-\d{2}-\d{2}$',
        'msg': '预计到货日期格式不正确'
    },
    'settle_type': {
        'enum': ['月结', '货到付款', '款到发货'],
    },
    'remark': {
        'max_length': 500,
    },
    'items': {
        'items': PURCHASE_ORDER_ITEM_UPDATE_CONFIG,
    }
}
