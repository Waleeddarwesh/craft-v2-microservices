from django.utils.translation import gettext_lazy as _

# Map frontend module keys to required permissions and roles
DASHBOARD_MODULES = [
    {
        "key": "overview",
        "label": _("Overview"),
        "icon": "dashboard",
        "roles": ["is_superuser", "is_supplier", "is_delivery", "is_staff"],
        "permission": None
    },
    {
        "key": "orders",
        "label": _("Orders"),
        "icon": "orders",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_manage_products"
    },
    {
        "key": "products",
        "label": _("Products"),
        "icon": "products",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_manage_products"
    },
    {
        "key": "users",
        "label": _("Users"),
        "icon": "users",
        "roles": ["is_superuser"],
        "permission": "accounts.can_suspend_users"
    },
    {
        "key": "returns",
        "label": _("Return Requests"),
        "icon": "returns",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_manage_disputes"
    },
    {
        "key": "payments",
        "label": _("Payments"),
        "icon": "payments",
        "roles": ["is_superuser"],
        "permission": "accounts.can_view_financial_reports"
    },
    {
        "key": "withdrawals",
        "label": _("Withdrawals"),
        "icon": "wallet",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_approve_withdrawals"
    },
    {
        "key": "courses",
        "label": _("Courses"),
        "icon": "courses",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_manage_courses"
    },
    {
        "key": "reviews",
        "label": _("Reviews"),
        "icon": "reviews",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_moderate_reviews"
    },
    {
        "key": "coupons",
        "label": _("Coupons"),
        "icon": "coupons",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_manage_products"
    },
    {
        "key": "reports",
        "label": _("Reports"),
        "icon": "reports",
        "roles": ["is_superuser", "is_supplier"],
        "permission": "accounts.can_view_financial_reports"
    },
    {
        "key": "notifications",
        "label": _("Notifications"),
        "icon": "notifications",
        "roles": ["is_superuser", "is_supplier", "is_delivery"],
        "permission": None
    },
    {
        "key": "support-tickets",
        "label": _("Support Tickets"),
        "icon": "support",
        "roles": ["is_superuser"],
        "permission": "accounts.can_manage_support_tickets"
    },
    {
        "key": "disputes",
        "label": _("Disputes"),
        "icon": "disputes",
        "roles": ["is_superuser"],
        "permission": "accounts.can_manage_disputes"
    },
    {
        "key": "audit-logs",
        "label": _("Audit Logs"),
        "icon": "audit",
        "roles": ["is_superuser"],
        "permission": "accounts.can_view_audit_logs"
    },
    {
        "key": "fraud-alerts",
        "label": _("Fraud Alerts"),
        "icon": "audit",
        "roles": ["is_superuser"],
        "permission": "accounts.can_view_audit_logs"
    },
    {
        "key": "product-moderation",
        "label": _("Product Moderation"),
        "icon": "products",
        "roles": ["is_superuser"],
        "permission": "accounts.can_manage_products"
    },
    {
        "key": "supplier-performance",
        "label": _("Supplier Performance"),
        "icon": "products",
        "roles": ["is_superuser"],
        "permission": "accounts.can_manage_products"
    },
    {
        "key": "delivery-performance",
        "label": _("Delivery Performance"),
        "icon": "orders",
        "roles": ["is_superuser"],
        "permission": "accounts.can_manage_products"
    },
    {
        "key": "reconciliation",
        "label": _("Financial Reconciliation"),
        "icon": "reports",
        "roles": ["is_superuser"],
        "permission": "accounts.can_view_financial_reports"
    },
    {
        "key": "settings",
        "label": _("Settings"),
        "icon": "settings",
        "roles": ["is_superuser", "is_supplier", "is_delivery", "is_staff"],
        "permission": None
    }
]

# Map dashboard widgets to roles/permissions
DASHBOARD_WIDGETS = {
    "total_revenue": {"roles": ["is_superuser"], "permission": "accounts.can_view_financial_reports"},
    "total_orders": {"roles": ["is_superuser", "is_supplier"], "permission": "accounts.can_manage_products"},
    "active_users": {"roles": ["is_superuser"], "permission": "accounts.can_suspend_users"},
    "pending_returns": {"roles": ["is_superuser", "is_supplier"], "permission": "accounts.can_manage_disputes"},
    "products_in_stock": {"roles": ["is_superuser", "is_supplier"], "permission": "accounts.can_manage_products"},
    "pending_withdrawals": {"roles": ["is_superuser"], "permission": "accounts.can_approve_withdrawals"},
    "revenue_chart": {"roles": ["is_superuser", "is_supplier"], "permission": "accounts.can_view_financial_reports"},
    "status_chart": {"roles": ["is_superuser", "is_supplier"], "permission": "accounts.can_manage_products"},
}

def get_user_dashboard_modules(user):
    """Returns a list of module keys the user is authorized to see."""
    if not user.is_authenticated:
        return []
        
    allowed_modules = []
    for module in DASHBOARD_MODULES:
        # Superuser sees everything
        if user.is_superuser:
            allowed_modules.append(module)
            continue
            
        # Check explicit permission
        if module["permission"] and user.has_perm(module["permission"]):
            allowed_modules.append(module)
            continue
            
        # Check role-based fallback
        if "is_supplier" in module["roles"] and getattr(user, 'is_supplier', False):
            allowed_modules.append(module)
            continue
            
        if "is_delivery" in module["roles"] and getattr(user, 'is_delivery', False):
            allowed_modules.append(module)
            continue
            
        if "is_staff" in module["roles"] and getattr(user, 'is_staff', False):
            allowed_modules.append(module)
            continue
            
    return allowed_modules

def get_user_dashboard_widgets(user):
    """Returns a list of widget keys the user is authorized to see."""
    if not user.is_authenticated:
        return []
        
    if user.is_superuser:
        return list(DASHBOARD_WIDGETS.keys())
        
    allowed_widgets = []
    for widget_key, config in DASHBOARD_WIDGETS.items():
        if config["permission"] and user.has_perm(config["permission"]):
            allowed_widgets.append(widget_key)
            continue
            
        if "is_supplier" in config["roles"] and getattr(user, 'is_supplier', False):
            allowed_widgets.append(widget_key)
            continue
            
        if "is_delivery" in config["roles"] and getattr(user, 'is_delivery', False):
            allowed_widgets.append(widget_key)
            continue
            
        if "is_staff" in config["roles"] and getattr(user, 'is_staff', False):
            allowed_widgets.append(widget_key)
            continue
            
    return allowed_widgets
