from fastapi.testclient import TestClient

from main import app

from uuid import uuid4

client = TestClient(app)


def test_get_tariff():
    response = client.get("/tariffs")

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)

def test_post_payment_HTTP_201():
    payload = {
      "tariff_id": 1,
      "email": "mail.ru",
      "method": "card"
    }

    response = client.post("/payments", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert isinstance(body, dict)

    assert body.get("amount") == 990000
    assert body.get("discount") == 0
    assert body.get("status") == "pending"

def test_post_payment_HTTP_201_PROMO():
    payload = {
      "tariff_id": 2,
      "email": "mail.ru",
      "method": "card",
      "promo_code": "kvitto10"
    }

    response = client.post("/payments", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert isinstance(body, dict)

    assert body.get("discount") == 199000
    assert body.get("amount") == 1791000

def test_post_payment_HTTP_201_INSTALLMENT_3M():
    payload = {
    "tariff_id": 2,
    "email": "mail.ru",
    "method": "installment",
    "installment_months": 3
    }

    response = client.post("/payments", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert isinstance(body, dict)

    assert isinstance(body.get("schedule"), list)

    assert len(body.get("schedule")) == 3
    assert sum(body.get("schedule")) == body.get("amount")

def test_post_payment_HTTP_201_INSTALLMENT_6M():
    payload = {
    "tariff_id": 2,
    "email": "mail.ru",
    "method": "installment",
    "installment_months": 6
    }

    response = client.post("/payments", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert isinstance(body, dict)

    assert isinstance(body.get("schedule"), list)

    assert len(body.get("schedule")) == 6
    assert sum(body.get("schedule")) == body.get("amount")

def test_post_payment_HTTP_201_INSTALLMENT_12M():
    payload = {
    "tariff_id": 2,
    "email": "mail.ru",
    "method": "installment",
    "installment_months": 12
    }

    response = client.post("/payments", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert isinstance(body, dict)

    assert isinstance(body.get("schedule"), list)

    assert len(body.get("schedule")) == 12
    assert sum(body.get("schedule")) == body.get("amount")

def test_payment_idempotency():
    payload = {
      "tariff_id": 1,
      "email": "mail.ru",
      "method": "card"
    }
    header = {
        'Idempotency-Key': str(uuid4())
    }

    response = client.post("/payments", json=payload, headers=header)

    assert response.status_code == 201

    body1 = response.json()

    assert isinstance(body1, dict)

    response = client.post("/payments", json=payload, headers=header)

    assert response.status_code == 200

    body2 = response.json()

    assert isinstance(body2, dict)

    assert body1 == body2

def test_webhook_invalid_transition():
    payload = {
      "tariff_id": 1,
      "email": "mail.ru",
      "method": "card"
    }

    response = client.post("/payments", json=payload)

    assert response.status_code == 201

    payment_id = response.json()['id']

    webhook_payload = {
        'payment_id': payment_id,
        'status': "refunded",
    }

    response = client.post("/webhooks/bank", json=webhook_payload)

    assert response.status_code == 409

    body = response.json()

    assert isinstance(body, dict)

    assert body == {'error': 'invalid_transition'}

    response = client.get(f"/payments/{payment_id}")

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, dict)

    assert body.get("status") == "pending"

def test_unknown_payment_404():

    payload = {
      "tariff_id": 1,
      "email": "mail.ru",
      "method": "card"
    }

    response = client.post("/payments", json=payload)

    assert response.status_code == 201

    payment_id = response.json()['id']

    new_unknown_payment_id = payment_id + 1

    response = client.get(f"/payments/{new_unknown_payment_id}")

    assert response.status_code == 404

    body = response.json()

    assert isinstance(body, dict)

    assert body == {"detail": "Payment not found"}
