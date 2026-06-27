"""
Admin API Views — Dashboard backend endpoints.
Refactored to Proxy-Only Architecture (Phase 5).
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from craft_common.api_clients import order_client, catalog_client, payment_client, auth_client, platform_client
from .dashboard_config import get_user_dashboard_modules, get_user_dashboard_widgets

class DashboardIdentityView(APIView):
    permission_classes = [] 
    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({'error': 'Unauthorized'}, status=403)
        user = request.user
        return Response({
            'user': {'id': user.id, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name, 'is_superuser': user.is_superuser},
            'permissions': list(user.get_all_permissions()),
            'modules': get_user_dashboard_modules(user),
            'widgets': get_user_dashboard_widgets(user),
            'environment': 'Production'
        })

from django.http import HttpResponse
from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)

class GenericProxyView(APIView):
    # Enforce authentication and authorization for all proxied endpoints
    permission_classes = [permissions.IsAuthenticated, IsSuperUser] 
    
    def __init__(self, client=None, downstream_prefix=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client
        self.downstream_prefix = downstream_prefix

    def proxy_request(self, request, *args, **kwargs):
        if not self.client:
            return Response({'error': 'No proxy client configured'}, status=500)
            
        path = request.path
        
        # Extract JWT from Authorization header
        auth_header = request.headers.get('Authorization', '')
        jwt_token = auth_header.split('Bearer ')[1] if 'Bearer ' in auth_header else None
        
        # Pass query params and body
        params = request.GET.dict()
        json_data = request.data if request.method in ['POST', 'PUT', 'PATCH'] else None
        
        method = request.method.lower()
        try:
            func = getattr(self.client, method)
            # Send the request
            res = func(path, params=params, json_data=json_data, jwt_token=jwt_token)
            
            # Create Django HttpResponse from requests.Response
            return HttpResponse(
                content=res.content,
                status=res.status_code,
                content_type=res.headers.get('Content-Type', 'application/json')
            )
        except Exception as e:
            return Response({'error': f'Proxy error: {str(e)}'}, status=502)

    def get(self, request, *args, **kwargs): return self.proxy_request(request, *args, **kwargs)
    def post(self, request, *args, **kwargs): return self.proxy_request(request, *args, **kwargs)
    def put(self, request, *args, **kwargs): return self.proxy_request(request, *args, **kwargs)
    def patch(self, request, *args, **kwargs): return self.proxy_request(request, *args, **kwargs)
    def delete(self, request, *args, **kwargs): return self.proxy_request(request, *args, **kwargs)

