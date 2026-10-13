from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

PROMO_CODE = "KVITTO10"

class TariffResponse(BaseModel):
    id: int
    title: str
    price: int

    model_config = ConfigDict(from_attributes=True)

class PaymentCreate(BaseModel):
    tariff_id: int
    email: str
    method: str
    installment_months: int | None = None
    promo_code: str | None = None

    @model_validator(mode='after')
    def validate_installment(self):

        allowed_months = [3, 6, 12]

        if self.method == 'installment':
            if self.installment_months is None:
                raise ValueError('Для installment обязательно installment_months')

            if self.installment_months not in allowed_months:
                raise ValueError(f'Рассрочка может быть только {allowed_months}')

        return self

    @model_validator(mode='after')
    def validate_method(self):

        methods = ['sbp', 'card', 'installment']

        if self.method not in methods:
            raise ValueError(f'method={self.method}, может быть={methods}')

        return self

    @model_validator(mode='after')
    def normalize_promo_code(self):
        if self.promo_code is not None and self.promo_code != PROMO_CODE:
            raise ValueError('Неизвестный промокод')
        return self

    @model_validator(mode='before')
    def validate_promo_code(cls, data):

        if data.get('promo_code') is not None:
            data['promo_code'] = data['promo_code'].upper()
        return data

class Payment(BaseModel):
    id: int
    status: str
    tariff_id: int
    amount: int
    discount: int
    method: str
    installment_months: int | None = None
    schedule: list[int] | None = None
    email: str
    created_at: datetime
    idempotency_key: str | None = None

    @model_validator(mode='after')
    def validate_installment_months(self):
        allowed_months = [3, 6, 12]

        if self.method == 'installment':

            if self.installment_months is None:
                raise ValueError('Для installment обязательно installment_months')

            if self.installment_months not in allowed_months:
                raise ValueError(f'Рассрочка может быть только {allowed_months}')

        return self

    @model_validator(mode='after')
    def validate_method(self):

        methods = ['sbp', 'card', 'installment']

        if self.method not in methods:
            raise ValueError(f'method={self.method}, может быть={methods}')

        return self

class WebHook(BaseModel):
    payment_id: int
    status: str

class PaymentResponse(BaseModel):
    id: int
    status: str
    tariff_id: int
    amount: int
    discount: int
    method: str
    installment_months: int | None = None
    schedule: list[int] | None = None
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)