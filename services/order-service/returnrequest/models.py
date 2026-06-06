import uuid
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

class ReturnRequestManager(models.Manager):
    pass

class ReturnRequest(models.Model):
    class ReturnStatus(models.TextChoices):
        NEW = 'new', _('New')
        ACCEPTED = 'accepted', _('Accepted')
        REJECTED = 'rejected', _('Rejected')
        CANCELLED = 'cancelled', _('Cancelled')

    class ReturnReason(models.TextChoices):
        DAMAGED = 'damaged', _('Item was damaged')
        WRONG_ITEM = 'wrong_item', _('Received wrong item')
        WRONG_SIZE = 'wrong_size', _('Wrong size or fit')
        NOT_AS_DESCRIBED = 'not_as_described', _('Not as described')
        CHANGED_MIND = 'changed_mind', _('Changed my mind')
        OTHER = 'other', _('Other')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.BigIntegerField()
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    product_id = models.BigIntegerField()
    quantity = models.PositiveIntegerField()
    supplier_id = models.BigIntegerField()
    delivery_person_id = models.BigIntegerField(null=True, blank=True)

    status = models.CharField(max_length=50, choices=ReturnStatus.choices, default=ReturnStatus.NEW)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=50, choices=ReturnReason.choices)
    image = models.ImageField(upload_to='returns/%Y/%m/%d/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ReturnRequestManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user_id", "created_at"])]

    def __str__(self):
        return f"Return Request #{self.pk} for Product {self.product_id}"

    def approve_by_supplier(self):
        self.status = self.ReturnStatus.ACCEPTED
        self.save()

    def reject_by_supplier(self):
        self.status = self.ReturnStatus.REJECTED
        self.save()

    def cancel(self):
        self.status = self.ReturnStatus.CANCELLED
        self.save()

class ReturnPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_id = models.BigIntegerField(unique=True, verbose_name=_("Supplier"))
    title = models.CharField(max_length=255, verbose_name=_("Title"), default=_("Standard Return Policy"))
    max_days_for_return = models.PositiveIntegerField(default=14, verbose_name=_("Max Days For Return"))
    allowed_conditions = models.JSONField(default=list, verbose_name=_("Allowed Conditions"))
    requires_admin_approval = models.BooleanField(default=False, verbose_name=_("Requires Admin Approval"))
    
    class Meta:
        verbose_name = _("Return Policy")
        verbose_name_plural = _("Return Policies")
        
    def __str__(self):
        return f"{self.title} - Supplier {self.supplier_id}"