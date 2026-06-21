"""
payment/views.py — Payment Service
Cross-service imports removed:
  - REMOVED: from orders.models import Cart, CartItems
  - REMOVED: from accounts.models import Address
  - REPLACED: craft_common RPC clients for any cross-service data needs.

Cart/order context is passed in the request payload or looked up via
the order-service internal API. Address data is not used directly here.
"""
import stripe
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from craft_common.api_clients import order_client  # internal HTTP client
from .models import PaymentHistory, StripeWebhookEvent
from .serializers import PaymentHistorySerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


# ─── Checkout Session ────────────────────────────────────────────────────────

class CreateCheckoutSessionView(APIView):
    """
    Creates a Stripe Checkout Session.

    The client supplies `order_id`; this view fetches order details
    from the order-service via the internal HTTP client — it does NOT
    query Cart or CartItems from a local DB.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response(
                {"detail": "order_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch order details from order-service (no direct DB access)
        order_response = order_client.get(f"/internal/orders/{order_id}/")
        if order_response.status_code != 200:
            return Response(
                {"detail": "Order not found or order-service unavailable."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        order = order_response.json()

        # Validate ownership
        if order["user_id"] != request.user.id:
            return Response(
                {"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN
            )

        # Build Stripe line items from the order payload (no Cart model needed)
        line_items = [
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": item["product_name"]},
                    "unit_amount": int(float(item["unit_price"]) * 100),
                },
                "quantity": item["quantity"],
            }
            for item in order.get("items", [])
        ]

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            metadata={"order_id": str(order_id), "user_id": str(request.user.id)},
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
            idempotency_key=f"checkout-{order_id}",  # guard against double-charge
        )

        return Response({"checkout_url": session.url}, status=status.HTTP_201_CREATED)


# ─── Stripe Webhook ──────────────────────────────────────────────────────────

class StripeWebhookView(APIView):
    """
    Receives and processes Stripe webhook events.
    No cross-service model imports — events are published to the event bus.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload   = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        stripe_event_id = event["id"]

        # Idempotency guard — skip if already processed
        if StripeWebhookEvent.objects.filter(stripe_event_id=stripe_event_id).exists():
            return Response({"detail": "Already processed."}, status=status.HTTP_200_OK)

        StripeWebhookEvent.objects.create(
            stripe_event_id=stripe_event_id,
            event_type=event["type"],
            payload=event,
        )

        # Dispatch to handler
        handler = _WEBHOOK_HANDLERS.get(event["type"])
        if handler:
            handler(event["data"]["object"])

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)


# ─── Webhook Handlers ────────────────────────────────────────────────────────

def _handle_checkout_session_completed(session):
    """payment.succeeded → publish event; order-service will mark order as PAID."""
    from craft_common.events.publisher import EventPublisher
    from craft_common.events.schemas import PaymentSucceededEvent

    order_id = session["metadata"].get("order_id")
    user_id  = session["metadata"].get("user_id")
    amount   = session.get("amount_total", 0) / 100

    PaymentHistory.objects.create(
        user_id=int(user_id),
        order_id=int(order_id),
        stripe_session_id=session["id"],
        amount=amount,
        status="SUCCEEDED",
    )

    publisher = EventPublisher()
    publisher.publish(
        PaymentSucceededEvent(
            order_id=int(order_id),
            user_id=int(user_id),
            amount=amount,
            stripe_session_id=session["id"],
        )
    )


def _handle_payment_intent_payment_failed(payment_intent):
    """payment.failed → publish event; order-service will cancel the order."""
    from craft_common.events.publisher import EventPublisher
    from craft_common.events.schemas import PaymentFailedEvent

    order_id = payment_intent["metadata"].get("order_id")
    user_id  = payment_intent["metadata"].get("user_id")

    if order_id:
        publisher = EventPublisher()
        publisher.publish(
            PaymentFailedEvent(
                order_id=int(order_id),
                user_id=int(user_id) if user_id else None,
                reason=payment_intent.get("last_payment_error", {}).get("message", ""),
            )
        )


_WEBHOOK_HANDLERS = {
    "checkout.session.completed":       _handle_checkout_session_completed,
    "payment_intent.payment_failed":    _handle_payment_intent_payment_failed,
}


# ─── Payment History ─────────────────────────────────────────────────────────

class PaymentHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = PaymentHistory.objects.filter(
            user_id=request.user.id
        ).order_by("-date")
        serializer = PaymentHistorySerializer(payments, many=True)
        return Response(serializer.data)

# ─── Withdrawal Requests ─────────────────────────────────────────────────────

from rest_framework import viewsets
from .models import WithdrawalRequest
from .serializers import WithdrawalRequestSerializer

class WithdrawalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WithdrawalRequest.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        withdrawal = serializer.save(user_id=self.request.user.id)
        
        # Trigger Approval Request synchronously in admin-service
        import requests
        try:
            requests.post(
                "http://admin-service:8000/api/workflows/approvals/",
                json={
                    "request_type": "withdrawal_approval",
                    "related_object_type": "withdrawal",
                    "related_object_id": str(withdrawal.id),
                    "assigned_department": "Finance",
                    "status": "pending"
                },
                headers={"Authorization": self.request.headers.get("Authorization", "")},
                timeout=3
            )
        except requests.RequestException as e:
            import logging
            logging.error(f"Failed to trigger withdrawal approval: {e}")
