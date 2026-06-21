from rest_framework import serializers
from .models import DepartmentTask, ApprovalRequest
from django.contrib.auth import get_user_model

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class DepartmentTaskSerializer(serializers.ModelSerializer):
    assigned_to_details = UserBasicSerializer(source='assigned_to', read_only=True)
    created_by_details = UserBasicSerializer(source='created_by', read_only=True)

    class Meta:
        model = DepartmentTask
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'completed_at', 'created_by']


class ApprovalRequestSerializer(serializers.ModelSerializer):
    requested_by_details = UserBasicSerializer(source='requested_by', read_only=True)
    reviewed_by_details = UserBasicSerializer(source='reviewed_by', read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'reviewed_at', 'requested_by', 'reviewed_by', 'review_comment', 'rejection_reason']


class ApprovalReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    comment = serializers.CharField(required=False, allow_blank=True)
