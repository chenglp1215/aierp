from typing import Any, Dict
from validators.base_validator import (
    BaseValidator,
    RequiredFieldsValidator,
    NumericRangeValidator,
)


class ProductCreateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_required_fields()
        self._validate_product_code()

    def _validate_required_fields(self) -> None:
        RequiredFieldsValidator.validate_required(
            self._data,
            ['product_code', 'name'],
            self
        )

    def _validate_product_code(self) -> None:
        product_code = self._data.get('product_code')
        if product_code:
            import re
            if not re.match(r'^[A-Z0-9\-_]+$', product_code.upper()):
                self.add_error('product_code', '商品编号只能包含字母、数字、横线和下划线')


class ProductUpdateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        product_code = self._data.get('product_code')
        if product_code is not None:
            import re
            if not re.match(r'^[A-Z0-9\-_]+$', product_code.upper()):
                self.add_error('product_code', '商品编号只能包含字母、数字、横线和下划线')


class ProductSpecCreateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        self._validate_required_fields()
        self._validate_price()

    def _validate_required_fields(self) -> None:
        RequiredFieldsValidator.validate_required(
            self._data,
            ['spec_code', 'price'],
            self
        )

    def _validate_price(self) -> None:
        price = self._data.get('price')
        NumericRangeValidator.validate_in_range(
            price,
            'price',
            min_value=0,
            validator=self
        )


class ProductSpecUpdateValidator(BaseValidator):
    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    def validate(self) -> None:
        price = self._data.get('price')
        if price is not None:
            NumericRangeValidator.validate_in_range(
                price,
                'price',
                min_value=0,
                validator=self
            )
