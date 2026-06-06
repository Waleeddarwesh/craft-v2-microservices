import datetime
from rest_framework import serializers
# Mock imports for missing microservice dependencies
# from course.models import Course
# from orders.models import Order
from django.conf import settings

class OrderInformationSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()

    def validate_order_id(self, value):
        # Microservice validation would be an API call
        return value
    
class CourseInformationSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()

    def validate_course_id(self, value):
        # Microservice validation would be an API call
        return value

        return value
from .models import PaymentHistory
class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = '__all__'
