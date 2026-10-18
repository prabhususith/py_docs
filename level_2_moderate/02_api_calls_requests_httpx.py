r"""
HTTP Client Transport: Synchronous (Requests) & Asynchronous (HTTPX)
===================================================================
Description: Enterprise HTTP client architectures contrasting synchronous blocking I/O
             with session connection pooling (`requests`) against modern asynchronous
             event-driven transport with HTTP/2 support (`httpx`).
Enterprise Mapping:
- `requests.Session`: Direct counterpart to PHP's `GuzzleHttp\Client` and synchronous cURL.
  Maintains an underlying `urllib3` connection pool, keeping TCP sockets alive across requests.
- `httpx.AsyncClient`: Direct counterpart to Node.js / TypeScript `fetch` / `axios` with
  async/await and `Promise.all()` parallel execution. Supports standard ASGI mocking, HTTP/2,
  and connection reuse across coroutines.
- Timeout & Retry Policies: Implements resilient exponential backoff strategies to prevent
  thread pool exhaustion and cascading downstream microservice failure.

Official Documentation References:
- Requests Official Documentation: https://requests.readthedocs.io/en/latest/
- Requests Session & Retries: https://requests.readthedocs.io/en/latest/user/advanced/#session-objects
- HTTPX Official Documentation: https://www.python-httpx.org/
- HTTPX Async Support: https://www.python-httpx.org/async/
"""

from __future__ import annotations

import asyncio
import http.server
import json
import threading
from typing import Any, Final, Sequence
import urllib.parse

import httpx
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==============================================================================
# 1. Production Synchronous HTTP Client (Requests + Session Pooling)
# ==============================================================================
class SynchronousHttpClient:
    """
    Enterprise Synchronous HTTP Client with connection pooling, automatic retries,
    and strict timeout boundaries.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url: str = base_url.rstrip("/")
        self.timeout_seconds: float = timeout_seconds
        self.session: requests.Session = self._build_resilient_session()

    def _build_resilient_session(self) -> requests.Session:
        """
        Configure requests.Session with connection pooling and exponential backoff retry.
        Mirrors Guzzle retry middleware in PHP.
        """
        session = requests.Session()

        # Retry on idempotent HTTP status codes (429 Too Many Requests, 500, 502, 503, 504)
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,  # waits: 0.3s, 0.6s, 1.2s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools to cache
            pool_maxsize=20,  # Max connections per pool
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        session.headers.update(
            {
                "User-Agent": "Enterprise-Python-Worker/1.0",
                "Accept": "application/json",
            }
        )
        return session

    def get_resource(self, endpoint: str, query_params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute typed synchronous GET request with error boundary."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=query_params, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return payload
        except requests.exceptions.HTTPError as http_err:
            print(f"  [ERROR] Synchronous HTTP error: {http_err.response.status_code} - {http_err}")
            raise
        except requests.exceptions.RequestException as req_err:
            print(f"  [ERROR] Synchronous network transport error: {req_err}")
            raise

    def post_resource(self, endpoint: str, json_body: dict[str, Any]) -> dict[str, Any]:
        """Execute typed synchronous POST request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=json_body, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Release underlying socket pool."""
        self.session.close()


# ==============================================================================
# 2. Modern Asynchronous HTTP Client (HTTPX + AsyncIO Concurrency)
# ==============================================================================
class AsynchronousHttpClient:
    """
    Modern Asynchronous HTTP Client for high-throughput non-blocking microservice communication.
    Mirrors Node.js axios / fetch with Promise.all() parallel dispatching.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url: str = base_url.rstrip("/")
        self.timeout: httpx.Timeout = httpx.Timeout(
            timeout=timeout_seconds,
            connect=3.0,
            read=timeout_seconds,
            write=timeout_seconds,
        )
        self.limits: httpx.Limits = httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        )

    async def fetch_parallel_resources(self, resource_ids: Sequence[int]) -> list[dict[str, Any]]:
        """
        Fetch multiple endpoints concurrently using asyncio.gather.
        Node.js equivalent:
          await Promise.all(resourceIds.map(id => client.get(`/items/${id}`)))
        """
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=self.limits,
            headers={"User-Agent": "Enterprise-Async-HTTPX/2.0"},
        ) as client:
            # Create concurrent coroutines
            coros = [client.get(f"/items/{item_id}") for item_id in resource_ids]
            responses = await asyncio.gather(*coros, return_exceptions=False)

            results: list[dict[str, Any]] = []
            for resp in responses:
                resp.raise_for_status()
                results.append(resp.json())

            return results

    async def post_payload(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Execute single asynchronous POST."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post(endpoint, json=data)
            resp.raise_for_status()
            return resp.json()


# ==============================================================================
# Self-Contained Ephemeral Mock HTTP Server for Offline Execution
# ==============================================================================
class _MockTelemetryHttpHandler(http.server.BaseHTTPRequestHandler):
    """In-memory HTTP Server simulating a production microservice backend."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stdout access logging during tests."""
        pass

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path.startswith("/items/"):
            item_id = parsed_url.path.split("/")[-1]
            response_data = {
                "id": int(item_id) if item_id.isdigit() else item_id,
                "status": "ACTIVE",
                "name": f"Enterprise-Item-{item_id}",
                "telemetry": {"latency_ms": 1.2, "region": "us-east-1"},
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        elif parsed_url.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "SERVING"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8"))
        response_data = {
            "ack": True,
            "received_payload": payload,
            "processed_by": "MockGateway/1.0",
        }
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))


