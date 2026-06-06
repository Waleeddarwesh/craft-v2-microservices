# Internal API Contracts

This document defines the synchronous HTTP APIs exposed by microservices for internal use only (not exposed via the Gateway).

## Catalog Service (`catalog-service:8002`)

### `GET /internal/products/bulk-lookup/`
- **Purpose**: Fetch product details (names, prices) for a list of product IDs.
- **Request Body**:
  ```json
  {
    "product_ids": [1, 2, 3]
  }
  ```
- **Response**:
  ```json
  [
    {"id": 1, "name": "Handmade Vase", "price": "45.00"},
    {"id": 2, "name": "Wooden Chair", "price": "120.00"}
  ]
  ```

## Payment Service (`payment-service:8004`)

### `POST /internal/payments/initiate/`
- **Purpose**: Initiate a payment intent and return a Stripe client secret.
- **Request Body**:
  ```json
  {
    "order_id": "123e4567-e89b-12d3-a456-426614174000",
    "amount": "165.00",
    "currency": "usd"
  }
  ```
- **Response**:
  ```json
  {
    "payment_intent_id": "pi_12345",
    "client_secret": "pi_12345_secret_67890"
  }
  ```

## Auth Service (`auth-service:8001`)

### `POST /internal/auth/validate-token/`
- **Purpose**: Exchange a token for user information (used by services that can't do local RS256 validation).
- **Request**: Bearer Token in `Authorization` header.
- **Response**:
  ```json
  {
    "user_id": 42,
    "email": "user@example.com",
    "is_active": true
  }
  ```
