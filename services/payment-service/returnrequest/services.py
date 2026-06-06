from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from accounts.models import Address, User
from orders.models import Shipment, ShipmentItem, Order, Product
from orders.services import get_warehouse_by_name, get_craft_user_by_email
from notifications.services import create_notification_for_user
from audit_logs.utils import log_audit_action
from Handcrafts.business_config import calculate_product_split

from .models import BalanceWithdrawRequest, ReturnRequest, Transaction


class ReturnRequestService:
    @staticmethod
    @transaction.atomic
    def create_return_request_logic(
        user_id, product_id, order_id, quantity, reason, image=None
    ) -> ReturnRequest:
        user = get_object_or_404(User, id=user_id)
        product = get_object_or_404(Product, id=product_id)
        order = get_object_or_404(Order, id=order_id)
        customer_address = order.address
        supplier_address = get_object_or_404(Address, user=product.Supplier.user)

        if order.status != Order.OrderStatus.DELIVERED_SUCCESSFULLY:
            raise ValidationError(_("Return requests can only be created for delivered orders."))

        # Enforce Return Policy
        policy = getattr(product.Supplier, 'return_policy', None)
        requires_admin_approval = False
        if policy:
            days_since_delivery = (timezone.now() - order.updated_at).days
            if days_since_delivery > policy.max_days_for_return:
                raise ValidationError(_("The return period of {max_days} days for this item has expired.").format(max_days=policy.max_days_for_return))
            
            if policy.allowed_conditions and reason not in policy.allowed_conditions:
                raise ValidationError(_("This reason is not accepted under the supplier's return policy."))
                
            requires_admin_approval = policy.requires_admin_approval

        # If requires admin approval, we could handle it differently. For now, we proceed to create.
        
        return_request = ReturnRequest.objects.create(
            user=user,
            order=order,
            product=product,
            supplier=product.Supplier,
            quantity=quantity,
            amount=product.UnitPrice * Decimal(quantity),
            reason=reason,
            image=image,
            status=ReturnRequest.ReturnStatus.NEW,
        )

        create_notification_for_user(
            user=user,
            message=_("Your return request for '{product_name}' has been submitted.").format(product_name=product.ProductName),
            related_object=return_request,
            image=image
        )
        create_notification_for_user(
            user=product.Supplier.user,
            message=_("You have received a new return request for '{product_name}'.").format(product_name=product.ProductName),
            related_object=return_request,
            image=image
        )

        customer_state = customer_address.State
        supplier_state = supplier_address.State

        if customer_state == supplier_state:
            shipment = Shipment.objects.create(
                return_request=return_request,
                supplier=product.Supplier,
                from_address=customer_address,
                to_address=supplier_address,
                from_state=customer_state,
                to_state=supplier_state,
                status=Shipment.ShipmentStatus.CREATED,
            )
            ShipmentItem.objects.create(
                shipment=shipment, return_request=return_request, quantity=quantity
            )
        else:
            warehouse_source = get_warehouse_by_name(customer_state)
            
            shipment1 = Shipment.objects.create(
                return_request=return_request,
                supplier=product.Supplier,
                from_address=customer_address,
                to_address=warehouse_source.Address,
                from_state=customer_state,
                to_state=customer_state,
                status=Shipment.ShipmentStatus.CREATED
            )
            ShipmentItem.objects.create(shipment=shipment1, return_request=return_request, quantity=quantity)

            shipment2 = Shipment.objects.create(
                return_request=return_request,
                supplier=product.Supplier,
                from_address=warehouse_source.Address,
                to_address=supplier_address,
                from_state=customer_state,
                to_state=supplier_state,
                status=Shipment.ShipmentStatus.In_Transmit
            )
            ShipmentItem.objects.create(shipment=shipment2, return_request=return_request, quantity=quantity)
        
        return return_request

    @staticmethod
    @transaction.atomic
    def process_supplier_approval(return_request: ReturnRequest):
        if return_request.status != ReturnRequest.ReturnStatus.NEW:
            raise ValidationError(
                _("This return request cannot be approved. Its current status is '{status}'.").format(status=return_request.get_status_display())
            )

        final_shipment = return_request.shipments.order_by("-created_at").first()
        if (
            not final_shipment
            or final_shipment.status != Shipment.ShipmentStatus.DELIVERED_SUCCESSFULLY
        ):
            raise ValidationError(
                _("Return cannot be approved until the item has been delivered to the supplier.")
            )

        return_amount = return_request.amount
        customer = return_request.user
        supplier_user = return_request.supplier.user

        # Calculate accurate refund portions
        split = calculate_product_split(return_amount)
        supplier_debit = split["supplier_revenue"]
        platform_debit = split["platform_commission"]

        customer.Balance += return_amount
        supplier_user.Balance -= supplier_debit
        customer.save(update_fields=["Balance"])
        supplier_user.save(update_fields=["Balance"])

        Transaction.objects.create(
            user=customer,
            transaction_type=Transaction.TransactionType.RETURN_CREDIT,
            amount=return_amount,
            related_object=return_request,
        )
        Transaction.objects.create(
            user=supplier_user,
            transaction_type=Transaction.TransactionType.RETURN_DEBIT,
            amount=-supplier_debit,
            related_object=return_request,
        )
        
        Craft = get_craft_user_by_email("CraftEG@craft.com")
        if Craft:
            Craft.Balance -= platform_debit
            Craft.save(update_fields=["Balance"])
            Transaction.objects.create(
                user=Craft,
                transaction_type=Transaction.TransactionType.RETURN_DEBIT,
                amount=-platform_debit,
                related_object=return_request,
            )

        return_request.approve_by_supplier()

        create_notification_for_user(
            user=customer,
            message=_("Your return request for '{product_name}' has been approved.").format(product_name=return_request.product.ProductName),
            related_object=return_request
        )
        
        log_audit_action(
            user=supplier_user,
            action="Refund approved",
            instance=return_request,
            new_value={'status': return_request.status}
        )

    @staticmethod
    def reject_return_request(return_request: ReturnRequest):
        if return_request.status != ReturnRequest.ReturnStatus.NEW:
            raise ValidationError(
                _("This return request cannot be rejected. Its current status is '{status}'.").format(status=return_request.get_status_display())
            )

        final_shipment = return_request.shipments.order_by("-created_at").first()
        if (
            not final_shipment
            or final_shipment.status != Shipment.ShipmentStatus.DELIVERED_SUCCESSFULLY
        ):
            raise ValidationError(
                _("Return cannot be rejected until the item has been delivered to you.")
            )

        return_request.reject_by_supplier()

        create_notification_for_user(
            user=return_request.user,
            message=_("Your return request for '{product_name}' has been rejected.").format(product_name=return_request.product.ProductName),
            related_object=return_request
        )
        
        log_audit_action(
            user=return_request.supplier.user,
            action="Refund rejected",
            instance=return_request,
            new_value={'status': return_request.status}
        )

    @staticmethod
    @transaction.atomic
    def cancel_return_request(return_request: ReturnRequest):
        cancellable_statuses = [
            Shipment.ShipmentStatus.CREATED,
            Shipment.ShipmentStatus.READY_TO_SHIP,
        ]
        shipments = return_request.shipments.select_for_update().all()

        if not shipments.exists():
            return_request.cancel()
        else:
            for shipment in shipments:
                if shipment.status not in cancellable_statuses:
                    raise ValidationError(
                        _("Cannot cancel. A shipment for this return is already in progress (status: {status}).").format(status=shipment.get_status_display())
                    )
            shipments.update(status=Shipment.ShipmentStatus.CANCELLED)
            return_request.cancel()
        
        create_notification_for_user(
            user=return_request.user,
            message=_("You have successfully cancelled your return request for '{product_name}'.").format(product_name=return_request.product.ProductName),
            related_object=return_request
        )
        create_notification_for_user(
            user=return_request.supplier.user,
            message=_("The return request for '{product_name}' has been cancelled by the customer.").format(product_name=return_request.product.ProductName),
            related_object=return_request
        )


