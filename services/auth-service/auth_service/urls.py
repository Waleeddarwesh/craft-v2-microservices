from django.contrib import admin
from django.urls import path, include
from craft_common.views import HealthCheckView

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('admin/auth/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('auth/', include('social_django.urls', namespace='social')),
    path('internal/', include('accounts.internal_urls')),
    path('admin-api/', include('accounts.admin_urls')),
    path('health/', HealthCheckView.as_view(), name='health_check'),
]


