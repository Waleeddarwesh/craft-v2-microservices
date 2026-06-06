import jwt
from typing import Dict, Any
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

def validate_jwt(token: str, public_key: str = None) -> Dict[str, Any]:
    """
    Validates an RS256 JWT token using a public key.
    If public_key is not provided, it falls back to settings.JWT_PUBLIC_KEY.
    """
    key = public_key or getattr(settings, 'JWT_PUBLIC_KEY', None)
    if not key:
        raise AuthenticationFailed("JWT public key is not configured.")

    try:
        # We only expect the access token payload
        payload = jwt.decode(token, key, algorithms=["RS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired.")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token.")
