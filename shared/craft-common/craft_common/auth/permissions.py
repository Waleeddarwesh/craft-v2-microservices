from functools import wraps
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

class HasRole(BasePermission):
    """
    Allows access only to users with at least one of the specific roles.
    Assumes the API Gateway has validated the JWT and injected the 'X-User-Roles' header.
    """
    def __init__(self, *required_roles: str):
        # Store as lowercase for case-insensitive matching
        self.required_roles = [r.lower() for r in required_roles]

    def has_permission(self, request, view):
        # Allow checking either X-User-Roles header (if API gateway injected)
        # OR check request.user.roles (if JWT was decoded directly by the microservice)
        roles_header = request.headers.get('X-User-Roles', '')
        roles = [role.strip().lower() for role in roles_header.split(',') if role.strip()]
        
        if not roles and hasattr(request.user, 'roles'):
            roles = [r.lower() for r in request.user.roles]
        elif not roles and hasattr(request.user, 'payload'):
            roles = [r.lower() for r in request.user.payload.get('roles', [])]
        elif not roles and getattr(request.user, 'is_staff', False) and 'admin' in self.required_roles:
            # Fallback for real user objects in auth-service
            roles = ['admin']
            
        # Check if user has ANY of the required roles
        if any(req_role in roles for req_role in self.required_roles):
            return True
            
        logger.warning(f"Access denied for user {getattr(request.user, 'id', 'Unknown')}. Required roles: {self.required_roles}, Found: {roles}")
        return False
        
    def __call__(self, *args, **kwargs):
        return self

def require_role(role_name: str):
    """
    Decorator for function-based views to require a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            roles_header = request.headers.get('X-User-Roles', '')
            roles = [role.strip() for role in roles_header.split(',') if role.strip()]
            
            if not roles and hasattr(request.user, 'roles'):
                roles = request.user.roles
            elif not roles and hasattr(request.user, 'payload'):
                roles = request.user.payload.get('roles', [])
            elif not roles and getattr(request.user, 'is_staff', False) and role_name == 'admin':
                roles = ['admin']
                
            if role_name not in roles:
                raise PermissionDenied(f"You do not have the required role: {role_name}")
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
