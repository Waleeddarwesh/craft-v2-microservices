from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

class HealthCheckView(APIView):
    """
    A generic health check endpoint that returns 200 OK.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok", "message": "Service is healthy"})
