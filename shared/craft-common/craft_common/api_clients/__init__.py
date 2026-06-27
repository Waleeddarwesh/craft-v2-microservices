import os
from craft_common.http_client import InternalHTTPClient

# In a real environment, these URLs would be fetched from environment variables.
# Here we provide default fallback URLs matching our docker-compose internal DNS names.
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_INTERNAL_URL", "http://auth-service:8001")
CATALOG_SERVICE_URL = os.environ.get("CATALOG_SERVICE_INTERNAL_URL", "http://catalog-service:8002")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_INTERNAL_URL", "http://order-service:8003")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_INTERNAL_URL", "http://payment-service:8004")
PLATFORM_SERVICE_URL = os.environ.get("PLATFORM_SERVICE_INTERNAL_URL", "http://platform-service:8005")
REPORTING_SERVICE_URL = os.environ.get("REPORTING_SERVICE_INTERNAL_URL", "http://reporting-service:8007")
REALTIME_SERVICE_URL = os.environ.get("REALTIME_SERVICE_INTERNAL_URL", "http://realtime-service:8008")

auth_client = InternalHTTPClient(base_url=AUTH_SERVICE_URL)
catalog_client = InternalHTTPClient(base_url=CATALOG_SERVICE_URL)
order_client = InternalHTTPClient(base_url=ORDER_SERVICE_URL)
payment_client = InternalHTTPClient(base_url=PAYMENT_SERVICE_URL)
platform_client = InternalHTTPClient(base_url=PLATFORM_SERVICE_URL)
reporting_client = InternalHTTPClient(base_url=REPORTING_SERVICE_URL)
realtime_client = InternalHTTPClient(base_url=REALTIME_SERVICE_URL)