class BalanceService:
    @staticmethod
    def _run_fraud_check(request: BalanceWithdrawRequest):
        if request.amount > 1000:
            request.risk_score = 75.0
            request.transfer_status = (
                BalanceWithdrawRequest.TransferStatus.AWAITING_APPROVAL
            )
            request.admin_notes = _("Flagged for manual review due to high amount.")
        else:
            request.risk_score = 10.0
            request.transfer_status = BalanceWithdrawRequest.TransferStatus.AWAITING_APPROVAL
        request.save()

    @staticmethod
    @transaction.atomic
    def create_withdrawal_request_logic(
        user_id, amount: Decimal, transfer_number: str, transfer_type: str, notes: str = None
    ) -> BalanceWithdrawRequest:
        user = get_object_or_404(User, id=user_id)
        if user.Balance < amount:
            raise ValidationError(_("Insufficient balance for this withdrawal."))

        if amount <= 0:
            raise ValidationError(_("Withdrawal amount must be positive."))

        user.Balance -= amount
        user.save(update_fields=["Balance"])

        transaction_log = Transaction.objects.create(
            user=user,
            transaction_type=Transaction.TransactionType.WITHDRAWAL_REQUEST,
            amount=-amount,
        )

        withdrawal_request = BalanceWithdrawRequest.objects.create(
            user=user,
            amount=amount,
            transfer_number=transfer_number,
            transfer_type=transfer_type,
            notes=notes,
            related_transaction=transaction_log,
        )

        BalanceService._run_fraud_check(withdrawal_request)

        create_notification_for_user(
            user=user,
            message=_("Your withdrawal request for EGP {amount:.2f} has been submitted for review.").format(amount=amount),
            related_object=withdrawal_request
        )

        return withdrawal_request

    @staticmethod
    @transaction.atomic
    def approve_withdrawal(request: BalanceWithdrawRequest, admin_user_id, admin_notes: str):
        admin_user = get_object_or_404(User, id=admin_user_id)
        if request.transfer_status != BalanceWithdrawRequest.TransferStatus.AWAITING_APPROVAL:
            raise ValidationError(_("This request is not awaiting approval."))

        request.transfer_status = BalanceWithdrawRequest.TransferStatus.APPROVED
        request.admin_notes = admin_notes
        request.admin_notes += _("\nManually approved by {admin_name} on {date}.").format(
            admin_name=admin_user.get_full_name,
            date=timezone.now().strftime('%Y-%m-%d %H:%M')
        )
        request.save()

        create_notification_for_user(
            user=request.user,
            message=_("Your withdrawal request for EGP {amount:.2f} has been approved.").format(amount=request.amount),
            related_object=request
        )
        
        log_audit_action(
            user=admin_user,
            action="Withdrawal approved",
            instance=request,
            new_value={'transfer_status': request.transfer_status}
        )

    @staticmethod
    @transaction.atomic
    def reject_withdrawal(request: BalanceWithdrawRequest, admin_user_id, admin_notes: str):
        admin_user = get_object_or_404(User, id=admin_user_id)
        if request.transfer_status not in [
            BalanceWithdrawRequest.TransferStatus.AWAITING_APPROVAL,
            BalanceWithdrawRequest.TransferStatus.REQUESTED,
        ]:
            raise ValidationError(_("This request cannot be rejected."))

        original_status = request.transfer_status
        request.transfer_status = BalanceWithdrawRequest.TransferStatus.REJECTED
        request.admin_notes = admin_notes
        request.admin_notes += _("\nManually rejected by {admin_name} on {date}.").format(
            admin_name=admin_user.get_full_name,
            date=timezone.now().strftime('%Y-%m-%d %H:%M')
        )
        request.save()

        create_notification_for_user(
            user=request.user,
            message=_("Your withdrawal request for EGP {amount:.2f} was rejected. Reason: {reason}").format(
                amount=request.amount,
                reason=admin_notes
            ),
            related_object=request
        )
        
        log_audit_action(
            user=admin_user,
            action="Withdrawal rejected",
            instance=request,
            new_value={'transfer_status': request.transfer_status}
        )

        if original_status == BalanceWithdrawRequest.TransferStatus.AWAITING_APPROVAL:
            user = request.user
            user.Balance += request.amount
            user.save(update_fields=["Balance"])

            Transaction.objects.create(
                user=user,
                transaction_type=Transaction.TransactionType.WITHDRAWAL_CANCELLED,
                amount=request.amount,
                related_object=request,
            )

    @staticmethod
    def process_approved_request(request: BalanceWithdrawRequest):
        if request.transfer_status != BalanceWithdrawRequest.TransferStatus.APPROVED:
            raise ValidationError(_("This request is not approved for processing."))

        request.transfer_status = BalanceWithdrawRequest.TransferStatus.PROCESSING
        request.save()

        # In a real scenario, this is where you would integrate with a payment gateway.
        # For now, we'll simulate a successful transfer.

        request.transfer_status = BalanceWithdrawRequest.TransferStatus.COMPLETED
        request.save()

        Transaction.objects.create(
            user=request.user,
            transaction_type=Transaction.TransactionType.WITHDRAWAL_COMPLETED,
            amount=-request.amount,
            related_object=request,
        )

        create_notification_for_user(
            user=request.user,
            message=_("Your withdrawal of EGP {amount:.2f} is complete and has been sent.").format(amount=request.amount),
            related_object=request
        )
        
        log_audit_action(
            user=None,  # System action
            action="Withdrawal completed",
            instance=request,
            new_value={'transfer_status': request.transfer_status}
        )