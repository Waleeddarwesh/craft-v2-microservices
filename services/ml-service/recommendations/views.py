from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from products.models import Product
from products.serializers import ProductSerializer  
from .models import FrequentlyBoughtTogether, UserProductView, UserProductInteraction
from .services import get_collaborative_filtering_recommendations

class ProductRecommendationAPIView(APIView):
    def get(self, request, product_id):
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Track the product view for the current user (if authenticated)
        if request.user.is_authenticated:
            UserProductView.objects.get_or_create(user=request.user, product=product)

        # Get "Frequently Bought Together" recommendations
        fbt_products = FrequentlyBoughtTogether.objects.filter(product=product).order_by('-score')[:5]
        fbt_serializer = ProductSerializer([rec.recommended_product for rec in fbt_products], many=True)

        # Get "Customers Who Viewed This Also Viewed" (Collaborative Filtering) recommendations
        collab_products = get_collaborative_filtering_recommendations(product)
        collab_serializer = ProductSerializer(collab_products, many=True)

        return Response({
            "frequently_bought_together": fbt_serializer.data,
            "customers_also_viewed": collab_serializer.data,
        }, status=status.HTTP_200_OK)

class PersonalizedRecommendationsView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required for personalized recommendations."}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Very simple collaborative filtering / content-based logic for V2:
        # 1. Get user's recent interactions (views)
        recent_views = UserProductView.objects.filter(user=request.user).order_by('-viewed_at')[:10]
        if not recent_views:
            # Fallback to trending products or similar
            products = Product.objects.order_by('-Rating')[:10]
        else:
            # Find products in the same category as the recently viewed ones
            categories = [view.product.Category for view in recent_views if view.product.Category]
            products = Product.objects.filter(Category__in=categories).exclude(id__in=[v.product.id for v in recent_views]).distinct().order_by('-Rating')[:10]
            
            # If still not enough, pad with top rated
            if products.count() < 10:
                more = Product.objects.exclude(id__in=[p.id for p in products]).order_by('-Rating')[:10 - products.count()]
                products = list(products) + list(more)

        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)