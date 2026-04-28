from typing import Any, Dict, List, Optional
import re


class ValidationError(Exception):
    def __init__(self, errors: Dict[str, Any]):
        self.errors = errors
        super().__init__(str(errors))


def validate(data: Dict[str, Any], config: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
    errors: Dict[str, List[str]] = {}
    _validate_dict(data, config, errors, '')
    return len(errors) == 0, errors if errors else None


def _validate_dict(data: Dict[str, Any], config: Dict[str, Any], errors: Dict[str, List[str]], prefix: str) -> None:
    for field, rules in config.items():
        if field.startswith('__'):
            continue
        if not isinstance(rules, dict):
            continue

        full_field = f'{prefix}{field}' if prefix else field
        value = data.get(field)

        if rules.get('required') and (value is None or (isinstance(value, str) and not value.strip())):
            _add_error(errors, full_field, rules.get('required_msg', f'{field}为必填'))
            continue

        if value is None:
            continue

        if 'min_length' in rules and isinstance(value, (str, list)) and len(value) < rules['min_length']:
            _add_error(errors, full_field, f'{field}长度不能少于{rules["min_length"]}')

        if 'max_length' in rules and isinstance(value, (str, list)) and len(value) > rules['max_length']:
            _add_error(errors, full_field, f'{field}长度不能超过{rules["max_length"]}')

        if 'min' in rules and isinstance(value, (int, float)) and value < rules['min']:
            _add_error(errors, full_field, f'{field}不能小于{rules["min"]}')

        if 'max' in rules and isinstance(value, (int, float)) and value > rules['max']:
            _add_error(errors, full_field, f'{field}不能大于{rules["max"]}')

        if 'enum' in rules and value not in rules['enum']:
            _add_error(errors, full_field, f'{field}的值必须在{rules["enum"]}中')

        if 'pattern' in rules and isinstance(value, str):
            if not re.match(rules['pattern'], value):
                _add_error(errors, full_field, rules.get('msg', f'{field}格式不正确'))

        if 'type' in rules and not isinstance(value, rules['type']):
            _add_error(errors, full_field, f'{field}类型错误')

        if 'items' in rules and isinstance(value, list):
            _validate_list(value, rules['items'], errors, full_field)

    if '__conditional__' in config:
        for cond in config['__conditional__']:
            _validate_conditional(data, cond, errors)


def _validate_list(items: List, item_config: Dict[str, Any], errors: Dict[str, List[str]], prefix: str) -> None:
    for i, item in enumerate(items):
        if isinstance(item, dict):
            _validate_dict(item, item_config, errors, f'{prefix}[{i}].')


def _validate_conditional(data: Dict[str, Any], cond: Dict[str, Any], errors: Dict[str, List[str]]) -> None:
    depends_on = cond.get('depends_on')
    required_val = cond.get('required_value')
    target_field = cond.get('field')
    message = cond.get('message', f'{target_field}为必填')

    if depends_on and data.get(depends_on) == required_val:
        value = data.get(target_field)
        if value is None or (isinstance(value, str) and not value.strip()):
            _add_error(errors, target_field, message)


def _add_error(errors: Dict[str, List[str]], field: str, message: str) -> None:
    if field not in errors:
        errors[field] = []
    errors[field].append(message)
