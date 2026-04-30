"""Pydantic response models for the MillionScan public API.

The shapes mirror `backend/api_public/schemas.py` on the server side
so the field set, types, and nullability stay consistent across
languages. Every field carries a docstring-style description so an
IDE / AI assistant gets useful inline help on hover.

Sizes are in raw coin units; notional / entry / mark / PnL are USD;
timestamps are timezone-aware UTC ``datetime`` objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PublicMeta(BaseModel):
    """Per-response metadata block."""

    fetched_at: datetime = Field(
        ...,
        description="UTC timestamp when this response was generated server-side.",
    )


class PublicTrader(BaseModel):
    """One row in the curated leaderboard."""

    public_id: str = Field(
        ...,
        description=(
            "Stable public identifier of the trader, e.g. '77271'. "
            "Use this in subsequent /traders/{public_id}/* calls."
        ),
    )
    score: Optional[float] = Field(
        None,
        description=(
            "Composite quality score 0-68. Higher = stronger track record. "
            "Methodology at https://millionscan.com/about/score."
        ),
    )
    status: str = Field(
        ...,
        description=(
            "'Active' if the trader has had qualifying activity in the "
            "last 14 days, otherwise 'Inactive'."
        ),
    )
    roi_30d: Optional[float] = Field(
        None,
        description="Trailing 30-day return on investment in percentage points.",
    )
    pnl_30d: Optional[float] = Field(
        None,
        description="Trailing 30-day realised profit-and-loss in USD.",
    )
    win_rate: Optional[float] = Field(
        None,
        description="Trailing 30-day win rate, fraction 0-1 (e.g. 0.62 = 62%).",
    )
    account_value: Optional[float] = Field(
        None,
        description="Current futures-account collateral + uPnL in USD.",
    )
    last_trade_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp of the trader's most recent on-chain event.",
    )


class LeaderboardResponse(BaseModel):
    """Paginated curated trader leaderboard response."""

    tier: str = Field(
        ...,
        description="Curation pool: 'featured' / 'active' / 'advanced'.",
    )
    page: int = Field(..., description="1-indexed page returned.")
    page_size: int = Field(..., description="Items in this page.")
    total: int = Field(..., description="Total trader count across all pages.")
    traders: List[PublicTrader]
    meta: PublicMeta


class PublicPosition(BaseModel):
    """One open position held by a trader."""

    coin: str = Field(..., description="Asset symbol, e.g. 'BTC'.")
    side: str = Field(..., description="'long' or 'short'.")
    size: Optional[float] = Field(
        None,
        description="Position size in coin units (always positive).",
    )
    notional_value: Optional[float] = Field(
        None,
        description="Position notional in USD = abs(size) * entry_price.",
    )
    leverage: Optional[float] = Field(
        None,
        description="Effective leverage. e.g. 5 = 5x.",
    )
    entry_price: Optional[float] = Field(
        None,
        description="Volume-weighted entry price in USD.",
    )
    mark_price: Optional[float] = Field(
        None,
        description="Latest mark price in USD.",
    )
    unrealized_pnl: Optional[float] = Field(
        None,
        description="Live unrealised PnL in USD at the latest snapshot.",
    )
    opened_ago: Optional[str] = Field(
        None,
        description="Human-readable age since OPEN, e.g. '2h ago' / '3d ago'.",
    )


class PositionsResponse(BaseModel):
    """All currently-open positions for a single trader."""

    public_id: str
    open_positions: List[PublicPosition]
    meta: PublicMeta


class PublicTrade(BaseModel):
    """One historical event in a trader's trade ledger."""

    timestamp: datetime = Field(
        ...,
        description="UTC time the event was recorded on-chain.",
    )
    coin: str
    side: str = Field(..., description="'long' or 'short'.")
    action: str = Field(
        ...,
        description=(
            "One of 'OPEN' / 'ADD' / 'REDUCE' / 'CLOSE' / 'FLIP'."
        ),
    )
    size: Optional[float] = Field(
        None,
        description=(
            "Coin-unit size of THIS event (signed delta when ADD/REDUCE; "
            "full position size when OPEN/CLOSE/FLIP)."
        ),
    )
    entry_price: Optional[float] = Field(
        None,
        description="USD price at which this event executed.",
    )
    realized_pnl: Optional[float] = Field(
        None,
        description=(
            "USD realised PnL booked by this event. Populated on CLOSE / "
            "partial REDUCE; null on OPEN / ADD / FLIP-open."
        ),
    )


class TradesResponse(BaseModel):
    """Paginated trade history for a single trader."""

    public_id: str
    page: int
    page_size: int
    total: int = Field(..., description="Total events across all pages.")
    trades: List[PublicTrade]
    meta: PublicMeta
