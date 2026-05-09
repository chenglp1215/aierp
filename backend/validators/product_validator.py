"""
商品管理 - 验证规则
全新设计的商品验证规则
"""

# ============ 品牌验证配置 ============

BRAND_CREATE_CONFIG = {
    'name': {'required': True, 'min_length': 1, 'max_length': 100},
    'logo_url': {'max_length': 500},
    'description': {'max_length': 500},
    'purchaser_id': {'max_length': 100},
    'is_active': {'type': bool},
}

BRAND_UPDATE_CONFIG = {
    'name': {'min_length': 1, 'max_length': 100},
    'logo_url': {'max_length': 500},
    'description': {'max_length': 500},
    'purchaser_id': {'max_length': 100},
    'is_active': {'type': bool},
}


# ============ 商品分类验证配置 ============

CATEGORY_CREATE_CONFIG = {
    'name': {'required': True, 'min_length': 1, 'max_length': 100},
    'tax_code': {'max_length': 50},
    'sort_order': {'min': 0},
    'parent_id': {'max_length': 100},
    'is_shop_display': {'type': bool},
}

CATEGORY_UPDATE_CONFIG = {
    'name': {'min_length': 1, 'max_length': 100},
    'tax_code': {'max_length': 50},
    'sort_order': {'min': 0},
    'parent_id': {'max_length': 100},
    'is_shop_display': {'type': bool},
}


# ============ 商品规格验证配置 ============
PRODUCT_SPEC_CREATE_CONFIG = {
    'spec_code': {'required': False, 'min_length': 1, 'max_length': 50},
    'packaging': {'max_length': 100},
    'sales_spec': {'max_length': 100},
    'price': {'required': True, 'min': 0},
    'cas_number': {'max_length': 50},
    'is_active': {'type': bool},
}

PRODUCT_SPEC_UPDATE_CONFIG = {
    'spec_code': {'min_length': 1, 'max_length': 50},
    'packaging': {'max_length': 100},
    'sales_spec': {'max_length': 100},
    'price': {'min': 0},
    'cas_number': {'max_length': 50},
    'is_active': {'type': bool},
}
# ============ 商品验证配置 ============
PRODUCT_CREATE_CONFIG = {
    'product_code': {'required': False, 'min_length': 1, 'max_length': 50},
    'name': {'required': True, 'min_length': 1, 'max_length': 200},
    'image_url': {'max_length': 500},
    'brand_id': {'max_length': 100},
    'category_id': {'max_length': 100},
    'tax_code': {'max_length': 50},
    'is_active': {'type': bool},
}

PRODUCT_UPDATE_CONFIG = {
    'product_code': {'min_length': 1, 'max_length': 50},
    'name': {'min_length': 1, 'max_length': 200},
    'image_url': {'max_length': 500},
    'brand_id': {'max_length': 100},
    'category_id': {'max_length': 100},
    'tax_code': {'max_length': 50},
    'is_active': {'type': bool},
}
