from .base_validator import validate

CUSTOMER_CREATE_CONFIG = {
    'name': {'required': True, 'min_length': 1, 'max_length': 200},
    'customer_type': {'enum': ['individual', 'company', 'government']},
    'level': {'enum': ['vip', 'normal', 'potential']},
    'contact_phone': {'pattern': r'^1[3-9]\d{9}$', 'msg': '手机号格式不正确'},
    'contact_email': {'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 'msg': '邮箱格式不正确'},
    'tax_number': {'pattern': r'^[A-Z0-9]{15,20}$', 'msg': '税号格式不正确'},
    'bank_account': {'pattern': r'^\d{10,20}$', 'msg': '银行账号格式不正确'},
    'credit_limit': {'min': 0},
    'shipping_addresses': {
        'items': {
            'recipient_name': {'required': True, 'min_length': 1, 'max_length': 100},
            'recipient_phone': {'required': True, 'pattern': r'^1[3-9]\d{9}$', 'msg': '手机号格式不正确'},
            'address': {'required': True, 'min_length': 1, 'max_length': 500},
        }
    },
    '__conditional__': [
        {'depends_on': 'delivery_type', 'required_value': 'inventory', 'field': 'warehouse_id', 'message': '库存发货时必须选择仓库'}
    ]
}

CUSTOMER_UPDATE_CONFIG = {
    'name': {'min_length': 1, 'max_length': 200},
    'contact_phone': {'pattern': r'^1[3-9]\d{9}$', 'msg': '手机号格式不正确'},
    'contact_email': {'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', 'msg': '邮箱格式不正确'},
    'credit_limit': {'min': 0},
}

SHIPPING_ADDRESS_CREATE_CONFIG = {
    'recipient_name': {'required': True, 'min_length': 1, 'max_length': 100},
    'recipient_phone': {'required': True, 'pattern': r'^1[3-9]\d{9}$', 'msg': '手机号格式不正确'},
    'address': {'required': True, 'min_length': 1, 'max_length': 500},
}

SHIPPING_ADDRESS_UPDATE_CONFIG = {
    'recipient_name': {'min_length': 1, 'max_length': 100},
    'recipient_phone': {'pattern': r'^1[3-9]\d{9}$', 'msg': '手机号格式不正确'},
}

PRODUCT_CREATE_CONFIG = {
    'product_code': {'required': True, 'pattern': r'^[A-Z0-9\-_]+$', 'msg': '商品编号只能包含字母、数字、横线和下划线'},
    'name': {'required': True, 'min_length': 1, 'max_length': 200},
    'image_url': {'max_length': 500},
    'brand': {'max_length': 100},
    'category': {'max_length': 100},
}

PRODUCT_UPDATE_CONFIG = {
    'product_code': {'pattern': r'^[A-Z0-9\-_]+$', 'msg': '商品编号只能包含字母、数字、横线和下划线'},
    'name': {'min_length': 1, 'max_length': 200},
    'image_url': {'max_length': 500},
    'brand': {'max_length': 100},
    'category': {'max_length': 100},
}

PRODUCT_SPEC_CREATE_CONFIG = {
    'spec_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'price': {'required': True, 'type': float, 'min': 0},
    'packaging': {'max_length': 100},
    'sales_spec': {'max_length': 100},
    'cas_number': {'max_length': 50},
}

PRODUCT_SPEC_UPDATE_CONFIG = {
    'spec_code': {'min_length': 1, 'max_length': 50},
    'price': {'type': float, 'min': 0},
    'packaging': {'max_length': 100},
    'sales_spec': {'max_length': 100},
    'cas_number': {'max_length': 50},
}

WAREHOUSE_CREATE_CONFIG = {
    'name': {'required': True, 'min_length': 1, 'max_length': 100},
    'address': {'required': True, 'min_length': 1, 'max_length': 500},
    'manager_name': {'max_length': 100},
}

WAREHOUSE_UPDATE_CONFIG = {
    'name': {'min_length': 1, 'max_length': 100},
    'address': {'min_length': 1, 'max_length': 500},
    'manager_name': {'max_length': 100},
}

STOCK_CREATE_CONFIG = {
    'spec_id': {'required': True},
    'warehouse_id': {'required': True},
    'quantity': {'required': True, 'type': float, 'min': 0},
    'min_stock': {'type': float, 'min': 0},
    'max_stock': {'type': float, 'min': 0},
}

STOCK_UPDATE_CONFIG = {
    'quantity': {'type': float, 'min': 0},
    'min_stock': {'type': float, 'min': 0},
    'max_stock': {'type': float, 'min': 0},
}

SALES_ORDER_ITEM_CONFIG = {
    'product_id': {'required': True},
    'product_name': {'required': True},
    'quantity': {'required': True, 'type': int, 'min': 1},
    'unit_price': {'required': True, 'type': float, 'min': 0},
    'subtotal': {'required': True, 'type': float},
}

SALES_ORDER_CREATE_CONFIG = {
    'customer_id': {'required': True},
    'customer_name': {'required': True},
    'delivery_type': {'required': True, 'enum': ['inventory', 'direct']},
    'pickup_type': {'required': True, 'enum': ['self_pickup', 'express']},
    'contact_phone': {'pattern': r'^1[3-9]\d{9}$', 'msg': '手机号格式不正确'},
    'express_fee': {'type': float, 'min': 0},
    'discount_ratio': {'type': float, 'min': 0, 'max': 100},
    'items': {'items': SALES_ORDER_ITEM_CONFIG},
    '__conditional__': [
        {'depends_on': 'delivery_type', 'required_value': 'inventory', 'field': 'warehouse_id', 'message': '库存发货时必须选择仓库'},
        {'depends_on': 'pickup_type', 'required_value': 'express', 'field': 'express_type', 'message': '选择快递时必须选择快递公司'},
        {'depends_on': 'pickup_type', 'required_value': 'express', 'field': 'express_no', 'message': '选择快递时必须填写快递单号'}
    ]
}

SALES_ORDER_UPDATE_CONFIG = {
    'discount_ratio': {'type': float, 'min': 0, 'max': 100},
    'status': {'enum': ['draft', 'pending', 'confirmed', 'processing', 'shipped', 'completed', 'cancelled']},
    'payment_status': {'enum': ['unpaid', 'partial', 'paid']},
}

PROCUREMENT_ORDER_CREATE_CONFIG = {
    'supplier_id': {'required': True},
    'supplier_name': {'required': True},
    'contact_phone': {'pattern': r'^1[3-9]\d{9}$', 'msg': '手机号格式不正确'},
    'items': {'items': {
        'product_id': {'required': True},
        'product_name': {'required': True},
        'quantity': {'required': True, 'type': float, 'min': 0.01},
        'unit_price': {'required': True, 'type': float, 'min': 0},
        'subtotal': {'required': True, 'type': float},
    }},
}

PROCUREMENT_ORDER_UPDATE_CONFIG = {
    'status': {'enum': ['draft', 'pending', 'confirmed', 'purchased', 'received', 'cancelled']},
}
