"""HTTP client for the MillionScan public API.

The :class:`Client` owns one ``httpx.Client`` and exposes the three
read-only REST surfaces the public API ships today:

* :meth:`Client.leaderboard` — curated trader leaderboard
* :meth:`Client.positions`   — currently-open positions for one trader
* :meth:`Client.trades`      — paginated trade history for one trader

Authentication is via the ``Authorization: Bearer <key>`` header. Get
a key at https://millionscan.com/developers and pass it as
``api_key=`` or set ``MILLIONSCAN_API_KEY`` in your environment.

A WebSocket event stream is exposed at ``/api/public/v1/events``; the
SDK ships REST today and the streaming wrapper lands in a follow-up
release. Until then, the Cookbook (https://millionscan.com/cookbook)
shows how to subscribe directly with ``httpx-ws`` or ``websockets``.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterator, Literal, Optional

import httpx

from millionscan.exceptions import (
    APIError,
    AuthError,
    NotFoundError,
    RateLimitError,
)
from millionscan.models import (
    LeaderboardResponse,
    PositionsResponse,
    TradesResponse,
)


DEFAULT_BASE_URL = "https://millionscan.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
USER_AGENT = "millionscan-python/0.1.0"

SortBy = Literal["score", "roi_30d", "pnl_30d", "win_rate", "account_value"]
SortOrder = Literal["asc", "desc"]
Tier = Literal["featured", "active", "advanced"]


class Client:
    """Synchronous HTTP client for the MillionScan public API.

    Parameters
    ----------
    api_key:
        Bearer key issued at https://millionscan.com/developers. When
        omitted, the constructor reads ``MILLIONSCAN_API_KEY`` from
        the environment. Calls without a key raise :class:`AuthError`
        on the first request.
    base_url:
        API root. Override only for self-hosted deployments. Defaults
        to ``https://millionscan.com``.
    timeout:
        Per-request timeout in seconds. Default 30 s — comfortable for
        the leaderboard endpoint, well above the typical 200-400 ms
        response envelope.
    max_retries:
        How many times to retry on transient transport / 5xx / 429
        responses before raising. Default 3. Set to ``0`` to disable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self._api_key = api_key or os.environ.get("MILLIONSCAN_API_KEY")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max(0, int(max_retries))
        self._http = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": USER_AGENT},
        )

    # -- Lifecycle ----------------------------------------------------

    def close(self) -> None:
        """Close the underlying connection pool."""
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    # -- Endpoints ----------------------------------------------------

    def leaderboard(
        self,
        *,
        tier: Tier = "featured",
        page: int = 1,
        page_size: int = 50,
        sort_by: SortBy = "score",
        sort_order: SortOrder = "desc",
    ) -> LeaderboardResponse:
        """Curated trader leaderboard.

        See :class:`LeaderboardResponse` for the full row shape. The
        default ``tier="featured"`` returns the verified, criteria-met
        curation pool — the highest-signal subset for downstream
        analytical workflows.
        """
        params: Dict[str, Any] = {
            "tier": tier,
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        payload = self._get("/api/public/v1/leaderboard", params=params)
        return LeaderboardResponse.model_validate(payload)

    def positions(self, public_id: str) -> PositionsResponse:
        """All currently-open positions held by a single trader.

        ``public_id`` is the ``#XXXXX`` identifier returned by
        :meth:`leaderboard`. Both ``"77271"`` and ``"#77271"`` are
        accepted; the leading hash is stripped before the request.
        """
        pid = _normalize_public_id(public_id)
        payload = self._get(f"/api/public/v1/traders/{pid}/positions")
        return PositionsResponse.model_validate(payload)

    def trades(
        self,
        public_id: str,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> TradesResponse:
        """Paginated trade history for a single trader, newest first.

        API-key callers receive the full history (no day-window cap).
        Iterate :meth:`iter_trades` if you want every event without
        managing pagination yourself.
        """
        pid = _normalize_public_id(public_id)
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        payload = self._get(
            f"/api/public/v1/traders/{pid}/trades", params=params,
        )
        return TradesResponse.model_validate(payload)

    def iter_trades(
        self,
        public_id: str,
        *,
        page_size: int = 100,
    ) -> Iterator[Any]:
        """Yield every trade for ``public_id`` across all pages.

        Convenience helper around :meth:`trades`. Stops the moment a
        page comes back shorter than ``page_size`` (the natural EOF
        signal in the v1 paging contract).
        """
        page = 1
        while True:
            batch = self.trades(public_id, page=page, page_size=page_size)
            for trade in batch.trades:
                yield trade
            if len(batch.trades) < page_size:
                return
            page += 1

    # -- Internals ----------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        if not self._api_key:
            raise AuthError(
                "API key not set. Pass api_key=... to Client(...) or "
                "export MILLIONSCAN_API_KEY=msk_live_... in your env. "
                "Issue a key at https://millionscan.com/settings#api.",
                status_code=401,
            )
        return {"Authorization": f"Bearer {self._api_key}"}

    def _get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        attempt = 0
        last_error: Optional[Exception] = None
        while attempt <= self._max_retries:
            try:
                response = self._http.get(
                    path, params=params, headers=self._headers(),
                )
            except httpx.TransportError as exc:
                last_error = exc
                if attempt == self._max_retries:
                    raise
                _sleep_backoff(attempt)
                attempt += 1
                continue

            if response.status_code < 400:
                return response.json()

            self._raise_for_status(response, attempt=attempt)
            attempt += 1

        # Defensive: the loop above either returns or raises. Reaching
        # here means we exhausted retries on a recoverable transport
        # failure with no last-success path.
        if last_error is not None:
            raise last_error
        raise APIError("retry budget exhausted", status_code=0)

    def _raise_for_status(self, response: httpx.Response, *, attempt: int) -> None:
        status = response.status_code
        try:
            payload = response.json()
        except ValueError:
            payload = None
        message = _extract_message(payload) or response.text or response.reason_phrase

        if status == 401:
            raise AuthError(message, status_code=status, payload=payload)
        if status == 404:
            raise NotFoundError(message, status_code=status, payload=payload)
        if status == 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            if attempt < self._max_retries:
                _sleep_backoff(attempt, hint=retry_after)
                return
            raise RateLimitError(
                message,
                status_code=status,
                payload=payload,
                retry_after=retry_after,
            )
        if 500 <= status < 600 and attempt < self._max_retries:
            _sleep_backoff(attempt)
            return
        raise APIError(message, status_code=status, payload=payload)


def _normalize_public_id(public_id: str) -> str:
    pid = public_id.strip()
    if pid.startswith("#"):
        pid = pid[1:]
    if not pid:
        raise ValueError("public_id must not be empty")
    return pid


def _extract_message(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("detail", "message", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _sleep_backoff(attempt: int, *, hint: Optional[float] = None) -> None:
    if hint is not None and hint > 0:
        time.sleep(min(hint, 30.0))
        return
    delay = min(0.5 * (2**attempt), 8.0)
    time.sleep(delay)
