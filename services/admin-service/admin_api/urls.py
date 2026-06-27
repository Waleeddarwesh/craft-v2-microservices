from django.urls import path
from . import views
from craft_common.api_clients import (
    auth_client, catalog_client, order_client, 
    payment_client, platform_client, reporting_client, realtime_client
)

urlpatterns = [
    # --- Identity & Config (Handled by Admin Service itself) ---
    path('me/', views.DashboardIdentityView.as_view(), name='admin-identity'),

    # --- KPI & Chart Data (Reporting Service) ---
    path('search/', views.GenericProxyView.as_view(client=reporting_client), name='admin-global-search'),
    path('stats/', views.GenericProxyView.as_view(client=reporting_client), name='admin-stats'),
    path('charts/', views.GenericProxyView.as_view(client=reporting_client), name='admin-charts'),
    path('reports/', views.GenericProxyView.as_view(client=reporting_client), name='admin-reports'),
    path('health/', views.GenericProxyView.as_view(client=reporting_client), name='admin-health'),
    
    # --- Catalog Service ---
    path('top-products/', views.GenericProxyView.as_view(client=catalog_client), name='admin-top-products'),
    path('products/', views.GenericProxyView.as_view(client=catalog_client), name='admin-products'),
    path('courses/', views.GenericProxyView.as_view(client=catalog_client), name='admin-courses'),
    path('moderation/products/', views.GenericProxyView.as_view(client=catalog_client), name='admin-moderation-products'),
    path('moderation/products/<int:pk>/action/', views.GenericProxyView.as_view(client=catalog_client), name='admin-moderation-products-action'),

    # --- Platform Service ---
    path('recent-activity/', views.GenericProxyView.as_view(client=platform_client), name='admin-recent-activity'),
    path('reviews/', views.GenericProxyView.as_view(client=platform_client), name='admin-reviews'),
    path('reviews/<int:pk>/action/', views.GenericProxyView.as_view(client=platform_client), name='admin-review-action'),
    path('support-tickets/', views.GenericProxyView.as_view(client=platform_client), name='admin-support-tickets'),
    path('support-tickets/<int:pk>/', views.GenericProxyView.as_view(client=platform_client), name='admin-support-ticket-detail'),
    path('disputes/', views.GenericProxyView.as_view(client=platform_client), name='admin-disputes'),
    path('disputes/<int:pk>/', views.GenericProxyView.as_view(client=platform_client), name='admin-dispute-detail'),
    path('fraud-alerts/', views.GenericProxyView.as_view(client=platform_client), name='admin-fraud-alerts'),
    path('fraud-alerts/<int:pk>/action/', views.GenericProxyView.as_view(client=platform_client), name='admin-fraud-alert-action'),

    # --- Order Service ---
    path('orders/', views.GenericProxyView.as_view(client=order_client), name='admin-orders'),
    path('orders/<uuid:pk>/status/', views.GenericProxyView.as_view(client=order_client), name='admin-order-status'),
    path('returns/', views.GenericProxyView.as_view(client=order_client), name='admin-returns-list'),
    path('returns/<uuid:pk>/action/', views.GenericProxyView.as_view(client=order_client), name='admin-return-action'),
    path('coupons/', views.GenericProxyView.as_view(client=order_client), name='admin-coupons'),
    path('performance/delivery/', views.GenericProxyView.as_view(client=order_client), name='admin-delivery-performance'),

    # --- Payment Service ---
    path('transactions/', views.GenericProxyView.as_view(client=payment_client), name='admin-transactions'),
    path('withdrawals/', views.GenericProxyView.as_view(client=payment_client), name='admin-withdrawals-list'),
    path('withdrawals/<uuid:pk>/action/', views.GenericProxyView.as_view(client=payment_client), name='admin-withdrawal-action'),
    path('payments/', views.GenericProxyView.as_view(client=payment_client), name='admin-payments'),
    path('finance/reconciliation/', views.GenericProxyView.as_view(client=payment_client), name='admin-financial-reconciliation'),

    # --- Auth Service ---
    path('users/', views.GenericProxyView.as_view(client=auth_client), name='admin-users'),
    path('users/<int:pk>/', views.GenericProxyView.as_view(client=auth_client), name='admin-user-detail'),
    path('users/<int:pk>/toggle/', views.GenericProxyView.as_view(client=auth_client), name='admin-user-toggle'),
    path('users/supplier/<int:pk>/', views.GenericProxyView.as_view(client=auth_client), name='admin-supplier-approval'),
    path('users/delivery/<int:pk>/', views.GenericProxyView.as_view(client=auth_client), name='admin-delivery-approval'),
    path('performance/suppliers/', views.GenericProxyView.as_view(client=auth_client), name='admin-supplier-performance'),

    # --- Realtime Service ---
    path('notifications/', views.GenericProxyView.as_view(client=realtime_client), name='admin-notifications'),
    path('notifications/send/', views.GenericProxyView.as_view(client=realtime_client), name='admin-send-notification'),
]
