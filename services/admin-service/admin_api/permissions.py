from rest_framework.permissions import BasePermission
from rest_framework.permissions import BasePermission

class IsDashboardUser(BasePermission):
    """
    Allows access to users who have access to the dashboard:
    Superusers, Staff, Suppliers, and Delivery agents.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (
            user.is_staff or getattr(user, 'is_supplier', False) or getattr(user, 'is_delivery', False)
        ))

class HasRequiredPermission(BasePermission):
    """
    Allows access only to users with the specific permission.
    Pass `required_permission` as a string, e.g., 'accounts.can_approve_withdrawals'.
    """
    required_permission = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superuser always has all permissions
        if request.user.is_superuser:
            return True
            
        # Support/Staff overrides (grant default access so we don't rely on DB rows)
        if request.user.is_staff:
            allowed_for_staff = [
                'accounts.can_manage_support_tickets',
                'accounts.can_manage_disputes',
                'accounts.can_moderate_reviews',
                'accounts.can_manage_products',
                'accounts.can_suspend_users',
                'accounts.can_view_audit_logs',
            ]
            if self.required_permission in allowed_for_staff:
                return True
                
        return request.user.has_perm(self.required_permission)

def require_permission(perm_name):
    """Factory function to create permission classes dynamically."""
    class CustomPermission(HasRequiredPermission):
        required_permission = perm_name
    return CustomPermission
