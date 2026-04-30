"""MillionScan SDK exceptions.

Hierarchy:

    MillionScanError              — base class for every SDK-raised error
    ├── APIError                  — server responded but not 2xx
    │   ├── AuthError             — 401 (invalid / missing API key)
    │   ├── NotFoundError         — 404 (trader / endpoint not found)
    │   └── RateLimitError        — 429 (rate limit hit)
    └── (transport / parse failures bubble up as httpx / pydantic exceptions)

Catch `MillionScanError` to handle every SDK-originated error in one
branch; catch the more specific subclasses when you want to react
differently to auth vs rate-limit vs other failures.
"""

from __future__ import annotations

from typing import Any


class MillionScanError(Exception):
    """Base class for every error raised by the MillionScan SDK."""


class APIError(MillionScanError):
    """The server returned a non-2xx response.

    Attributes
    ----------
    status_code:
        HTTP status code returned by the API.
    payload:
        Parsed JSON body of the error response when one exists, else
        ``None``. Useful for surfacing the server's ``detail`` string
        to your own logs.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        payload: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        base = super().__str__()
        return f"{base} [HTTP {self.status_code}]"


class AuthError(APIError):
    """The API key is missing, invalid, or has lapsed (HTTP 401)."""


class NotFoundError(APIError):
    """The requested resource was not found (HTTP 404)."""


class RateLimitError(APIError):
    """Per-key rate limit exceeded (HTTP 429).

    Attributes
    ----------
    retry_after:
        Seconds the server suggests waiting before retrying when the
        ``Retry-After`` header is present, else ``None``.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        payload: Any | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, payload=payload)
        self.retry_after = retry_after
