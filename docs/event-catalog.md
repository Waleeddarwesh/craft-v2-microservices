# Event Catalog

| Event Name | Publisher | Consumers | Description |
|---|---|---|---|
| `user.created` | Auth Service | All | A new user was registered |
| `user.updated` | Auth Service | All | User profile or roles updated |
| `user.deleted` | Auth Service | All | User account deleted |
| `user.role_changed` | Auth Service | All | User roles modified |
| `product.created` | Catalog Service | Platform | New product added |
| `product.updated` | Catalog Service | Platform | Product details updated |
| `product.stock_changed` | Catalog Service | Order | Product stock level changed |
| `product.viewed` | Catalog Service | ML | User viewed a product |
| `course.created` | Catalog Service | Platform | New course added |
| `enrollment.created` | Catalog Service | ML | User enrolled in a course |
| `order.created` | Order Service | Payment | New order placed |
| `order.placed` | Order Service | Real-Time, ML | Order confirmed |
| `order.paid` | Order Service | Real-Time | Order payment received |
| `order.shipped` | Order Service | Real-Time | Order shipped |
| `order.delivered` | Order Service | Real-Time, Platform | Order delivered to customer |
| `order.cancelled` | Order Service | Real-Time | Order cancelled |
| `payment.succeeded` | Payment Service | Order, Real-Time | Payment was successful |
| `payment.failed` | Payment Service | Order, Real-Time | Payment failed |
| `payment.refunded` | Payment Service | Order, Real-Time | Payment refunded |
| `return.requested` | Order Service | Real-Time | Return requested |
| `return.approved` | Order Service | Payment, Platform | Return approved |
| `return.rejected` | Order Service | Real-Time | Return rejected |
| `withdrawal.approved` | Payment Service | Real-Time | Withdrawal approved |
| `withdrawal.completed` | Payment Service | Real-Time | Withdrawal completed |
| `review.approved` | Platform Service | Catalog | Review approved and published |
| `dispute.opened` | Platform Service | Real-Time | Dispute opened |
| `dispute.resolved` | Platform Service | Real-Time | Dispute resolved |
