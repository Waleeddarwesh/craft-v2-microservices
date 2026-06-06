from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Order

class InternalOrderDetail(APIView):
    permission_classes = [] # internal

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        return Response({
            'id': str(order.id),
            'order_number': order.order_number,
            'user_id': order.user_id,
            'total_amount': str(order.total_amount),
            'status': order.status,
            'paid': order.paid
        })

class InternalOrderBulkLookup(APIView):
    permission_classes = []

    def post(self, request):
        ids = request.data.get('ids', [])
        orders = Order.objects.filter(id__in=ids)
        result = []
        for order in orders:
            result.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'user_id': order.user_id,
                'total_amount': str(order.total_amount),
                'status': order.status,
                'paid': order.paid
            })
        return Response(result)
