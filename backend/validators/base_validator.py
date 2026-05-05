from typing import Any, Dict, List, Optional
import re


class ValidationError(Exception):
    def __init__(self, errors: Dict[str, Any]):
        self.errors = errors
        super().__init__(str(errors))


class BaseValidator:
    """基础验证器类"""
    
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._errors: Dict[str, List[str]] = {}
    
    def validate(self) -> None:
        """验证数据，子类需要实现此方法"""
        pass
    
    def is_valid(self) -> bool:
        """检查数据是否有效"""
        return len(self._errors) == 0
    
    def get_errors(self) -> Optional[Dict[str, List[str]]]:
        """获取错误信息"""
        return self._errors if self._errors else None
    
    def add_error(self, field: str, message: str) -> None:
        """添加错误信息"""
        if field not in self._errors:
            self._errors[field] = []
        self._errors[field].append(message)


class RequiredFieldsValidator:
    """必填字段验证器"""
    
    @staticmethod
    def validate_required(data: Dict[str, Any], fields: List[str], validator: BaseValidator) -> None:
        """验证必填字段"""
        for field in fields:
            value = data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                validator.add_error(field, f'{field}为必填')


class PhoneValidator:
    """手机号验证器"""
    
    @staticmethod
    def validate_phone(phone: str, field: str, validator: BaseValidator) -> None:
        """验证手机号格式"""
        if phone and not re.match(r'^1[3-9]\d{9}$', phone):
            validator.add_error(field, '手机号格式不正确')


class NumericRangeValidator:
    """数值范围验证器"""
    
    @staticmethod
    def validate_in_range(value: Any, field: str, min_value: Optional[float] = None, 
                         max_value: Optional[float] = None, validator: Optional[BaseValidator] = None) -> bool:
        """验证数值是否在指定范围内"""
        if value is None:
            return True
        
        if not isinstance(value, (int, float)):
            if validator:
                validator.add_error(field, f'{field}必须是数字')
            return False
        
        if min_value is not None and value < min_value:
            if validator:
                validator.add_error(field, f'{field}不能小于{min_value}')
            return False
        
        if max_value is not None and value > max_value:
            if validator:
                validator.add_error(field, f'{field}不能大于{max_value}')
            return False
        
        return True


class DateRangeValidator:
    """日期范围验证器"""
    
    @staticmethod
    def validate_date_range(date_str: str, field: str, min_date: Optional[str] = None, 
                           max_date: Optional[str] = None, validator: Optional[BaseValidator] = None) -> bool:
        """验证日期是否在指定范围内"""
        if not date_str:
            return True
        
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            
            if min_date:
                min_obj = datetime.strptime(min_date, '%Y-%m-%d')
                if date_obj < min_obj:
                    if validator:
                        validator.add_error(field, f'{field}不能早于{min_date}')
                    return False
            
            if max_date:
                max_obj = datetime.strptime(max_date, '%Y-%m-%d')
                if date_obj > max_obj:
                    if validator:
                        validator.add_error(field, f'{field}不能晚于{max_date}')
                    return False
            
            return True
        except ValueError:
            if validator:
                validator.add_error(field, f'{field}日期格式不正确')
            return False


class ListLengthValidator:
    """列表长度验证器"""
    
    @staticmethod
    def validate_length(value: Any, field: str, min_length: Optional[int] = None, 
                       max_length: Optional[int] = None, validator: Optional[BaseValidator] = None) -> bool:
        """验证列表长度是否在指定范围内"""
        if value is None:
            return True
        
        if not isinstance(value, list):
            if validator:
                validator.add_error(field, f'{field}必须是列表')
            return False
        
        length = len(value)
        
        if min_length is not None and length < min_length:
            if validator:
                validator.add_error(field, f'{field}至少需要{min_length}项')
            return False
        
        if max_length is not None and length > max_length:
            if validator:
                validator.add_error(field, f'{field}最多只能有{max_length}项')
            return False
        
        return True


class ConditionalRequiredValidator:
    """条件必填验证器"""
    
    @staticmethod
    def validate_conditional(data: Dict[str, Any], depends_on: str, required_value: Any, 
                            target_field: str, message: Optional[str] = None, 
                            validator: Optional[BaseValidator] = None) -> bool:
        """验证条件必填字段"""
        if data.get(depends_on) == required_value:
            value = data.get(target_field)
            if value is None or (isinstance(value, str) and not value.strip()):
                if validator:
                    validator.add_error(target_field, message or f'{target_field}为必填')
                return False
        return True


def validate(data: Dict[str, Any], config: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, List[str]]]]:
    """验证数据"""
    errors: Dict[str, List[str]] = {}
    _validate_dict(data, config, errors, '')
    return len(errors) == 0, errors if errors else None


def _validate_dict(data: Dict[str, Any], config: Dict[str, Any], errors: Dict[str, List[str]], prefix: str) -> None:
    """验证字典数据"""
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

        # 支持嵌套对象验证（fields 键用于 deliver_info、invoice_info 等字典类型字段）
        if 'fields' in rules and isinstance(value, dict):
            _validate_dict(value, rules['fields'], errors, f'{full_field}.')

    if '__conditional__' in config:
        for cond in config['__conditional__']:
            _validate_conditional(data, cond, errors)


def _validate_list(items: List, item_config: Dict[str, Any], errors: Dict[str, List[str]], prefix: str) -> None:
    """验证列表数据"""
    for i, item in enumerate(items):
        if isinstance(item, dict):
            _validate_dict(item, item_config, errors, f'{prefix}[{i}].')


def _validate_conditional(data: Dict[str, Any], cond: Dict[str, Any], errors: Dict[str, List[str]]) -> None:
    """验证条件数据"""
    depends_on = cond.get('depends_on')
    required_val = cond.get('required_value')
    target_field = cond.get('field')
    message = cond.get('message', f'{target_field}为必填')

    if depends_on and data.get(depends_on) == required_val:
        value = data.get(target_field)
        if value is None or (isinstance(value, str) and not value.strip()):
            _add_error(errors, target_field, message)


def _add_error(errors: Dict[str, List[str]], field: str, message: str) -> None:
    """添加错误信息"""
    if field not in errors:
        errors[field] = []
    errors[field].append(message)