class FixHostHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        print('RUNNING FIX HOST HEADER MIDDLEWARE'); request.META['HTTP_HOST'] = 'localhost'
        return self.get_response(request)

