from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from orders.models import Order, OrderItem
from .models import ReturnRequest

class ReturnRequestCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(write_only=True)
    order = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), write_only=True
    )
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=ReturnRequest.ReturnReason.choices)
    image = serializers.ImageField(required=False, allow_null=True, use_url=True)

    def validate(self, data):
        user = self.context['request'].user
        product_id = data.get('product_id')
        order = data.get('order')
        quantity = data.get('quantity')

        if order.user != user:
            raise serializers.ValidationError(_("You can only create returns for your own orders."))

        # try:
        #     order_item = OrderItem.objects.get(order=order, product_id=product_id)
        # except OrderItem.DoesNotExist:
        #     raise serializers.ValidationError(_("This product was not found in the specified order."))

        # if quantity > order_item.quantity:
        #     raise serializers.ValidationError(_("Quantity cannot exceed the ordered quantity ({quantity}).").format(quantity=order_item.quantity))

        # if ReturnRequest.objects.filter(user_id=user.id, product_id=product_id, order=order).exists():
        #     raise serializers.ValidationError(_("A return request for this product in this order already exists."))
            
        return data

class ReturnRequestListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.ProductName', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = ReturnRequest
        fields = ("id", "order_number", "created_at" , "product_name", "amount", "image")

class ReturnRequestDetailSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    supplier = serializers.StringRelatedField(read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    reason = serializers.CharField(source='get_reason_display', read_only=True)
    image = serializers.ImageField(read_only=True, use_url=True)
    
    class Meta:
        model = ReturnRequest
        fields = "__all__"
