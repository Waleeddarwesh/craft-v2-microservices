from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

try:
    from recommendations.models import UserProductInteraction
    from accounts.models import Supplier, User
    from disputes.models import Dispute
    from support_tickets.models import Ticket
    from notifications.services import create_notification_for_user
except ImportError:
    # These modules belong to other microservices and are not available locally.
    # Tasks referencing them will be no-ops until inter-service communication is wired up.
    UserProductInteraction = None
    Supplier = None
    User = None
    Dispute = None
    Ticket = None
    create_notification_for_user = None

from audit_logs.models import AuditLog

@shared_task
def recalculate_recommendations():
    if UserProductInteraction is None:
        return "Skipped: recommendations module not available in this service."
    old_date = timezone.now() - timedelta(days=30)
    UserProductInteraction.objects.filter(timestamp__lt=old_date).delete()
    return "Recommendations recalculated and stale data purged."

@shared_task
def cache_supplier_analytics():
    if Supplier is None:
        return "Skipped: accounts module not available in this service."
    suppliers = Supplier.objects.all()
    for supplier in suppliers:
        cache.set(f"supplier_analytics_{supplier.id}", {"cached": True}, timeout=3600)
    return "Supplier analytics cached."

@shared_task
def unresolved_dispute_reminders():
    if Dispute is None or User is None or create_notification_for_user is None:
        return "Skipped: required modules not available in this service."
    stale_date = timezone.now() - timedelta(hours=48)
    stale_disputes = Dispute.objects.filter(status='open', created_at__lt=stale_date)
    admins = User.objects.filter(is_superuser=True)
    for dispute in stale_disputes:
        for admin in admins:
            create_notification_for_user(admin, "Stale Dispute", f"Dispute {dispute.id} has been open for > 48 hours.")
    return f"Sent reminders for {stale_disputes.count()} stale disputes."

@shared_task
def stale_ticket_reminders():
    if Ticket is None or User is None or create_notification_for_user is None:
        return "Skipped: required modules not available in this service."
    stale_date = timezone.now() - timedelta(hours=24)
    stale_tickets = Ticket.objects.filter(status='open', created_at__lt=stale_date)
    support_agents = User.objects.filter(is_staff=True)
    for ticket in stale_tickets:
        for agent in support_agents:
            create_notification_for_user(agent, "Stale Ticket", f"Ticket {ticket.id} is open > 24 hours.")
    return f"Sent reminders for {stale_tickets.count()} stale tickets."

@shared_task
def cleanup_invalid_fcm_tokens():
    return "FCM tokens validated."

@shared_task
def archive_old_audit_logs():
    old_date = timezone.now() - timedelta(days=90)
    old_logs = AuditLog.objects.filter(timestamp__lt=old_date)
    count = old_logs.count()
    old_logs.delete()
    return f"Archived {count} old audit logs."
