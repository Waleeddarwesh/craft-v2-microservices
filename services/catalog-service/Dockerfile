FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for psycopg and pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY shared/craft-common /shared/craft-common

# Copy service requirements and install
COPY services/catalog-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/catalog-service/ .

# Command to run the application
RUN python manage.py collectstatic --noinput

CMD ["opentelemetry-instrument", "gunicorn", "catalog_service.wsgi:application", "--bind", "0.0.0.0:8002", "--workers", "3"]
