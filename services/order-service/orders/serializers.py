"""
orders/serializers.py — Order Service
Removed: AddressSerializer, User imports from accounts.
Address is now an inline dict field (denormalized snapshot).
User identity comes from the JWT via request.user_id (set by middleware).
"""
from rest_framework import serializers

from .models import Order, OrderItem, Cart, CartItems, Wishlist, WishlistItem

# ─── Address ─────────────────────────────────────────────────────────────────
# No longer imported from accounts.serializers.
# An address snapshot is embedded directly in the order payload.

class AddressSnapshotSerializer(serializers.Serializer):
    """Inline, denormalized shipping address — no FK to auth-service DB."""
    street      = serializers.CharField(max_length=255)
    city        = serializers.CharField(max_length=100)
    state       = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country     = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)


# ─── Order Items ──────────────────────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = [
            "id",
            "product_id",       # plain IntegerField — no FK to catalog-service DB
            "product_name",     # denormalized snapshot
            "product_price",    # denormalized snapshot at time of order
            "quantity",
            "subtotal",
        ]
        read_only_fields = ["subtotal"]


# ─── Order ────────────────────────────────────────────────────────────────────

class OrderSerializer(serializers.ModelSerializer):
    items            = OrderItemSerializer(many=True, read_only=True)
    shipping_address = AddressSnapshotSerializer()

    class Meta:
        model  = Order
        fields = [
            "id",
            "user_id",           # plain IntegerField — no FK to auth-service DB
            "status",
            "items",
            "shipping_address",  # stored as JSONField on the model
            "total_price",
            "coupon_code",
            "discount_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user_id", "total_price", "created_at", "updated_at"]

    def create(self, validated_data):
        items_data           = validated_data.pop("items", [])
        shipping_address_data = validated_data.pop("shipping_address", {})
        order = Order.objects.create(
            **validated_data,
            shipping_address=shipping_address_data,
        )
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


# ─── Cart ─────────────────────────────────────────────────────────────────────

class CartItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CartItems
        fields = [
            "id",
            "product_id",    # plain IntegerField
            "product_name",  # denormalized
            "unit_price",    # denormalized at time of adding to cart
            "quantity",
            "subtotal",
        ]
        read_only_fields = ["subtotal"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemsSerializer(many=True, read_only=True)

    class Meta:
        model  = Cart
        fields = ["id", "user_id", "status", "items", "total_price", "created_at"]
        read_only_fields = ["id", "user_id", "total_price", "created_at"]


# ─── Wishlist ─────────────────────────────────────────────────────────────────

class WishlistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = WishlistItem
        fields = ["id", "product_id", "product_name", "added_at"]


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model  = Wishlist
        fields = ["id", "user_id", "items", "created_at"]
        read_only_fields = ["id", "user_id", "created_at"]
