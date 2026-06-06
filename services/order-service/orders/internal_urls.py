from django.urls import path
from . import internal_views

urlpatterns = [
    path('<uuid:order_id>/', internal_views.InternalOrderDetail.as_view(), name='internal-order-detail'),
    path('bulk-lookup/', internal_views.InternalOrderBulkLookup.as_view(), name='internal-order-bulk-lookup'),
]
