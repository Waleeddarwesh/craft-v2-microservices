# Developer Runbook

## Local Development

Start the infrastructure and gateway:
```bash
docker compose up -d
```

Services are accessible via the API Gateway at `http://localhost`.
Traefik dashboard is accessible at `http://localhost:8080`.
RabbitMQ management is accessible at `http://localhost:15672`.

## Shared Library

The `craft-common` library must be installed in editable mode for local development:
```bash
pip install -e ./shared/craft-common
```
