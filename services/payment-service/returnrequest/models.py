import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        WITHDRAWAL_REQUEST = 'WITHDRAWAL_REQUEST', _('Withdrawal Request')
        WITHDRAWAL_COMPLETED = 'WITHDRAWAL_COMPLETED', _('Withdrawal Completed')
        WITHDRAWAL_CANCELLED = 'WITHDRAWAL_CANCELLED', _('Withdrawal Cancelled')
        RETURN_CREDIT = 'RETURN_CREDIT', _('Return Credit')
        RETURN_DEBIT = 'RETURN_DEBIT', _('Return Debit')
        CASH_BACK = 'CASH_BACK', _('Cash Back')
        RETURNED_CASH_BACK = 'RETURNED_CASH_BACK', _('Returned Cash Back')
        RETURNED_PRODUCT = 'RETURNED_PRODUCT', _('Returned Product')
        PURCHASED_PRODUCTS = 'PURCHASED_PRODUCTS', _('Purchased Products')
        DELIVERY_FEE = 'DELIVERY_FEE', _('Delivery Fee')
        SUPPLIER_TRANSFER = 'SUPPLIER_TRANSFER', _('Supplier Transfer') 
        REFUND_FAILED = 'REFUND_FAILED', _('Refund Failed')
        PURCHASED_COURSE = 'PURCHASED_COURSE', _('Purchased Course')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.BigIntegerField()
    transaction_type = models.CharField(max_length=50, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.amount} for User {self.user_id}"

class BalanceWithdrawRequest(models.Model):
    class TransferStatus(models.TextChoices):
        REQUESTED = 'Requested', _('Requested')
        AWAITING_APPROVAL = 'Awaiting Approval', _('Awaiting Approval')
        APPROVED = 'Approved', _('Approved')
        PROCESSING = 'Processing', _('Processing')
        COMPLETED = 'Completed', _('Completed')
        REJECTED = 'Rejected', _('Rejected')
        FAILED = 'Failed', _('Failed')

    class TransferType(models.TextChoices):
        BANK_TRANSFER = 'Bank Transfer'
        INSTAPAY = 'Instapay'
        PHONE_WALLET = 'Phone Wallet'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.BigIntegerField()
    related_transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, null=True)
    transfer_number = models.CharField(max_length=50)
    transfer_type = models.CharField(max_length=50, choices=TransferType.choices, default=TransferType.BANK_TRANSFER)
    transfer_status = models.CharField(max_length=50, choices=TransferStatus.choices, default=TransferStatus.REQUESTED)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Balance Withdraw Request"
        ordering = ['-created_at']