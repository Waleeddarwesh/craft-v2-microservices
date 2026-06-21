from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import DepartmentTask, ApprovalRequest
from .serializers import DepartmentTaskSerializer, ApprovalRequestSerializer, ApprovalReviewSerializer

class DepartmentTaskViewSet(viewsets.ModelViewSet):
    queryset = DepartmentTask.objects.all()
    serializer_class = DepartmentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['department', 'status', 'priority', 'assigned_to', 'created_by']
    search_fields = ['title', 'description', 'related_object_type', 'related_object_id']
    ordering_fields = ['created_at', 'due_at', 'priority']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        tasks = self.queryset.filter(assigned_to=request.user).exclude(status='completed')
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    queryset = ApprovalRequest.objects.all()
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'assigned_department', 'requested_by', 'reviewed_by', 'request_type']
    search_fields = ['related_object_type', 'related_object_id']
    ordering_fields = ['created_at', 'reviewed_at']

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'], serializer_class=ApprovalReviewSerializer)
    def review(self, request, pk=None):
        approval = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        comment = serializer.validated_data.get('comment', '')

        if approval.status != 'pending':
            return Response(
                {"detail": f"Cannot review a request that is already {approval.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        approval.status = f"{action}d" # 'approved' or 'rejected'
        approval.reviewed_by = request.user
        approval.reviewed_at = timezone.now()

        if action == 'reject':
            approval.rejection_reason = comment
        else:
            approval.review_comment = comment

        approval.save()

        # In a real app, this would trigger webhooks/celery tasks to process the approval action
        
        return Response(ApprovalRequestSerializer(approval).data)
