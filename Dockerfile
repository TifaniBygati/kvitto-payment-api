FROM python:3.12-slim

WORKDIR /kvitto/app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY database ./database
COPY response_models ./response_models
COPY services ./services

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]