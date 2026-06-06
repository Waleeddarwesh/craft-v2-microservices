from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import PaymentHistory
import stripe
import logging

logger = logging.getLogger(__name__)

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_mock')

class InitiatePayment(APIView):
    permission_classes = [] # internal

    def post(self, request):
        order_id = request.data.get('order_id')
        amount = request.data.get('amount')
        user_id = request.data.get('user_id')
        
        if not order_id or not amount:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Create Stripe Checkout Session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Order {order_id}',
                        },
                        'unit_amount': int(float(amount) * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=getattr(settings, 'PAYMENT_SUCCESS_URL', 'http://localhost/success'),
                cancel_url=getattr(settings, 'PAYMENT_CANCEL_URL', 'http://localhost/cancel'),
                metadata={'order_id': order_id, 'user_id': user_id}
            )
            
            # Record payment history
            PaymentHistory.objects.create(
                order_id=order_id,
                user_id=user_id,
                stripe_session_id=session.id,
                payment_status='pending'
            )
            
            return Response({'checkout_url': session.url, 'session_id': session.id})
            
        except Exception as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RefundPayment(APIView):
    permission_classes = []

    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'Missing order_id'}, status=status.HTTP_400_BAD_REQUEST)
            
        payment = PaymentHistory.objects.filter(order_id=order_id, payment_status='succeeded').first()
        if not payment or not payment.stripe_payment_intent_id:
            return Response({'error': 'No successful payment found'}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            refund = stripe.Refund.create(
                payment_intent=payment.stripe_payment_intent_id,
            )
            return Response({'status': 'refund_initiated', 'refund_id': refund.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
