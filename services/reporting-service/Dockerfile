FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY shared/craft-common /shared/craft-common

# Copy service requirements and install
COPY services/reporting-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/reporting-service/ .

# Command to run the application
RUN python manage.py collectstatic --noinput

CMD ["opentelemetry-instrument", "gunicorn", "reporting_service.wsgi:application", "--bind", "0.0.0.0:8007", "--workers", "3"]
