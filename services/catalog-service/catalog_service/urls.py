from craft_common.views import HealthCheckView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/catalog/", admin.site.urls),
    path("product/", include("products.urls")),
    path("course/", include("course.urls")),
    path("internal/", include("internal.urls")),
    path("admin-api/", include("products.admin_urls")),
    path("admin-api/", include("course.admin_urls")),
    path("health/", HealthCheckView.as_view(), name="health_check"),
    path('product/api/schema/', SpectacularAPIView.as_view(), name="schema"),
    path('product/api/docs/', SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
