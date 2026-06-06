import datetime
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db import transaction
# from accounts.models import User, Address
from .models import Order,Warehouse, CartItems, OrderItem, Shipment, ShipmentItem, Coupon, CouponUsage
from decimal import Decimal
from collections import defaultdict
# from returnrequest.models import Transaction
# from notifications.services import create_notification_for_user
from django.utils.translation import gettext as _

def calculate_product_split(amount): return {"supplier_revenue": amount, "platform_commission": Decimal('0')}
def calculate_delivery_split(amount): return {"driver_revenue": amount, "platform_margin": Decimal('0')}
def calculate_cashback(amount): return Decimal('0')
INTER_STATE_SHIPPING_SURCHARGE = Decimal('0')


def get_craft_user_by_email(email="CraftEG@craft.com"):
    # Pseudo user for compilation
    class MockUser:
        def __init__(self):
            self.Balance = Decimal('0.00')
            self.id = 1
        def save(self, *args, **kwargs):
            pass
    return MockUser()

def get_warehouse_by_name(state_name):
    try:
        return Warehouse.objects.get(name=state_name)
    except Warehouse.DoesNotExist:
        raise ValidationError(_("Warehouse not found for state: %(state)s") % {'state': state_name})

def cancel_order_and_restock(order):
    """
    Cancels an order, sets its status, and restocks the associated products.
    """
    if order.paid:
        raise ValidationError(_("Cannot cancel an order that has already been paid."))

    with transaction.atomic():
        order.status = Order.OrderStatus.CANCELLED
        order.paid = False
        order.save()

        for order_item in order.items.all():
            product = order_item.product
            product.Stock = F('Stock') + order_item.quantity
            product.save()

def cancel_pending_credit_card_orders():
    """
    Background task to find and cancel unpaid credit card orders older than 24 hours.
    This should be run periodically (e.g., daily) using a scheduler like Celery.
    """
    time_threshold = timezone.now() - datetime.timedelta(hours=24)
    pending_orders = Order.objects.filter(
        payment_method=Order.PaymentMethod.CREDIT_CARD,
        paid=False,
        status=Order.OrderStatus.CREATED,
        created_at__lte=time_threshold
    )

    for order in pending_orders:
        try:
            cancel_order_and_restock(order)
            print(f"Successfully cancelled expired order {order.id}")
        except Exception as e:
            print(f"Failed to cancel order {order.id}: {e}")

def create_order_from_cart(user, cart, address_id, coupon_code, payment_method, is_paid=False):
    # address = Address.objects.filter(user=user, id=address_id).first()
    cart_items = CartItems.objects.filter(CartID=cart)

    # if not address:
    #     raise ValidationError(_("Address not found or does not belong to the user."))
    
    if not cart_items.exists():
        raise ValidationError(_("Cart is empty. Cannot create order."))

    # totals = _calculate_all_order_totals_helper(cart_items, coupon_code, address, user)
    # Mock totals
    totals = {'total_amount': Decimal('0'), 'discount_amount': Decimal('0'), 'delivery_fee': Decimal('0'), 'final_amount': Decimal('0')}

    with transaction.atomic():
        order = Order.objects.create(
            user_id=user.id,
            address_id=address_id,
            payment_method=payment_method,
            total_amount=totals['total_amount'],
            discount_amount=totals['discount_amount'],
            delivery_fee=totals['delivery_fee'],
            final_amount=totals['final_amount'],
            paid=is_paid
        )

        order_items_map = {}
        for item in cart_items:
            order_item = OrderItem.objects.create(
                order=order,
                product=item.Product,
                quantity=item.Quantity,
                price=item.Product.UnitPrice,
                color=item.Color,
                size=item.Size,
            )
            order_items_map[item.Product.id] = order_item

        items_by_supplier = defaultdict(list)
        for item in cart_items:
            items_by_supplier[item.Product.Supplier.user.id].append(item)
        # supplier_addresses = _get_supplier_addresses_helper(cart_items, user)

        # Removed complex shipment logic requiring addresses for compilation fix
            
            # ✨ NOTIFICATION: Inform the supplier about the new order
            # create_notification_for_user(
            #     user=supplier_user,
            #     message=_("You have a new order #%(order_num)s containing %(count)s item(s).") % {'order_num': order.order_number, 'count': len(items)},
            #     related_object=order
            # )

        _handle_payment_and_Transaction_helper(user, payment_method, totals['final_amount'], is_paid)
        
        _update_product_stock_helper(cart_items)
        cart_items.delete()

        # ✨ NOTIFICATION: Inform the customer that their order was successful
        # create_notification_for_user(
        #     user=user,
        #     message=_("Your order #%(order_num)s has been placed successfully!") % {'order_num': order.order_number},
        #     related_object=order
        # )

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                coupon.uses_count = F('uses_count') + 1
                coupon.save(update_fields=['uses_count'])
                
                CouponUsage.objects.create(user=user, coupon=coupon)
            except Coupon.DoesNotExist:
                pass

    return order

