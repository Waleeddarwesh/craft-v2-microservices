from craft_common.views import HealthCheckView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
"""
URL configuration for reporting_service project.

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
    path('admin/reporting/', admin.site.urls),
    path('admin-api/', include('admin_api.urls')),

    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('reports/api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('reports/api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
