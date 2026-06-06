from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from .jwt_validator import validate_jwt

class StatelessUser:
    """A dummy user object for services that do not have a User model in their DB."""
    def __init__(self, payload):
        self.id = payload.get("user_id")
        self.is_authenticated = True
        self.payload = payload

    def __str__(self):
        return f"User({self.id})"

class JWTAuthentication(BaseAuthentication):
    """
    Custom DRF Authentication class that validates RS256 JWTs 
    using the public key, without hitting the database.
    """
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')
        elif len(auth) > 2:
            raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

        try:
            token = auth[1].decode()
        except UnicodeError:
            raise AuthenticationFailed('Invalid token header. Token string should not contain invalid characters.')

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        payload = validate_jwt(token)
        
        # In microservices where we don't have the user table, we return a StatelessUser
        # For the auth service, we could return a real User model.
        user = StatelessUser(payload)
        
        return (user, token)
