from rest_framework import serializers
from .models import AuditLog, FraudAlert
from django.contrib.auth import get_user_model

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class AuditLogSerializer(serializers.ModelSerializer):
    user_details = UserBasicSerializer(source='user', read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'


class FraudAlertSerializer(serializers.ModelSerializer):
    user_details = UserBasicSerializer(source='user', read_only=True)
    resolved_by_details = UserBasicSerializer(source='resolved_by', read_only=True)

    class Meta:
        model = FraudAlert
        fields = '__all__'
