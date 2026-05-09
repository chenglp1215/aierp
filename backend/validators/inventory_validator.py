"""
库存管理 - 验证规则
"""

# ============ 仓库验证配置 ============

WAREHOUSE_CREATE_CONFIG = {
    'warehouse_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'name': {'required': True, 'min_length': 1, 'max_length': 100},
    'address': {'required': True, 'min_length': 1, 'max_length': 500},
    'manager_id': {"required": False, "max_length": 100},
    'manager_name': {"required": False, "max_length": 50},
    'status': {'type': str, 'allowed_values': ['active', 'inactive', 'maintenance']},
    'description': {'max_length': 500},
}

WAREHOUSE_UPDATE_CONFIG = {
    'warehouse_code': {'min_length': 1, 'max_length': 50},
    'name': {'min_length': 1, 'max_length': 100},
    'address': {'min_length': 1, 'max_length': 500},
    'manager_id': {"required": False, "max_length": 100},
    'manager_name': {"required": False, "max_length": 50},
    'status': {'type': str, 'allowed_values': ['active', 'inactive', 'maintenance']},
    'description': {'max_length': 500},
}


# ============ 库存验证配置 ============

STOCK_CREATE_CONFIG = {
    'warehouse_id': {'required': True, 'max_length': 100},
    'product_id': {'required': True, 'max_length': 100},
    'product_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'product_name': {'required': True, 'min_length': 1, 'max_length': 200},
    'spec_id': {'required': True, 'max_length': 100},
    'spec_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'quantity': {'required': True, 'min': 0},
    'min_stock': {'min': 0},
    'max_stock': {'min': 0},
    'status': {'type': str, 'allowed_values': ['normal', 'low_stock', 'out_of_stock', 'overstock']},
}

STOCK_UPDATE_CONFIG = {
    'quantity': {'min': 0},
    'min_stock': {'min': 0},
    'max_stock': {'min': 0},
    'status': {'type': str, 'allowed_values': ['normal', 'low_stock', 'out_of_stock', 'overstock']},
}


# ============ 入库批次验证配置 ============

INBOUND_BATCH_CREATE_CONFIG = {
    'warehouse_id': {'required': True, 'max_length': 100},
    'product_id': {'required': True, 'max_length': 100},
    'product_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'product_name': {'required': True, 'min_length': 1, 'max_length': 200},
    'spec_id': {'required': True, 'max_length': 100},
    'spec_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'stock_id': {'required': False, 'max_length': 100}, # 入库时，库存ID可为空， 需要根据规格ID查询库存或者创建新库存
    'quantity': {'required': True, 'min': 0},
    'user_id': {'required': True, 'max_length': 100},
    'user_name': {'required': True, 'min_length': 1, 'max_length': 50},
}

INBOUND_BATCH_UPDATE_CONFIG = {
    'warehouse_id': {'max_length': 100},
    'product_id': {'max_length': 100},
    'product_code': {'min_length': 1, 'max_length': 50},
    'product_name': {'min_length': 1, 'max_length': 200},
    'spec_id': {'max_length': 100},
    'spec_code': {'min_length': 1, 'max_length': 50},
    'stock_id': {'max_length': 100},
    'quantity': {'min': 0},
    'user_id': {'max_length': 100},
    'user_name': {'min_length': 1, 'max_length': 50},
}


# ============ 出库批次验证配置 ============

OUTBOUND_BATCH_CREATE_CONFIG = {
    'warehouse_id': {'required': True, 'max_length': 100},
    'product_id': {'required': True, 'max_length': 100},
    'product_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'product_name': {'required': True, 'min_length': 1, 'max_length': 200},
    'spec_id': {'required': True, 'max_length': 100},
    'spec_code': {'required': True, 'min_length': 1, 'max_length': 50},
    'stock_id': {'required': True, 'max_length': 100},
    'quantity': {'required': True, 'min': 0},
    'user_id': {'required': True, 'max_length': 100},
    'user_name': {'required': True, 'min_length': 1, 'max_length': 50},
}

OUTBOUND_BATCH_UPDATE_CONFIG = {
    'warehouse_id': {'max_length': 100},
    'product_id': {'max_length': 100},
    'product_code': {'min_length': 1, 'max_length': 50},
    'product_name': {'min_length': 1, 'max_length': 200},
    'spec_id': {'max_length': 100},
    'spec_code': {'min_length': 1, 'max_length': 50},
    'stock_id': {'max_length': 100},
    'quantity': {'min': 0},
    'user_id': {'max_length': 100},
    'user_name': {'min_length': 1, 'max_length': 50},
}
