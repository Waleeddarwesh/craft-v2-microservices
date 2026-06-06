# 🧶 Craft Application — v2.0 (Microservices Architecture)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal)
![Docker](https://img.shields.io/badge/Docker-Microservices-blue)
![Traefik](https://img.shields.io/badge/Traefik-API%20Gateway-cyan)

## 📌 Overview

**Craft v2.0** represents a complete architectural evolution of the Craft e-commerce and e-learning platform. Moving away from the monolithic architecture of v1.2, Craft is now a fully decoupled, scalable, and highly available system composed of independent microservices.

## 🏗️ Architecture: The Microservices Ecosystem

The platform has been broken down into independent domains, communicating via RESTful HTTP APIs and event-driven patterns.

### The Services

| Service | Technology | Domain | Port |
|---|---|---|---|
| **Auth Service** | Django | Identity, Users, RBAC, Profiles | `8001` |
| **Catalog Service** | Django | Products, Categories, Inventory | `8002` |
| **Order Service** | Django | Cart, Orders, Shipping, Returns | `8003` |
| **Payment Service** | Django | Stripe Integration, Wallets | `8004` |
| **Platform Service** | Django | Reviews, Support Tickets | `8005` |
| **Reporting Service**| Django | Analytics, Admin Dashboard | `8006` |
| **Realtime Service** | FastAPI | WebSockets, Notifications | `8007` |
| **ML Service** | FastAPI | Recommendation Engine | `8008` |

### Infrastructure

- **API Gateway (Traefik):** Unified entrypoint (`http://localhost`) that intelligently routes requests to the appropriate microservices based on path prefixes (`/api/auth/`, `/api/catalog/`, etc.).
- **Monitoring & Observability:** Prometheus and Grafana integration for metrics.
- **Shared Library (`craft_common`):** A centralized Python package containing shared API clients, authentication middleware, and logging configurations to ensure consistency across Django services.

---

## 🚀 Running the Microservices

The entire ecosystem is orchestrated via Docker Compose.

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```
Ensure you provide the necessary API keys (like `STRIPE_SECRET_KEY`).

### 2. Bootstrapping the Ecosystem

Run the root Docker Compose file to build and start all services, databases, and the API gateway.

```bash
docker-compose up --build -d
```

### 3. Accessing the Platform

All services are accessible through the Traefik API Gateway on port `80`.

- Auth: `http://localhost/api/auth/`
- Catalog: `http://localhost/api/catalog/`
- Orders: `http://localhost/api/orders/`
- Traefik Dashboard: `http://localhost:8080`

### 4. Running Migrations

Each Django service has its own isolated database. You can run migrations per service:

```bash
docker-compose exec auth-service python manage.py migrate
docker-compose exec catalog-service python manage.py migrate
```

---

## 🛠️ Development & Tooling

A central `craft_common` directory is mounted into every Django container, allowing seamless updates to shared HTTP client abstractions and utilities without rebuilding images. 

### Local Verification

To run global checks across all Django microservices natively:
```bash
bash verify_services.sh
```

---

## 📞 Contact

### Waleed Darwesh
Django Developer | Cloud DevOps Engineer
📧 Email: [Waleeddarwesh2002@gmail.com](mailto:Waleeddarwesh2002@gmail.com)
🔗 LinkedIn: [Waleed Darwesh](https://www.linkedin.com/in/waleeddarwesh1/)
