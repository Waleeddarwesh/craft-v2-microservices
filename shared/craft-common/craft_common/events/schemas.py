from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

class BaseEvent(BaseModel):
    """Base class for all domain events."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    
    model_config = ConfigDict(from_attributes=True)

class UserCreatedEvent(BaseEvent):
    event_type: str = "user.created"
    user_id: int
    email: str
    roles: list[str]

class UserUpdatedEvent(BaseEvent):
    event_type: str = "user.updated"
    user_id: int
    data: Dict[str, Any]

class UserDeletedEvent(BaseEvent):
    event_type: str = "user.deleted"
    user_id: int

class UserRoleChangedEvent(BaseEvent):
    event_type: str = "user.role_changed"
    user_id: int
    old_roles: list[str]
    new_roles: list[str]

class ProductCreatedEvent(BaseEvent):
    event_type: str = "product.created"
    product_id: int
    supplier_id: int
    name: str
    price: float

class ProductUpdatedEvent(BaseEvent):
    event_type: str = "product.updated"
    product_id: int
    data: Dict[str, Any]

class ProductStockChangedEvent(BaseEvent):
    event_type: str = "product.stock_changed"
    product_id: int
    new_stock: int

class ProductViewedEvent(BaseEvent):
    event_type: str = "product.viewed"
    product_id: int
    user_id: int

class CourseCreatedEvent(BaseEvent):
    event_type: str = "course.created"
    course_id: int
    supplier_id: int
    title: str

class EnrollmentCreatedEvent(BaseEvent):
    event_type: str = "enrollment.created"
    enrollment_id: int
    course_id: int
    user_id: int

class OrderCreatedEvent(BaseEvent):
    event_type: str = "order.created"
    order_id: int
    user_id: int
    items: list[Dict[str, Any]]

class OrderPlacedEvent(BaseEvent):
    event_type: str = "order.placed"
    order_id: int
    user_id: int
    total_amount: float

class OrderPaidEvent(BaseEvent):
    event_type: str = "order.paid"
    order_id: int
    transaction_id: str

class OrderShippedEvent(BaseEvent):
    event_type: str = "order.shipped"
    order_id: int
    shipment_id: int
    tracking: str

class OrderDeliveredEvent(BaseEvent):
    event_type: str = "order.delivered"
    order_id: int
    delivered_at: datetime

class OrderCancelledEvent(BaseEvent):
    event_type: str = "order.cancelled"
    order_id: int
    reason: str

class PaymentSucceededEvent(BaseEvent):
    event_type: str = "payment.succeeded"
    order_id: int
    transaction_id: str

class PaymentFailedEvent(BaseEvent):
    event_type: str = "payment.failed"
    order_id: int
    reason: str

class PaymentRefundedEvent(BaseEvent):
    event_type: str = "payment.refunded"
    order_id: int
    refund_amount: float

class ReturnRequestedEvent(BaseEvent):
    event_type: str = "return.requested"
    return_id: int
    order_id: int
    user_id: int

class ReturnApprovedEvent(BaseEvent):
    event_type: str = "return.approved"
    return_id: int
    refund_amount: float

class ReturnRejectedEvent(BaseEvent):
    event_type: str = "return.rejected"
    return_id: int
    reason: str

class WithdrawalApprovedEvent(BaseEvent):
    event_type: str = "withdrawal.approved"
    withdrawal_id: int
    user_id: int
    amount: float

class WithdrawalCompletedEvent(BaseEvent):
    event_type: str = "withdrawal.completed"
    withdrawal_id: int

class ReviewApprovedEvent(BaseEvent):
    event_type: str = "review.approved"
    review_id: int
    product_id: Optional[int] = None
    course_id: Optional[int] = None
    rating: int

class DisputeOpenedEvent(BaseEvent):
    event_type: str = "dispute.opened"
    dispute_id: int
    order_id: int
    user_id: int

class DisputeResolvedEvent(BaseEvent):
    event_type: str = "dispute.resolved"
    dispute_id: int
    resolution: str

