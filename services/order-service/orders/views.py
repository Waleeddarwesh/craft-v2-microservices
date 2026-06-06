"""
orders/views.py — Order Service
Cross-service imports removed. Address data is now read from the
request body (denormalized) or fetched via craft_common HTTP client.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Order, OrderItem, Cart, CartItems, Wishlist, WishlistItem
from .serializers import (
    OrderSerializer,
    OrderItemSerializer,
    CartSerializer,
    CartItemsSerializer,
    WishlistSerializer,
    WishlistItemSerializer,
)
from craft_common.auth.permissions import HasRole

# NOTE: Address is no longer queried from the accounts app.
# Address data must be submitted inline in the order creation payload
# (denormalized snapshot) or retrieved via the auth-service internal API:
#   from craft_common.api_clients import auth_client
#   address = auth_client.get(f"/internal/users/{user_id}/addresses/{address_id}/")


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user_id=self.request.user_id)

    def create(self, request, *args, **kwargs):
        """
        Create an order. Address must be supplied inline in the payload as a
        denormalized snapshot — do NOT look it up from accounts.models.Address.

        Expected payload:
          {
            "items": [...],
            "shipping_address": {
              "street": "...", "city": "...", "country": "...", "zip": "..."
            }
          }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(user_id=request.user_id)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status not in ("PENDING", "PROCESSING"):
            return Response(
                {"detail": "Only pending or processing orders can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = "CANCELLED"
        order.save(update_fields=["status"])
        return Response({"detail": "Order cancelled."})


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user_id=self.request.user_id)

    def get_or_create_cart(self):
        cart, _ = Cart.objects.get_or_create(
            user_id=self.request.user_id, status="OPEN"
        )
        return cart

    @action(detail=False, methods=["get"])
    def my_cart(self, request):
        cart = self.get_or_create_cart()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """
        Add a product to the cart. Product details (name, price) must be
        supplied in the request body — do NOT import products.models.
        """
        cart = self.get_or_create_cart()
        serializer = CartItemsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=cart)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        cart = self.get_or_create_cart()
        cart.items.all().delete()
        return Response({"detail": "Cart cleared."})


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user_id=self.request.user_id)
