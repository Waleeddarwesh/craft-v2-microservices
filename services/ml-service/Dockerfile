FROM python:3.10-slim

WORKDIR /app

COPY services/ml-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/ml-service/ .

CMD ["opentelemetry-instrument", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]
