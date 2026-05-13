"""
销售订单管理 - 验证规则
"""

# ============ 销售订单创建验证配置 ============

SALES_ORDER_CREATE_CONFIG = {
    'order_date': {
        'required': True,
        'min_length': 1,
        'required_msg': '订单日期为必填',
    },
    'customer_id': {
        'required': True,
        'min_length': 1,
        'required_msg': '客户ID为必填',
    },
    'settle_type': {
        'required': True,
        'enum': ['月结', '货到付款', '款到发货'],
        'required_msg': '结算方式为必填',
    },
    'tax_rate': {
        'min': 0,
        'max': 1,
    },
    'remark': {
        'max_length': 500,
    },
    'items': {
        'required': True,
        'items': {
            'row_no': {'required': True, 'type': int, 'min': 1, 'required_msg': '行号为必填'},
            'product_code': {'required': True, 'required_msg': '商品编码为必填'},
            'qty': {'required': True, 'type': int, 'min': 1, 'required_msg': '数量为必填'},
            'price': {'required': True, 'type': (int, float), 'min': 0, 'required_msg': '单价为必填'},
            'discount': {'required': True, 'type': (int, float), 'min': 0, 'max': 1, 'required_msg': '折扣为必填'},
            'shipping_method': {'required': True, 'required_msg': '发货方式为必填'},
        },
    },
}

# ============ 销售订单更新验证配置 ============

SALES_ORDER_UPDATE_CONFIG = {
    'order_date': {
        'min_length': 1,
    },
    'customer_id': {
        'min_length': 1,
    },
    'settle_type': {
        'enum': ['月结', '货到付款', '款到发货'],
    },
    'tax_rate': {
        'min': 0,
        'max': 1,
    },
    'remark': {
        'max_length': 500,
    },
}

# ============ 订单状态更新验证配置 ============

ORDER_STATUS_UPDATE_CONFIG = {
    'status': {
        'required': True,
        'enum': ['draft', 'audited', 'partially_pushed_to_purchase', 'pushed_to_purchase', 'closed', 'cancelled'],
        'required_msg': '订单状态为必填',
    },
}

# ============ 发货状态更新验证配置 ============

DELIVERY_STATUS_UPDATE_CONFIG = {
    'delivery_status': {
        'required': True,
        'enum': ['none', 'partial', 'full'],
        'required_msg': '发货状态为必填',
    },
}

# ============ 收货状态更新验证配置 ============

RECEIVE_STATUS_UPDATE_CONFIG = {
    'receive_status': {
        'required': True,
        'enum': ['none', 'partial', 'full'],
        'required_msg': '收货状态为必填',
    },
}

# ============ 开票状态更新验证配置 ============

INVOICE_STATUS_UPDATE_CONFIG = {
    'invoice_status': {
        'required': True,
        'enum': ['none', 'partial', 'full'],
        'required_msg': '开票状态为必填',
    },
}
