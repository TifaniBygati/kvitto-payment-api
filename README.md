# Kvitto Payment API

Тестовое задание: REST API для создания и обработки платежей онлайн-школы.

## Стек

- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy
- SQLite
- pytest
- httpx

## Возможности

API поддерживает:

- получение списка тарифов;
- создание платежей;
- промокод `KVITTO10` со скидкой 10%;
- оплату картой, СБП и рассрочкой;
- рассрочку на 3, 6 или 12 месяцев;
- `Idempotency-Key` для защиты от повторного создания платежа;
- получение платежа по ID;
- обработку банковских webhook;
- контроль допустимых переходов статуса платежа.

Все денежные значения хранятся и передаются в копейках.

## Установка

Клонировать репозиторий:

```bash
git clone <repository-url>
cd Kvitto
```

Создать виртуальное окружение:

```bash
python -m venv .venv
```

Активировать виртуальное окружение.

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

## Запуск

### Локальный запуск

Создать виртуальное окружение:

```bash
python -m venv .venv
```

#### Windows PowerShell

Если PowerShell запрещает запуск скрипта активации, разрешить его только для текущей сессии:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Активировать виртуальное окружение:

```powershell
.\.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
source .venv/bin/activate
```

Установить зависимости:

```bash
python -m pip install -r requirements.txt
```

Запустить приложение:

```bash
python -m uvicorn main:app --reload
```

После запуска API будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### Запуск через Docker

Проект также можно запустить через Docker Compose.

Сборка и запуск:

```bash
docker compose up --build
```

После запуска API будет доступен по адресу:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Остановка контейнера:

```bash
docker compose down
```

SQLite-база данных и необходимые таблицы создаются автоматически при запуске приложения.

При первом запуске также создаются тарифы:

| Тариф | Цена |
|---|---:|
| basic | 990000 коп. |
| standard | 1990000 коп. |
| premium | 2990000 коп. |

## Запуск тестов

```bash
pytest -v
```

Тесты проверяют:

- получение списка тарифов;
- создание платежа;
- применение промокода без учёта регистра;
- расчёт рассрочки на 3 месяца;
- расчёт рассрочки на 6 месяцев;
- расчёт рассрочки на 12 месяцев;
- совпадение суммы элементов `schedule` с итоговым `amount`;
- работу `Idempotency-Key`;
- возврат существующего платежа при повторном запросе;
- запрещённые переходы статусов;
- сохранение предыдущего статуса после запрещённого перехода;
- получение `404` для отсутствующего платежа.

## API

### GET /tariffs

Возвращает список доступных тарифов.

Пример запроса:

```bash
curl http://127.0.0.1:8000/tariffs
```

Пример ответа:

```json
[
  {
    "id": 1,
    "title": "basic",
    "price": 990000
  },
  {
    "id": 2,
    "title": "standard",
    "price": 1990000
  },
  {
    "id": 3,
    "title": "premium",
    "price": 2990000
  }
]
```

---

### POST /payments

Создаёт новый платёж.

Поддерживаемые способы оплаты:

- `card`
- `sbp`
- `installment`

Пример оплаты картой:

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "tariff_id": 1,
    "email": "user@example.com",
    "method": "card"
  }'
```

При успешном создании нового платежа API возвращает:

```text
201 Created
```

Пример ответа:

```json
{
  "id": 1,
  "status": "pending",
  "tariff_id": 1,
  "amount": 990000,
  "discount": 0,
  "method": "card",
  "installment_months": null,
  "schedule": null,
  "email": "user@example.com",
  "created_at": "2026-10-13T10:00:00+00:00"
}
```

---

### Платёж с промокодом

Промокод:

```text
KVITTO10
```

даёт скидку 10%.

Промокод регистронезависимый, поэтому `kvitto10`, `Kvitto10` и `KVITTO10` обрабатываются одинаково.

Пример:

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "tariff_id": 2,
    "email": "user@example.com",
    "method": "card",
    "promo_code": "kvitto10"
  }'
```

Для тарифа `standard`:

```text
Исходная цена: 1990000 коп.
Скидка:         199000 коп.
Итоговая сумма: 1791000 коп.
```

Неизвестный промокод приводит к ответу:

```text
422 Unprocessable Entity
```

---

### Платёж в рассрочку

Для метода:

```text
installment
```

необходимо передать `installment_months`.

Поддерживаемые значения:

```text
3
6
12
```

Пример:

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -d '{
    "tariff_id": 2,
    "email": "user@example.com",
    "method": "installment",
    "installment_months": 3
  }'
```

Для суммы `1990000` копеек график платежей будет:

```json
[
  663334,
  663333,
  663333
]
```

Остаточные копейки распределяются по первым платежам так, чтобы:

```text
sum(schedule) == amount
```

---

### Idempotency-Key

Для защиты от повторного создания одного и того же платежа можно передать HTTP-заголовок:

```text
Idempotency-Key
```

Пример:

```bash
curl -X POST http://127.0.0.1:8000/payments \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: payment-example-123" \
  -d '{
    "tariff_id": 1,
    "email": "user@example.com",
    "method": "card"
  }'
```

При первом запросе создаётся новый платёж:

```text
201 Created
```

Если повторить запрос с тем же `Idempotency-Key`, новый платёж создан не будет.

API вернёт уже существующий платёж:

```text
200 OK
```

---

### GET /payments/{payment_id}

Возвращает платёж по его ID.

Пример:

```bash
curl http://127.0.0.1:8000/payments/1
```

Если платёж существует:

```text
200 OK
```

Если платёж не найден:

```text
404 Not Found
```

Пример ответа:

```json
{
  "detail": "Payment not found"
}
```

---

### POST /webhooks/bank

Endpoint для обработки изменения статуса платежа со стороны банка.

Пример:

```bash
curl -X POST http://127.0.0.1:8000/webhooks/bank \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 1,
    "status": "succeeded"
  }'
```

Допустимые переходы статусов:

```text
pending -> succeeded
pending -> failed
succeeded -> refunded
```

При успешном переходе:

```text
200 OK
```

Ответ:

```json
{
  "result": "ok"
}
```

Все остальные переходы запрещены.

Например:

```text
pending -> refunded
```

вернёт:

```text
409 Conflict
```

Ответ:

```json
{
  "error": "invalid_transition"
}
```

При запрещённом переходе текущий статус платежа не изменяется.

Если указанный `payment_id` не существует:

```text
404 Not Found
```

## Использование AI

При выполнении тестового задания использовался ChatGPT как технический наставник.

AI использовался для:

- разбора незнакомых требований;
- обсуждения бизнес-логики;
- объяснения новых механизмов FastAPI и Pydantic;
- ревью написанного кода;
- разбора ошибок и вариантов реализации.

Подробное описание работы с AI находится в файле:

```text
AI_LOG.md
```