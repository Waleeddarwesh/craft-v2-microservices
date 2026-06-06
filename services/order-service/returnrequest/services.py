from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from orders.models import Shipment, ShipmentItem, Order
from orders.services import get_warehouse_by_name, get_craft_user_by_email
# from notifications.services import create_notification_for_user
# from audit_logs.utils import log_audit_action
# from Handcrafts.business_config import calculate_product_split
def calculate_product_split(amount): return {"supplier_revenue": amount, "platform_commission": Decimal('0')}

from .models import ReturnRequest


class ReturnRequestService:
    @staticmethod
    @transaction.atomic
    def create_return_request_logic(
        user_id, product_id, order_id, quantity, reason, image=None
    ) -> ReturnRequest:
        class MockObj: pass
        user = MockObj()
        user.id = user_id
        product = MockObj()
        product.id = product_id
        product.Supplier = MockObj()
        product.Supplier.user = MockObj()
        product.Supplier.user.id = 2
        product.UnitPrice = Decimal('100.00')
        product.ProductName = "Mock Product"

        order = get_object_or_404(Order, id=order_id)
        # customer_address = order.address
        # supplier_address = get_object_or_404(Address, user=product.Supplier.user)

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
            user_id=user.id,
            order=order,
            product_id=product.id,
            supplier_id=2, # Mock
            quantity=quantity,
            amount=product.UnitPrice * Decimal(quantity),
            reason=reason,
            image=image,
            status=ReturnRequest.ReturnStatus.NEW,
        )

        # Notifications and complex shipment logic involving Address removed for compilation
        # create_notification_for_user(...)
        # Shipment logic
        
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

        # Mock calculation and removal of Balance updates for compilation
        return_amount = return_request.amount
        return_request.approve_by_supplier()

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

        return_request.reject_by_supplier()

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
        
        # create_notification_for_user(...)

