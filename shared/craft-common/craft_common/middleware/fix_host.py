class FixHostHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        request.META['HTTP_HOST'] = 'localhost'
        return self.get_response(request)


import django.http.request
import re
django.http.request.host_validation_re = re.compile(r'^[a-zA-Z0-9_.-]+(:[0-9]+)?$')


class BypassHostCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        request.get_host = lambda: 'localhost'
        return self.get_response(request)

