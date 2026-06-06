from django.urls import path
from .views import ProductRecommendationAPIView, PersonalizedRecommendationsView

urlpatterns = [
    path('products/<int:product_id>/', ProductRecommendationAPIView.as_view(), name='product-recommendations'),
    path('v2/personalized/', PersonalizedRecommendationsView.as_view(), name='personalized-recommendations'),
]