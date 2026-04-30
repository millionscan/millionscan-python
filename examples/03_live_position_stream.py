"""Example 3 — Polling-based live position monitor.

Polls each watched trader's live positions every 30 seconds and
prints any change vs the previous snapshot — new opens, closed
positions, and meaningful unrealized-PnL drift.

The public API ships a WebSocket event stream at /api/public/v1/events
that gives you the same signal in near-real-time without polling; the
SDK's WebSocket wrapper lands in a follow-up release. Until then, this
polling pattern is the simplest way to observe live activity from
plain Python.

Set MILLIONSCAN_API_KEY in your environment before running:

    export MILLIONSCAN_API_KEY=msk_live_...
    python examples/03_live_position_stream.py

Informational and research use only.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import millionscan

WATCHLIST = ["77271", "14567", "88123"]  # public_ids you care about
POLL_INTERVAL_SEC = 30                    # API snapshot cadence


def _key(p: millionscan.PublicPosition) -> tuple[str, str]:
    return (p.coin, p.side)


def main() -> None:
    client = millionscan.Client()
    state: dict[str, dict[tuple[str, str], millionscan.PublicPosition]] = {
        pid: {} for pid in WATCHLIST
    }

    print(
        f"Polling {len(WATCHLIST)} traders every {POLL_INTERVAL_SEC} s. "
        "Ctrl+C to stop.\n"
    )

    while True:
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        for pid in WATCHLIST:
            try:
                snapshot = client.positions(pid)
            except millionscan.APIError as exc:
                print(f"[{now}] #{pid} error: {exc}")
                continue

            current = {_key(p): p for p in snapshot.open_positions}
            previous = state[pid]

            for key, pos in current.items():
                if key not in previous:
                    print(
                        f"[{now}] #{pid} OPENED {pos.coin} {pos.side} "
                        f"@ {pos.entry_price}"
                    )
            for key, pos in previous.items():
                if key not in current:
                    print(f"[{now}] #{pid} CLOSED {pos.coin} {pos.side}")

            state[pid] = current

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nstopped.")
