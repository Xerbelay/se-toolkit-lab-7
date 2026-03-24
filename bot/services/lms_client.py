from __future__ import annotations

from dataclasses import dataclass

import httpx

from config import get_settings


class BackendError(Exception):
    """User-friendly backend communication error."""

    pass


@dataclass
class LMSClient:
    base_url: str
    api_key: str
    timeout: float = 10.0

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _format_http_error(self, response: httpx.Response) -> str:
        status = response.status_code
        reason = response.reason_phrase or "Unknown error"

        if status == 502:
            return "Backend error: HTTP 502 Bad Gateway. The backend service may be down."

        if status == 401:
            return "Backend error: HTTP 401 Unauthorized. Check LMS_API_KEY."

        if status == 403:
            return "Backend error: HTTP 403 Forbidden. Access was denied by the backend."

        if status == 404:
            return "Backend error: HTTP 404 Not Found. Check the backend URL."

        return f"Backend error: HTTP {status} {reason}."

    def _format_request_error(self, exc: httpx.RequestError) -> str:
        message = str(exc).strip()

        if "Connection refused" in message or "[Errno 111]" in message:
            return (
                "Backend error: connection refused "
                f"({self.base_url}). Check that the services are running."
            )

        if "Name or service not known" in message:
            return (
                "Backend error: could not resolve backend host "
                f"({self.base_url}). Check LMS_API_BASE_URL."
            )

        return f"Backend error: {message}"

    def get_json(self, path: str, params: dict | None = None):
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.headers, params=params)
                if response.status_code >= 400:
                    raise BackendError(self._format_http_error(response))
                return response.json()
        except httpx.RequestError as exc:
            raise BackendError(self._format_request_error(exc)) from exc


def get_lms_client() -> LMSClient:
    settings = get_settings()
    return LMSClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key,
    )
