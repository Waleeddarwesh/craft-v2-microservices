import uuid
import contextvars

_request_id_ctx_var = contextvars.ContextVar('request_id', default=None)

def get_request_id():
    return _request_id_ctx_var.get()

class RequestIDMiddleware:
    """
    Middleware to ensure every request has an X-Request-ID.
    If the client sends one, it is preserved. Otherwise, a new UUID is generated.
    The ID is also added to the response headers.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID')
        if not request_id:
            request_id = str(uuid.uuid4())
            
        request.request_id = request_id
        _request_id_ctx_var.set(request_id)

        # Proceed with the request
        response = self.get_response(request)

        # Add the Request ID to the response headers
        response['X-Request-ID'] = request_id
        return response
