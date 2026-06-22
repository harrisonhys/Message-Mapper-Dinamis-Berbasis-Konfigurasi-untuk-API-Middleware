"""engine/adapter.py — Partner Adapter."""
import httpx, time
from typing import Any

class PartnerAdapter:
    def __init__(self, base_url: str, path: str, method: str = "POST", api_key: str | None = None, api_key_header: str = "X-API-Key", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.path = path if path.startswith("/") else f"/{path}"
        self.method = method.upper()
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.timeout = timeout

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key: headers[self.api_key_header] = self.api_key
        return headers

    def send(self, payload: dict) -> dict[str, Any]:
        url = f"{self.base_url}{self.path}"
        headers = self._build_headers()
        try:
            start = time.perf_counter()
            with httpx.Client(timeout=self.timeout) as client:
                if self.method == "POST": resp = client.post(url, json=payload, headers=headers)
                elif self.method == "PUT": resp = client.put(url, json=payload, headers=headers)
                elif self.method == "PATCH": resp = client.patch(url, json=payload, headers=headers)
                else: resp = client.get(url, headers=headers)
            latency_ms = (time.perf_counter() - start) * 1000
            response_body = {}
            if resp.content:
                try: response_body = resp.json()
                except Exception: response_body = {"raw_text": resp.text[:500]}
            return {"status_code": resp.status_code, "response_body": response_body, "success": resp.is_success, "latency_ms": round(latency_ms, 2)}
        except httpx.RequestError as exc:
            return {"status_code": 0, "response_body": {"error": str(exc)}, "success": False, "latency_ms": 0}

def build_adapter_from_partner(partner, endpoint) -> PartnerAdapter:
    return PartnerAdapter(base_url=partner.base_url or "http://localhost:9000", path=endpoint.path, method=endpoint.method, api_key=partner.api_key)
