import os
from craft_common.http_client import InternalHTTPClient

# In a real environment, these URLs would be fetched from environment variables.
# Here we provide default fallback URLs matching our docker-compose internal DNS names.
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_INTERNAL_URL", "http://auth_service:8001")
CATALOG_SERVICE_URL = os.environ.get("CATALOG_SERVICE_INTERNAL_URL", "http://catalog_service:8002")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_INTERNAL_URL", "http://order_service:8003")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_INTERNAL_URL", "http://payment_service:8004")
PLATFORM_SERVICE_URL = os.environ.get("PLATFORM_SERVICE_INTERNAL_URL", "http://platform_service:8005")

auth_client = InternalHTTPClient(base_url=AUTH_SERVICE_URL)
catalog_client = InternalHTTPClient(base_url=CATALOG_SERVICE_URL)
order_client = InternalHTTPClient(base_url=ORDER_SERVICE_URL)
payment_client = InternalHTTPClient(base_url=PAYMENT_SERVICE_URL)
platform_client = InternalHTTPClient(base_url=PLATFORM_SERVICE_URL)
