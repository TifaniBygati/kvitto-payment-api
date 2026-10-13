from fastapi import FastAPI, Depends, HTTPException, Header, Response, status

from fastapi.responses import JSONResponse

from database.orm_database import (
    init_db,
    get_tariffs_sqlite,
    find_tariff_sqlite,
    save_payment_sqlite,
    Payment,
    find_payment_by_idempotency_key_sqlite,
    find_payment_by_id_sqlite,
    update_payment_status_sqlite

)

from services.payment_service import calculate_price, calculate_schedule

from response_models.scheme_response import TariffResponse, PaymentCreate, WebHook, PaymentResponse

init_db()

app = FastAPI()

@app.get(
    "/tariffs",
    response_model=list[TariffResponse],
    tags=["actions"]
)
def get_tariffs(tariffs: list = Depends(get_tariffs_sqlite)):
    return tariffs

@app.post(
    "/payments",
    tags=["actions"],
    status_code=201,
    response_model=PaymentResponse
)
def create_payment(
        payment: PaymentCreate,
        response: Response,
        idempotency_key: str | None = Header(
        default = None,
        alias = "Idempotency-Key",
)
):

    if idempotency_key is not None:
        existing_payment = find_payment_by_idempotency_key_sqlite(
            idempotency_key
        )
        if existing_payment is not None:
            response.status_code = status.HTTP_200_OK
            return existing_payment

    tariff = find_tariff_sqlite(payment.tariff_id)

    if tariff is None:
        raise HTTPException(
            status_code=404,
            detail="Tariff not found"
        )

    discount, amount = calculate_price(
        payment.promo_code,
        tariff.price
    )
    schedule = None
    if payment.method == 'installment':

        schedule = calculate_schedule(amount, payment.installment_months)

    payment_obj = Payment(
        tariff_id=payment.tariff_id,
        amount=amount,
        discount=discount,
        method=payment.method,
        installment_months=payment.installment_months,
        idempotency_key=idempotency_key,
        schedule=schedule,
        email=payment.email,
    )
    payment_obj = save_payment_sqlite(payment_obj)

    return payment_obj

@app.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse
)
def get_payment(
        payment_id: int,
):
    payment = find_payment_by_id_sqlite(payment_id)
    if payment is None:
        raise HTTPException(
            detail="Payment not found",
            status_code=404
        )

    return payment

@app.post('/webhooks/bank')
def webhook_bank(
  webhook: WebHook
):
    allowed_transitions = {
        "pending": {"succeeded", "failed"},
        "succeeded": {"refunded"},
    }

    payment = find_payment_by_id_sqlite(webhook.payment_id)

    if payment is None:
        raise HTTPException(
            detail="Payment not found",
            status_code=404
        )

    allowed_statuses = allowed_transitions.get(payment.status, set())

    if webhook.status not in allowed_statuses:
        return JSONResponse(
            status_code=409,
            content={"error": "invalid_transition"}
        )

    update_payment_status_sqlite(payment.id, webhook.status)


    return {
        'result': 'ok'
    }