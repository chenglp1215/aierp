from typing import Any, Dict, List, Optional
from validators.base_validator import (
    BaseValidator,
    PhoneValidator,
    RequiredFieldsValidator,
    ListLengthValidator,
    NumericRangeValidator,
    DateRangeValidator,
    ConditionalRequiredValidator,
)
from datetime import datetime


class SalesOrderItemValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_required_fields()
        self._validate_numeric_fields()
        self._validate_subtotal()

    def _validate_required_fields(self) -> None:
        RequiredFieldsValidator.validate_required(
            self._data,
            ['product_id', 'product_name', 'quantity', 'unit_price', 'subtotal'],
            self
        )

    def _validate_numeric_fields(self) -> None:
        quantity = self._data.get('quantity')
        NumericRangeValidator.validate_in_range(
            quantity,
            'quantity',
            min_value=1,
            validator=self
        )

        unit_price = self._data.get('unit_price')
        NumericRangeValidator.validate_in_range(
            unit_price,
            'unit_price',
            min_value=0,
            validator=self
        )

    def _validate_subtotal(self) -> None:
        quantity = self._data.get('quantity', 0)
        unit_price = self._data.get('unit_price', 0)
        subtotal = self._data.get('subtotal', 0)
        expected_subtotal = quantity * unit_price
        if abs(subtotal - expected_subtotal) > 0.01:
            self.add_error('subtotal', f'小计金额不正确，应为{quantity} x {unit_price} = {expected_subtotal}')


class SalesOrderCreateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_required_fields()
        self._validate_contact_info()
        self._validate_delivery_info()
        self._validate_items()
        self._validate_financial_info()
        self._validate_date_range()

    def _validate_required_fields(self) -> None:
        RequiredFieldsValidator.validate_required(
            self._data,
            ['customer_id', 'customer_name', 'delivery_type', 'pickup_type'],
            self
        )

    def _validate_contact_info(self) -> None:
        phone = self._data.get('contact_phone')
        if phone is not None:
            PhoneValidator.validate(phone, 'contact_phone', self)

    def _validate_delivery_info(self) -> None:
        delivery_type = self._data.get('delivery_type')
        warehouse_id = self._data.get('warehouse_id')

        ConditionalRequiredValidator.validate([
            {
                'depends_on': 'delivery_type',
                'required_value': 'inventory',
                'field': 'warehouse_id',
                'message': '选择库存发货时必须选择发货仓库'
            }
        ], self._data, self)

        if delivery_type == 'direct':
            self.clear_error('warehouse_id')

        pickup_type = self._data.get('pickup_type')
        express_type = self._data.get('express_type')
        express_no = self._data.get('express_no')

        if pickup_type == 'express':
            if not express_type:
                self.add_error('express_type', '选择快递时必须选择快递公司')
            if not express_no:
                self.add_error('express_no', '选择快递时必须填写快递单号')

    def _validate_items(self) -> None:
        items = self._data.get('items', [])
        ListLengthValidator.validate_min_length(
            items,
            1,
            'items',
            self,
            '订单明细至少需要1项'
        )
        for i, item in enumerate(items):
            item_validator = SalesOrderItemValidator(item)
            if not item_validator.is_valid():
                for field, errors in item_validator.errors.items():
                    for error in errors:
                        self.add_error(f'items[{i}].{field}', error)

    def _validate_financial_info(self) -> None:
        express_fee = self._data.get('express_fee')
        if express_fee is not None:
            NumericRangeValidator.validate_in_range(
                express_fee,
                'express_fee',
                min_value=0,
                validator=self
            )

        discount_ratio = self._data.get('discount_ratio')
        if discount_ratio is not None:
            NumericRangeValidator.validate_in_range(
                discount_ratio,
                'discount_ratio',
                min_value=0,
                max_value=100,
                validator=self
            )

    def _validate_date_range(self) -> None:
        order_date = self._data.get('order_date')
        expected_delivery_date = self._data.get('expected_delivery_date')

        if isinstance(order_date, str):
            order_date = self._parse_date(order_date)
        if isinstance(expected_delivery_date, str):
            expected_delivery_date = self._parse_date(expected_delivery_date)

        DateRangeValidator.validate_date_range(
            order_date,
            expected_delivery_date,
            'order_date',
            'expected_delivery_date',
            self
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            return None


class SalesOrderUpdateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_contact_info()
        self._validate_delivery_info()
        self._validate_financial_info()
        self._validate_status_transition()

    def _validate_contact_info(self) -> None:
        phone = self._data.get('contact_phone')
        if phone is not None:
            PhoneValidator.validate(phone, 'contact_phone', self)

    def _validate_delivery_info(self) -> None:
        delivery_type = self._data.get('delivery_type')
        warehouse_id = self._data.get('warehouse_id')

        if delivery_type == 'inventory' and not warehouse_id:
            self.add_error('warehouse_id', '选择库存发货时必须选择发货仓库')

        pickup_type = self._data.get('pickup_type')
        express_type = self._data.get('express_type')
        express_no = self._data.get('express_no')

        if pickup_type == 'express':
            if not express_type:
                self.add_error('express_type', '选择快递时必须选择快递公司')
            if not express_no:
                self.add_error('express_no', '选择快递时必须填写快递单号')

    def _validate_financial_info(self) -> None:
        express_fee = self._data.get('express_fee')
        if express_fee is not None:
            NumericRangeValidator.validate_in_range(
                express_fee,
                'express_fee',
                min_value=0,
                validator=self
            )

        discount_ratio = self._data.get('discount_ratio')
        if discount_ratio is not None:
            NumericRangeValidator.validate_in_range(
                discount_ratio,
                'discount_ratio',
                min_value=0,
                max_value=100,
                validator=self
            )

    def _validate_status_transition(self) -> None:
        status = self._data.get('status')
        if status:
            valid_transitions = {
                'draft': ['pending', 'cancelled'],
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['completed', 'cancelled'],
            }
            # Note: In real scenario, you would check current status from database
            # This is just a template for the validation logic


class ProcurementOrderItemValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_required_fields()
        self._validate_numeric_fields()
        self._validate_subtotal()

    def _validate_required_fields(self) -> None:
        RequiredFieldsValidator.validate_required(
            self._data,
            ['product_id', 'product_name', 'quantity', 'unit_price', 'subtotal'],
            self
        )

    def _validate_numeric_fields(self) -> None:
        quantity = self._data.get('quantity')
        NumericRangeValidator.validate_in_range(
            quantity,
            'quantity',
            min_value=0.01,
            validator=self
        )

        unit_price = self._data.get('unit_price')
        NumericRangeValidator.validate_in_range(
            unit_price,
            'unit_price',
            min_value=0,
            validator=self
        )

    def _validate_subtotal(self) -> None:
        quantity = self._data.get('quantity', 0)
        unit_price = self._data.get('unit_price', 0)
        subtotal = self._data.get('subtotal', 0)
        expected_subtotal = quantity * unit_price
        if abs(subtotal - expected_subtotal) > 0.01:
            self.add_error('subtotal', f'小计金额不正确，应为{quantity} x {unit_price} = {expected_subtotal}')


class ProcurementOrderCreateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_required_fields()
        self._validate_contact_info()
        self._validate_items()

    def _validate_required_fields(self) -> None:
        RequiredFieldsValidator.validate_required(
            self._data,
            ['supplier_id', 'supplier_name'],
            self
        )

    def _validate_contact_info(self) -> None:
        phone = self._data.get('contact_phone')
        if phone is not None:
            PhoneValidator.validate(phone, 'contact_phone', self)

    def _validate_items(self) -> None:
        items = self._data.get('items', [])
        ListLengthValidator.validate_min_length(
            items,
            1,
            'items',
            self,
            '采购明细至少需要1项'
        )
        for i, item in enumerate(items):
            item_validator = ProcurementOrderItemValidator(item)
            if not item_validator.is_valid():
                for field, errors in item_validator.errors.items():
                    for error in errors:
                        self.add_error(f'items[{i}].{field}', error)


class ProcurementOrderUpdateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_contact_info()

    def _validate_contact_info(self) -> None:
        phone = self._data.get('contact_phone')
        if phone is not None:
            PhoneValidator.validate(phone, 'contact_phone', self)
