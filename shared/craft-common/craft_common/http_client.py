import requests
from typing import Dict, Any, Optional, List
import logging
from urllib.parse import urljoin
import time
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

class CircuitBreakerOpen(Exception):
    pass

class InternalHTTPClient:
    """
    HTTP client for service-to-service internal communication.
    Automatically forwards X-Request-ID and authentication headers if provided.
    Includes retry logic and a basic circuit breaker.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        # Internal timeout should be short to avoid cascading failures
        self.timeout = 5.0
        
        # Retry settings
        self.max_retries = 3
        self.backoff_factor = 0.5
        
        # Circuit breaker settings
        self.failure_threshold = 5
        self.failure_count = 0
        self.circuit_open = False
        self.circuit_open_time = 0
        self.reset_timeout = 60  # seconds

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None, 
                        request_id: Optional[str] = None, 
                        jwt_token: Optional[str] = None) -> Dict[str, str]:
        req_headers = headers or {}
        if request_id:
            req_headers['X-Request-ID'] = request_id
        if jwt_token:
            req_headers['Authorization'] = f"Bearer {jwt_token}"
        req_headers['X-Internal-Secret'] = 'super-secret-internal-key'
        req_headers['Host'] = 'internal-service'
        return req_headers

    def _check_circuit(self):
        if self.circuit_open:
            if time.time() - self.circuit_open_time > self.reset_timeout:
                # Half-open state
                self.circuit_open = False
                logger.info(f"Circuit breaker for {self.base_url} half-open, testing...")
            else:
                raise CircuitBreakerOpen(f"Circuit breaker is open for {self.base_url}")

    def _record_success(self):
        if self.failure_count > 0:
            logger.info(f"Circuit breaker for {self.base_url} reset after success.")
        self.failure_count = 0
        self.circuit_open = False

    def _record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self.circuit_open_time = time.time()
            logger.warning(f"Circuit breaker opened for {self.base_url} after {self.failure_count} failures")

    def _execute_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        self._check_circuit()
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                self._record_success()
                return response
            except RequestException as e:
                last_exception = e
                # Don't retry client errors (4xx)
                if hasattr(e, 'response') and e.response is not None and 400 <= e.response.status_code < 500:
                    self._record_failure() # still record it as a failure for circuit breaker? Maybe not 4xx
                    raise
                
                logger.warning(f"Internal HTTP {method} to {url} failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.backoff_factor * (2 ** attempt))
        
        self._record_failure()
        logger.error(f"Internal HTTP {method} to {url} failed after {self.max_retries} retries: {last_exception}")
        raise last_exception
        req_headers = headers or {}
        if request_id:
            req_headers['X-Request-ID'] = request_id
        if jwt_token:
            req_headers['Authorization'] = f"Bearer {jwt_token}"
        req_headers['X-Internal-Secret'] = 'super-secret-internal-key'
        req_headers['Host'] = 'internal-service'
        return req_headers

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, 
            headers: Optional[Dict[str, str]] = None, 
            request_id: Optional[str] = None, 
            jwt_token: Optional[str] = None) -> requests.Response:
        url = urljoin(self.base_url, path)
        req_headers = self._prepare_headers(headers, request_id, jwt_token)
        return self._execute_with_retry('GET', url, params=params, headers=req_headers)

    def post(self, path: str, json_data: Optional[Dict[str, Any]] = None, 
             headers: Optional[Dict[str, str]] = None, 
             request_id: Optional[str] = None, 
             jwt_token: Optional[str] = None) -> requests.Response:
        url = urljoin(self.base_url, path)
        req_headers = self._prepare_headers(headers, request_id, jwt_token)
        return self._execute_with_retry('POST', url, json=json_data, headers=req_headers)

    def put(self, path: str, json_data: Optional[Dict[str, Any]] = None, 
            headers: Optional[Dict[str, str]] = None, 
            request_id: Optional[str] = None, 
            jwt_token: Optional[str] = None) -> requests.Response:
        url = urljoin(self.base_url, path)
        req_headers = self._prepare_headers(headers, request_id, jwt_token)
        return self._execute_with_retry('PUT', url, json=json_data, headers=req_headers)

    def patch(self, path: str, json_data: Optional[Dict[str, Any]] = None, 
              headers: Optional[Dict[str, str]] = None, 
              request_id: Optional[str] = None, 
              jwt_token: Optional[str] = None) -> requests.Response:
        url = urljoin(self.base_url, path)
        req_headers = self._prepare_headers(headers, request_id, jwt_token)
        return self._execute_with_retry('PATCH', url, json=json_data, headers=req_headers)

    def delete(self, path: str, 
               headers: Optional[Dict[str, str]] = None, 
               request_id: Optional[str] = None, 
               jwt_token: Optional[str] = None) -> requests.Response:
        url = urljoin(self.base_url, path)
        req_headers = self._prepare_headers(headers, request_id, jwt_token)
        return self._execute_with_retry('DELETE', url, headers=req_headers)
        
    def bulk_lookup(self, path: str, ids: List[int],
                    headers: Optional[Dict[str, str]] = None, 
                    request_id: Optional[str] = None, 
                    jwt_token: Optional[str] = None) -> requests.Response:
        """
        Convenience method for bulk lookups. Expects the endpoint to accept {"ids": [1, 2, 3]}
        """
        return self.post(path, json_data={"ids": ids}, headers=headers, request_id=request_id, jwt_token=jwt_token)
