from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CreateCheckoutSessionView, StripeWebhookView, PaymentHistoryView, WithdrawalRequestViewSet

app_name = "payment"

router = DefaultRouter()
router.register(r'withdrawals', WithdrawalRequestViewSet, basename='withdrawals')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', CreateCheckoutSessionView.as_view(), name='checkout'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('history/', PaymentHistoryView.as_view(), name='history'),
]