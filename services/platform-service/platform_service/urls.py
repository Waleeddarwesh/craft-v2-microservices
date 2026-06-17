from craft_common.views import HealthCheckView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
"""
URL configuration for platform_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('admin/platform/', admin.site.urls),
    path('disputes/', include('disputes.urls')),
    path('review/', include('reviews.urls')),
    path('support/', include('support_tickets.urls')),

    path('admin-api/', include('reviews.admin_urls')),
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('review/api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('review/api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