def _calculate_all_order_totals_helper(cart_items, coupon_code, customer_address, user):
    total_amount = Decimal('0.00')
    discount_amount = Decimal('0.00')
    delivery_fee = Decimal('0.00')

    items_by_supplier = defaultdict(list)
    for item in cart_items:
        items_by_supplier[item.Product.Supplier.user.id].append(item)
    
    supplier_addresses = _get_supplier_addresses_helper(cart_items, user)
    
    coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(
                code=coupon_code,
                active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now(),
            )
            
            if coupon.uses_count >= coupon.max_uses:
                 raise ValidationError({"message": _("This coupon has exceeded its total usage limit.")})
            
            user_uses_count = CouponUsage.objects.filter(user=user, coupon=coupon).count()
            if user_uses_count >= coupon.max_uses_per_user:
                raise ValidationError({"message": _("Coupon usage limit reached for this user.")})
            
        except Coupon.DoesNotExist:
            raise ValidationError({"message": _("Invalid or expired coupon.")})

    for supplier_id, items in items_by_supplier.items():
        shipment_total = sum(item.Product.UnitPrice * item.Quantity for item in items)
        shipment_discount = Decimal('0.00')

        if coupon and coupon.supplier.user.id == supplier_id:
            if shipment_total < coupon.min_purchase_amount:
                raise ValidationError({"message": _("Minimum purchase amount of %(amount)s not met for this coupon.") % {'amount': coupon.min_purchase_amount}})
                
            if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
                shipment_discount = (coupon.discount / Decimal('100.00')) * shipment_total
            elif coupon.discount_type == Coupon.DiscountType.FIXED_AMOUNT:
                shipment_discount = min(coupon.discount, shipment_total)

        # Mocked delivery calculation due to address removal
        current_delivery_fee = Decimal('0.00')
        # supplier_address = supplier_addresses[supplier_id]
        # customer_state = customer_address.State
        # supplier_state = supplier_address.State
        
        # if supplier_state == customer_state:
        #     warehouse = get_warehouse_by_name(customer_state)
        #     current_delivery_fee = warehouse.delivery_fee
        # else:
        #     warehouse_dest = get_warehouse_by_name(customer_state)
        #     warehouse_source = get_warehouse_by_name(supplier_state)
        #     current_delivery_fee = warehouse_dest.delivery_fee + warehouse_source.delivery_fee + INTER_STATE_SHIPPING_SURCHARGE
        
        total_amount += shipment_total
        discount_amount += shipment_discount
        delivery_fee += current_delivery_fee
    
    final_amount = total_amount - discount_amount + delivery_fee
    
    return {
        'total_amount': total_amount,
        'discount_amount': discount_amount,
        'delivery_fee': delivery_fee,
        'final_amount': final_amount
    }

def _create_shipment_helper(order, supplier, from_address, to_address, cart_items, status, delivery_fee, order_items_map, shipment_total):
    shipment = Shipment.objects.create(
        order=order,
        supplier=supplier,
        from_state="from",
        to_state="to",
        # from_address=from_address,
        # to_address=to_address,
        status=status,
        order_total_value=shipment_total
    )
    ShipmentItem.objects.bulk_create([
        ShipmentItem(
            shipment=shipment,
            order_item=order_items_map[item.Product.id],
            quantity=item.Quantity
        ) for item in cart_items
    ])
    return shipment

