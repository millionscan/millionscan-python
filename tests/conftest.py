"""Shared pytest fixtures.

Tests use respx to mock the HTTP transport. No real API calls fire
during `pytest`; the integration smoke that hits the live endpoint
lives in a separate runner that sets MILLIONSCAN_API_KEY explicitly.
"""

from __future__ import annotations

import pytest

from millionscan.client import Client


@pytest.fixture()
def client() -> Client:
    return Client(
        api_key="msk_live_test_key",
        base_url="https://millionscan.test",
        max_retries=0,
    )


SAMPLE_LEADERBOARD = {
    "tier": "featured",
    "page": 1,
    "page_size": 2,
    "total": 142,
    "traders": [
        {
            "public_id": "77271",
            "score": 68,
            "status": "Active",
            "roi_30d": 142.5,
            "pnl_30d": 30190,
            "win_rate": 0.62,
            "account_value": 184_000,
            "last_trade_at": "2026-04-30T07:27:15.116503+00:00",
        },
        {
            "public_id": "14567",
            "score": 62,
            "status": "Active",
            "roi_30d": 38.1,
            "pnl_30d": 9_876,
            "win_rate": 0.55,
            "account_value": 41_500,
            "last_trade_at": "2026-04-30T05:14:01.000000+00:00",
        },
    ],
    "meta": {"fetched_at": "2026-04-30T08:00:00+00:00"},
}


SAMPLE_POSITIONS = {
    "public_id": "77271",
    "open_positions": [
        {
            "coin": "BTC",
            "side": "long",
            "size": 1.25,
            "notional_value": 84_000,
            "leverage": 5.0,
            "entry_price": 67_200,
            "mark_price": 68_900,
            "unrealized_pnl": 2_125,
            "opened_ago": "3h ago",
        }
    ],
    "meta": {"fetched_at": "2026-04-30T08:00:00+00:00"},
}


SAMPLE_TRADES = {
    "public_id": "77271",
    "page": 1,
    "page_size": 2,
    "total": 47,
    "trades": [
        {
            "timestamp": "2026-04-30T07:27:15.116503+00:00",
            "coin": "BTC",
            "side": "long",
            "action": "OPEN",
            "size": 1.25,
            "entry_price": 67_200,
            "realized_pnl": None,
        },
        {
            "timestamp": "2026-04-29T22:11:08.412000+00:00",
            "coin": "ETH",
            "side": "short",
            "action": "CLOSE",
            "size": 12.0,
            "entry_price": 3_180,
            "realized_pnl": 1_840.55,
        },
    ],
    "meta": {"fetched_at": "2026-04-30T08:00:00+00:00"},
}
