"""Unit tests for the synchronous Client.

Every test mocks the HTTP transport with respx, so no live API
traffic happens during `pytest`.
"""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from millionscan import (
    APIError,
    AuthError,
    Client,
    NotFoundError,
    RateLimitError,
)

from tests.conftest import SAMPLE_LEADERBOARD, SAMPLE_POSITIONS, SAMPLE_TRADES


BASE = "https://millionscan.test"


@respx.mock
def test_leaderboard_returns_typed_response(client: Client) -> None:
    route = respx.get(f"{BASE}/api/public/v1/leaderboard").mock(
        return_value=Response(200, json=SAMPLE_LEADERBOARD),
    )
    result = client.leaderboard(tier="featured", page_size=2)

    assert route.called
    assert result.tier == "featured"
    assert result.total == 142
    assert len(result.traders) == 2
    top = result.traders[0]
    assert top.public_id == "77271"
    assert top.score == 68
    assert top.roi_30d == 142.5


@respx.mock
def test_positions_strips_hash_prefix(client: Client) -> None:
    route = respx.get(f"{BASE}/api/public/v1/traders/77271/positions").mock(
        return_value=Response(200, json=SAMPLE_POSITIONS),
    )
    result = client.positions("#77271")

    assert route.called
    assert result.public_id == "77271"
    assert len(result.open_positions) == 1
    assert result.open_positions[0].coin == "BTC"
    assert result.open_positions[0].unrealized_pnl == 2_125


@respx.mock
def test_trades_paginates(client: Client) -> None:
    route = respx.get(f"{BASE}/api/public/v1/traders/77271/trades").mock(
        return_value=Response(200, json=SAMPLE_TRADES),
    )
    result = client.trades("77271", page=1, page_size=2)

    assert route.called
    assert result.page == 1
    assert result.total == 47
    assert result.trades[1].action == "CLOSE"
    assert result.trades[1].realized_pnl == pytest.approx(1_840.55)


@respx.mock
def test_iter_trades_walks_until_short_page(client: Client) -> None:
    page_one = {
        **SAMPLE_TRADES,
        "page": 1,
        "page_size": 2,
        "total": 3,
    }
    page_two = {
        **SAMPLE_TRADES,
        "page": 2,
        "page_size": 2,
        "total": 3,
        "trades": SAMPLE_TRADES["trades"][:1],  # short page → stop
    }
    route_one = respx.get(
        f"{BASE}/api/public/v1/traders/77271/trades", params={"page": 1, "page_size": 2},
    ).mock(return_value=Response(200, json=page_one))
    route_two = respx.get(
        f"{BASE}/api/public/v1/traders/77271/trades", params={"page": 2, "page_size": 2},
    ).mock(return_value=Response(200, json=page_two))

    trades = list(client.iter_trades("77271", page_size=2))

    assert route_one.called
    assert route_two.called
    assert len(trades) == 3


@respx.mock
def test_auth_error_raised_on_401(client: Client) -> None:
    respx.get(f"{BASE}/api/public/v1/leaderboard").mock(
        return_value=Response(401, json={"detail": "Invalid API key"}),
    )
    with pytest.raises(AuthError) as exc:
        client.leaderboard()
    assert exc.value.status_code == 401
    assert "Invalid API key" in str(exc.value)


@respx.mock
def test_not_found_error_raised_on_404(client: Client) -> None:
    respx.get(f"{BASE}/api/public/v1/traders/00000/positions").mock(
        return_value=Response(404, json={"detail": "trader not found"}),
    )
    with pytest.raises(NotFoundError):
        client.positions("00000")


@respx.mock
def test_rate_limit_error_raised_on_429() -> None:
    # Use a fresh client with retries=0 to force the raise.
    c = Client(
        api_key="msk_live_test_key",
        base_url=BASE,
        max_retries=0,
    )
    respx.get(f"{BASE}/api/public/v1/leaderboard").mock(
        return_value=Response(
            429,
            json={"detail": "rate limit exceeded"},
            headers={"Retry-After": "5"},
        ),
    )
    with pytest.raises(RateLimitError) as exc:
        c.leaderboard()
    assert exc.value.retry_after == 5.0


def test_missing_api_key_raises_auth_error_eagerly() -> None:
    c = Client(api_key=None, base_url=BASE, max_retries=0)
    with pytest.raises(AuthError):
        c.leaderboard()


@respx.mock
def test_other_4xx_raised_as_apierror(client: Client) -> None:
    respx.get(f"{BASE}/api/public/v1/leaderboard").mock(
        return_value=Response(400, json={"detail": "bad request"}),
    )
    with pytest.raises(APIError) as exc:
        client.leaderboard()
    assert exc.value.status_code == 400
