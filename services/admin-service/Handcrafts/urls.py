from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from django.conf import settings
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf.urls.i18n import i18n_patterns

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)



from django.conf.urls.i18n import i18n_patterns

from admin_api.views import dashboard_view

from django.views.generic import RedirectView

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from accounts.views import admin_profile_settings

def check_docs_token(view_func):
    def wrapped_view(request, *args, **kwargs):
        # Allow access only if logged into Django Admin as superuser via Session
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('/docs/login/?next=' + request.path)
            
        original_user = request.user
        # Get the response from drf_yasg
        response = view_func(request, *args, **kwargs)
        
        # If it's the HTML UI (not the JSON schema), inject the JWT token
        if request.GET.get('format') != 'openapi' and hasattr(response, 'render'):
            response.render()
            
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(original_user)
            # Add roles payload to token for craft_common
            refresh['roles'] = ['admin'] if request.user.is_superuser else []
            access_token = str(refresh.access_token)
            
            html = response.content.decode('utf-8')
            
            inject_js = f"""
            <script>
            window.CRAFT_ACCESS_TOKEN = "{access_token}";
            window.addEventListener('load', function() {{
                var injectToken = function() {{
                    if (window.ui && window.ui.authActions) {{
                        window.ui.authActions.authorize({{
                            Bearer: {{
                                name: "Bearer",
                                schema: {{
                                    type: "apiKey",
                                    in: "header",
                                    name: "Authorization"
                                }},
                                value: "{access_token}"
                            }}
                        }});
                        console.log('JWT Token auto-injected from Admin Session!');
                    }} else {{
                        setTimeout(injectToken, 500);
                    }}
                }};
                injectToken();
            }});
            </script>
            </body>
            """
            html = html.replace('</body>', inject_js)
            response.content = html.encode('utf-8')
            
        return response
    return wrapped_view

from django.contrib.auth.forms import AuthenticationForm

def docs_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        next_url = request.GET.get('next', '/docs/')
        return redirect(next_url)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                login(request, user)
                next_url = request.GET.get('next', '/docs/')
                return redirect(next_url)
            else:
                form.add_error(None, 'You must be a superuser to access the Developer Portal.')
    else:
        form = AuthenticationForm()

    return render(request, 'admin/docs_login.html', {'form': form})

def docs_logout_view(request):
    logout(request)
    return redirect('/docs/login/')

from django.views.generic import TemplateView

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='index'),
    path('admin-schema.json', SpectacularAPIView.as_view(), name='schema-json'),
    path('docs/', check_docs_token(TemplateView.as_view(template_name='admin/central_docs.html')), name='schema-swagger-ui'),
    path('docs/login/', docs_login_view, name='docs-login'),
    path('docs/logout/', docs_logout_view, name='docs-logout'),
    path('admin/profile-settings/', admin_profile_settings, name='admin_profile_settings'),
    path('admin/', admin.site.urls),

    # Admin API & Dashboard
    path('admin-api/', include('admin_api.urls')),
    
    # Workflows & Approvals (Phase 1 & 2)
    path('api/workflows/', include('workflows.urls')),
    path('api/audit/', include('audit_logs.urls')),
    
    # Internal Notifications (Phase 6)
    path('api/notifications-system/', include('notifications.urls')),
    
    # Craft Developer Portal
    path('developer/', include('developer_portal.urls')),

    path('dashboard/', dashboard_view, {'path': 'index.html'}, name='dashboard-login'),
    path('dashboard/<path:path>', dashboard_view, name='dashboard-file'),

    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]

urlpatterns += [
    path('i18n/', include('django.conf.urls.i18n')),
]

from django.urls import re_path
from django.views.static import serve
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
