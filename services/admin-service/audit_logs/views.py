from rest_framework import viewsets, permissions
from .models import AuditLog, FraudAlert
from .serializers import AuditLogSerializer, FraudAlertSerializer

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'action', 'entity_type', 'entity_id']
    search_fields = ['entity_type', 'entity_id', 'action']
    ordering_fields = ['timestamp']

class FraudAlertViewSet(viewsets.ModelViewSet):
    queryset = FraudAlert.objects.all()
    serializer_class = FraudAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'user', 'resolved_by']
    search_fields = ['reason', 'notes']
    ordering_fields = ['created_at', 'risk_score']