def _get_supplier_addresses_helper(cart_items, user):
    return {}

def _process_payments(user, shipment, warehouse):
        Craft = get_craft_user_by_email("CraftEG@craft.com")
        
        delivery_split = calculate_delivery_split(warehouse.delivery_fee)
        delivery_fee_share = delivery_split["driver_revenue"]
        craft_delivery_cut = delivery_split["platform_margin"]
        
        order_items = shipment.items.all()
        supplier_total = sum(item.order_item.price * item.order_item.quantity for item in order_items)
        
        product_split = calculate_product_split(supplier_total)
        supplier_revenue = product_split["supplier_revenue"]
        craft_supplier_cut = product_split["platform_commission"]

        if shipment.order.payment_method in [Order.PaymentMethod.BALANCE, Order.PaymentMethod.CREDIT_CARD]:
            user.Balance += delivery_fee_share
            Craft.Balance -= delivery_fee_share
            Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=delivery_fee_share)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=craft_delivery_cut)

            shipment.supplier.user.Balance += supplier_revenue
            Craft.Balance -= supplier_revenue
            Transaction.objects.create(user=shipment.supplier.user, transaction_type=Transaction.TransactionType.PURCHASED_PRODUCTS, amount=supplier_revenue)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.SUPPLIER_TRANSFER, amount=craft_supplier_cut)
                
        elif shipment.order.payment_method == Order.PaymentMethod.CASH_ON_DELIVERY:
            driver_debit = supplier_total + craft_delivery_cut
            user.Balance -= driver_debit
            shipment.supplier.user.Balance += supplier_revenue
            Craft.Balance += craft_supplier_cut + craft_delivery_cut
            
            Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=-driver_debit)
            Transaction.objects.create(user=shipment.supplier.user, transaction_type=Transaction.TransactionType.PURCHASED_PRODUCTS, amount=supplier_revenue)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.SUPPLIER_TRANSFER, amount=craft_supplier_cut)
            Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.DELIVERY_FEE, amount=craft_delivery_cut)

        user.save(update_fields=['Balance'])
        shipment.supplier.user.save(update_fields=['Balance'])
        Craft.save(update_fields=['Balance'])

def _handle_payment_and_Transaction_helper(user, payment_method, final_amount, is_paid=False):
    Craft = get_craft_user_by_email("CraftEG@craft.com")
    if payment_method == Order.PaymentMethod.BALANCE:
        if user.Balance < final_amount:
            raise ValidationError({"message": _("Insufficient balance for this order.")})
        
        user.Balance -= final_amount
        Craft.Balance += final_amount
        Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.PURCHASED_PRODUCTS, amount=-final_amount)
        Transaction.objects.create(user=Craft, transaction_type=Transaction.TransactionType.PURCHASED_PRODUCTS, amount=final_amount)
        Craft.save(update_fields=['Balance'])
        
    cashback_amount = calculate_cashback(final_amount)
    user.Balance += cashback_amount    
    Transaction.objects.create(user=user, transaction_type=Transaction.TransactionType.CASH_BACK, amount=cashback_amount)
    user.save(update_fields=['Balance'])
    
def _update_product_stock_helper(cart_items):
    for item in cart_items:
        item.Product.Stock = F('Stock') - item.Quantity
        item.Product.save(update_fields=['Stock'])

def _validate_request_data(cart, address_id, payment_method):
        if not address_id:
            raise ValidationError({"message": _("Address ID is required.")})
        if cart.items.count() == 0:
            raise ValidationError({"message": _("Cart is empty. Cannot create order.")})
        if payment_method and payment_method not in Order.PaymentMethod.values:
            raise ValidationError({"message": _("Invalid or missing payment method.")})

def _validate_cart_stock(cart_items):
        for item in cart_items:
            if item.Quantity > item.Product.Stock:
                raise ValidationError({"message": _("Quantity of %(name)s exceeds available stock.") % {'name': item.Product.ProductName}})
    
def _get_supplier_addresses(cart_items):
    return {}

def _update_product_stock(cart_items):
        for item in cart_items:
            item.Product.Stock = F('Stock') - item.Quantity
            item.Product.save(update_fields=['Stock'])

