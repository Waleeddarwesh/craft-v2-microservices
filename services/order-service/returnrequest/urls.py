from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('return-requests', views.ReturnRequestViewSet, basename='return-request')

urlpatterns = [
    path('', include(router.urls)),
]