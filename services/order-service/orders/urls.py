from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('whishlists', views.WishlistViewSet, basename='whishlist')
router.register('carts', views.CartViewSet, basename='cart')
router.register('orders', views.OrderViewSet, basename="order")

urlpatterns = [
    path('', include(router.urls)),
    path('orders/supplier-orders/<uuid:pk>/', views.OrderViewSet.as_view({'get': 'retrieve_supplier_order'}),
         name='supplier-orders-details'),
    path('orders/supplier-orders/<uuid:pk>/ready-to-ship/', views.OrderViewSet.as_view({'post': 'ready_to_ship'}),
         name='ready-to-ship'),
]