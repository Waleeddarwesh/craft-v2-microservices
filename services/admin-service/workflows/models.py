from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class DepartmentTask(models.Model):
    TASK_STATUS = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("waiting_approval", "Waiting Approval"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=100)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_tasks")

    related_object_type = models.CharField(max_length=100)
    related_object_id = models.CharField(max_length=100)

    status = models.CharField(max_length=50, choices=TASK_STATUS, default="open")
    priority = models.CharField(max_length=50, choices=PRIORITY, default="medium")

    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="created_tasks", null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['department', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"[{self.department}] {self.title} - {self.status}"


class ApprovalRequest(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    request_type = models.CharField(max_length=100)
    related_object_type = models.CharField(max_length=100)
    related_object_id = models.CharField(max_length=100)

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="approval_requests", on_delete=models.SET_NULL, null=True)
    assigned_department = models.CharField(max_length=100)

    status = models.CharField(max_length=50, choices=STATUS, default="pending")

    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reviewed_approvals", on_delete=models.SET_NULL, null=True, blank=True)
    review_comment = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assigned_department', 'status']),
        ]

    def __str__(self):
        return f"Approval {self.request_type} - {self.status}"
