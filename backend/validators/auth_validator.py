from typing import Any, Dict, List, Optional

USER_CREATE_CONFIG = {
    'username': {
        'required': True,
        'required_msg': '用户名为必填',
        'min_length': 3,
        'max_length': 50,
    },
    'password': {
        'required': True,
        'required_msg': '密码为必填',
        'min_length': 6,
        'max_length': 50,
    },
    'email': {
        'max_length': 100,
    },
    'phone': {
        'pattern': r'^1[3-9]\d{9}$',
        'msg': '手机号格式不正确'
    },
    'full_name': {
        'max_length': 100,
    },
    'role_ids': {
        'type': list,
    }
}

USER_UPDATE_CONFIG = {
    'email': {
        'max_length': 100,
    },
    'phone': {
        'pattern': r'^1[3-9]\d{9}$',
        'msg': '手机号格式不正确'
    },
    'full_name': {
        'max_length': 100,
    },
    'role_ids': {
        'type': list,
    },
    'new_password': {
        'min_length': 6,
        'max_length': 50,
    }
}

ROLE_CREATE_CONFIG = {
    'code': {
        'required': True,
        'required_msg': '角色编码为必填',
        'min_length': 1,
        'max_length': 50,
    },
    'name': {
        'required': True,
        'required_msg': '角色名称为必填',
        'min_length': 1,
        'max_length': 100,
    },
    'description': {
        'max_length': 500,
    },
    'permission_ids': {
        'type': list,
    }
}

ROLE_UPDATE_CONFIG = {
    'name': {
        'min_length': 1,
        'max_length': 100,
    },
    'description': {
        'max_length': 500,
    },
    'permission_ids': {
        'type': list,
    }
}

PASSWORD_CHANGE_CONFIG = {
    'old_password': {
        'required': True,
        'required_msg': '旧密码为必填',
    },
    'new_password': {
        'required': True,
        'required_msg': '新密码为必填',
        'min_length': 6,
        'max_length': 50,
    }
}

PASSWORD_RESET_CONFIG = {
    'new_password': {
        'required': True,
        'required_msg': '新密码为必填',
        'min_length': 6,
        'max_length': 50,
    }
}
