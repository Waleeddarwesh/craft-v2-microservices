import jwt
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

security = HTTPBearer(auto_error=False)

def get_current_user_id(request: Request, token: HTTPAuthorizationCredentials = Security(security)) -> int:
    """
    Extract user_id from the JWT token.
    FastAPI will automatically look for the Authorization: Bearer <token> header.
    """
    if not token:
        # Check query params for websockets
        token_str = request.query_params.get("token")
        if not token_str:
            raise HTTPException(status_code=401, detail="Not authenticated")
    else:
        token_str = token.credentials

    if not settings.jwt_public_key:
        raise HTTPException(status_code=500, detail="JWT public key not configured")

    try:
        payload = jwt.decode(token_str, settings.jwt_public_key, algorithms=["RS256"])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
