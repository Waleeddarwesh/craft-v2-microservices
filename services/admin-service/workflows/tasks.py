from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import DepartmentTask, ApprovalRequest
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_sla_breaches():
    """
    Checks for tasks that are past their due_at date but not completed.
    Escalates priority to 'critical' and logs an alert.
    """
    now = timezone.now()
    breached_tasks = DepartmentTask.objects.filter(
        due_at__lt=now,
        status__in=['open', 'in_progress', 'waiting_approval']
    ).exclude(priority='critical')

    count = 0
    for task in breached_tasks:
        task.priority = 'critical'
        task.save(update_fields=['priority'])
        logger.warning(f"SLA Breach: Task #{task.id} '{task.title}' escalated to critical.")
        
        # Trigger an internal Notification to the department
        from notifications.models import Notification
        Notification.objects.create(
            department=task.department,
            message=f"[SLA Breach] Task #{task.id} '{task.title}' has exceeded its deadline and escalated to CRITICAL priority."
        )
        
        count += 1
        
    return f"Checked SLA breaches. Escalated {count} tasks."


@shared_task
def send_pending_approval_reminders():
    """
    Finds approvals that have been pending for > 24 hours
    and triggers a reminder notification.
    """
    threshold = timezone.now() - timedelta(hours=24)
    stale_approvals = ApprovalRequest.objects.filter(
        status='pending',
        created_at__lt=threshold
    )

    count = stale_approvals.count()
    if count > 0:
        logger.info(f"Found {count} pending approvals older than 24h. Reminders should be dispatched.")
        
        from notifications.models import Notification
        for approval in stale_approvals:
            Notification.objects.create(
                department=approval.assigned_department,
                message=f"[Reminder] Pending Approval #{approval.id} ({approval.request_type}) has been waiting for more than 24 hours."
            )
        
    return f"Processed {count} stale approvals."
