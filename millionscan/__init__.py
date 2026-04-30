"""MillionScan — Official Python SDK.

Quick start
-----------

    import millionscan

    client = millionscan.Client(api_key="msk_live_...")

    # Top 10 featured traders by score
    leaderboard = client.leaderboard(tier="featured", page_size=10)
    for trader in leaderboard.traders:
        print(trader.public_id, trader.score, trader.roi_30d)

    # Live open positions for one trader
    positions = client.positions("77271")
    for p in positions.open_positions:
        print(p.coin, p.side, p.unrealized_pnl)

    # Full trade history (paginated)
    trades = client.trades("77271", page=1, page_size=100)
    for t in trades.trades:
        print(t.timestamp, t.action, t.coin, t.realized_pnl)

Get an API key at https://millionscan.com/developers and set it as the
MILLIONSCAN_API_KEY environment variable; the Client picks it up
automatically when you don't pass one explicitly.

Informational and research use only — not investment advice.
"""

from millionscan.client import Client
from millionscan.exceptions import (
    APIError,
    AuthError,
    MillionScanError,
    NotFoundError,
    RateLimitError,
)
from millionscan.models import (
    LeaderboardResponse,
    PositionsResponse,
    PublicMeta,
    PublicPosition,
    PublicTrade,
    PublicTrader,
    TradesResponse,
)

__version__ = "0.1.0"

__all__ = [
    "Client",
    "MillionScanError",
    "APIError",
    "AuthError",
    "NotFoundError",
    "RateLimitError",
    "PublicMeta",
    "PublicTrader",
    "LeaderboardResponse",
    "PublicPosition",
    "PositionsResponse",
    "PublicTrade",
    "TradesResponse",
    "__version__",
]
