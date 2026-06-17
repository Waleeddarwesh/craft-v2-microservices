from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from django.conf import settings
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf.urls.i18n import i18n_patterns

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)

schema_view = get_schema_view(
    openapi.Info(
        title="Craft API",
        default_version='v1',
        description="API documentation for Craft application",
        terms_of_service="https://www.example.com/policies/terms/",
        contact=openapi.Contact(email="Waleeddarwesh2002@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(IsSuperUser,),
    authentication_classes=(SessionAuthentication, JWTAuthentication,),
)

from django.conf.urls.i18n import i18n_patterns

from admin_api.views import dashboard_view

from django.views.generic import RedirectView

def check_docs_token(view_func):
    def wrapped_view(request, *args, **kwargs):
        # Allow access only if logged into Django Admin as superuser via Session
        if not request.user.is_authenticated or not request.user.is_superuser:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You must be authenticated as a superuser to access the API documentation.")
            
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

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='index'),
    path('docs/', check_docs_token(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
    path('admin/', admin.site.urls),


    # Admin API & Dashboard
    path('admin-api/', include('admin_api.urls')),
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
