from django.core.cache import cache
from craft_common.http_client import InternalHTTPClient
from pydantic import BaseModel
from typing import Optional, List

class UserProfile(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    roles: List[str] = []

class UserProxy:
    """
    A service layer to fetch user data from the Auth Service.
    Includes caching to prevent excessive internal HTTP calls.
    """
    
    @classmethod
    def get_user(cls, user_id: int) -> Optional[UserProfile]:
        cache_key = f"user_profile_{user_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return UserProfile(**cached_data)
            
        client = InternalHTTPClient("http://auth_service:8001")
        # In a real setup, we should pass an internal secret or valid JWT token
        response = client.get(f"/internal/users/{user_id}/", headers={"X-Internal-Secret": "super-secret-internal-key"})
        
        if response.status_code == 200:
            data = response.json()
            cache.set(cache_key, data, timeout=300) # Cache for 5 mins
            return UserProfile(**data)
            
        return None

    @classmethod
    def bulk_get_users(cls, user_ids: List[int]) -> List[UserProfile]:
        client = InternalHTTPClient("http://auth_service:8001")
        response = client.post("/internal/users/bulk-lookup/", json={"ids": user_ids}, headers={"X-Internal-Secret": "super-secret-internal-key"})
        
        if response.status_code == 200:
            users_data = response.json()
            profiles = []
            for data in users_data:
                profiles.append(UserProfile(**data))
                # Update cache for individual items too
                cache_key = f"user_profile_{data['id']}"
                cache.set(cache_key, data, timeout=300)
            return profiles
            
        return []

    @classmethod
    def invalidate_cache(cls, user_id: int):
        cache_key = f"user_profile_{user_id}"
        cache.delete(cache_key)
