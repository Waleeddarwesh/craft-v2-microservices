import stripe
from django.conf import settings
from django.core.management.base import BaseCommand
from orders.models import Order
from payment.models import PaymentHistory

class Command(BaseCommand):
    help = 'Reconciles local orders with Stripe to detect discrepancies'

    def handle(self, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.stdout.write("Starting Payment Reconciliation...")
        
        # Get pending orders locally
        pending_orders = Order.objects.filter(status='created')
        discrepancies_found = 0
        
        for order in pending_orders:
            try:
                history = PaymentHistory.objects.get(order=order)
                if history.stripe_session_id:
                    session = stripe.checkout.Session.retrieve(history.stripe_session_id)
                    if session.payment_status == 'paid':
                        # Discrepancy! Stripe says paid, we say pending
                        history.payment_status = 'succeeded'
                        history.save()
                        order.status = 'ready_to_ship'
                        order.save()
                        discrepancies_found += 1
                        self.stdout.write(self.style.WARNING(f"Discrepancy fixed: Order {order.id} was paid in Stripe but pending locally."))
            except PaymentHistory.DoesNotExist:
                pass
            except stripe.error.StripeError as e:
                self.stdout.write(self.style.ERROR(f"Stripe error for Order {order.id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Reconciliation complete. Fixed {discrepancies_found} issues."))
