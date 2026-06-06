from django.urls import path
from .views import CreateCheckoutSessionView, StripeWebhookView, PaymentHistoryView

app_name = "payment"

urlpatterns = [
    path('checkout/', CreateCheckoutSessionView.as_view(), name='checkout'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('history/', PaymentHistoryView.as_view(), name='history'),
]