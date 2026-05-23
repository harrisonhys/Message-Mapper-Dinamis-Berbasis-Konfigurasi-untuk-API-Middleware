"""
engine/adapter.py — Partner Adapter
Menyesuaikan endpoint, headers, dan pengiriman ke partner API.
"""
import httpx
from typing import Any


class PartnerAdapter:
    """Adapter untuk mengirim payload ke partner API."""

    def __init__(
        self,
        base_url: str,
        path: str,
        method: str = "POST",
        api_key: str | None = None,
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.path = path if path.startswith("/") else f"/{path}"
        self.method = method.upper()
        self.api_key = api_key
        self.timeout = timeout

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def send(self, payload: dict) -> dict[str, Any]:
        """
        Kirim payload ke partner API.

        Returns dict:
          status_code, response_body, success
        """
        url = f"{self.base_url}{self.path}"
        headers = self._build_headers()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                if self.method == "POST":
                    resp = client.post(url, json=payload, headers=headers)
                elif self.method == "PUT":
                    resp = client.put(url, json=payload, headers=headers)
                elif self.method == "PATCH":
                    resp = client.patch(url, json=payload, headers=headers)
                else:
                    resp = client.get(url, headers=headers)

            return {
                "status_code": resp.status_code,
                "response_body": resp.json() if resp.content else {},
                "success": resp.is_success,
            }
        except httpx.RequestError as exc:
            return {
                "status_code": 0,
                "response_body": {"error": str(exc)},
                "success": False,
            }


def build_adapter_from_partner(partner, endpoint) -> PartnerAdapter:
    """Factory helper dari ORM objects."""
    return PartnerAdapter(
        base_url=partner.base_url or "http://localhost:9000",
        path=endpoint.path,
        method=endpoint.method,
        api_key=partner.api_key,
    )
