from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditLogViewSet, FraudAlertViewSet

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='audit-log')
router.register(r'fraud-alerts', FraudAlertViewSet, basename='fraud-alert')

urlpatterns = [
    path('', include(router.urls)),
]