# ==============================================================================
# Verification & Self-Executing Diagnostic Suite
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print(" LEVEL 2: 02_API_CALLS_REQUESTS_HTTPX - ENTERPRISE RUNTIME DEMO")
    print("=" * 70)

    # 1. Spin up ephemeral HTTP server on local random port
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _MockTelemetryHttpHandler)
    server_port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base_endpoint = f"http://127.0.0.1:{server_port}"
    print(f"[*] Ephemeral Mock HTTP Server started at {base_endpoint}")

    try:
        # 2. Test Synchronous Requests Client
        print("\n--- 1. Testing Synchronous HTTP (Requests + Session Pooling) ---")
        sync_client = SynchronousHttpClient(base_url=base_endpoint)
        health_resp = sync_client.get_resource("/health")
        print(f"  Sync GET /health -> {health_resp}")
        assert health_resp["status"] == "SERVING"

        post_data = {"deployment_id": "dep_9942", "version": "v2.1.0"}
        post_resp = sync_client.post_resource("/deployments", json_body=post_data)
        print(f"  Sync POST /deployments -> Ack: {post_resp['ack']}")
        assert post_resp["ack"] is True
        sync_client.close()

        # 3. Test Asynchronous HTTPX Client with Concurrent Parallel Dispatch
        print("\n--- 2. Testing Asynchronous HTTP (HTTPX + asyncio.gather) ---")
        async_client = AsynchronousHttpClient(base_url=base_endpoint)

        async def _run_async_tests() -> None:
            # Parallel request simulation: 5 concurrent calls
            item_ids = [101, 102, 103, 104, 105]
            batch_results = await async_client.fetch_parallel_resources(item_ids)
            print(f"  Async Concurrently fetched {len(batch_results)} microservice items:")
            for item in batch_results:
                print(f"    Item #{item['id']}: {item['name']} | Status: {item['status']}")
            assert len(batch_results) == 5

            async_post_resp = await async_client.post_payload(
                "/events", {"event": "USER_LOGIN", "user_id": 42}
            )
            print(f"  Async POST /events -> Ack: {async_post_resp['ack']}")
            assert async_post_resp["ack"] is True

        asyncio.run(_run_async_tests())

    finally:
        # Gracefully shutdown mock server
        server.shutdown()
        server_thread.join(timeout=2.0)
        print("\n[*] Mock HTTP Server terminated cleanly.")

    print("\n" + "=" * 70)
    print("[ALL CHECKS PASSED] 02_api_calls_requests_httpx module executed cleanly.")
    print("=" * 70)
