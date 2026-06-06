from django.urls import path
from . import internal_views

urlpatterns = [
    path('initiate/', internal_views.InitiatePayment.as_view(), name='internal-payment-initiate'),
    path('refund/', internal_views.RefundPayment.as_view(), name='internal-payment-refund'),
]
