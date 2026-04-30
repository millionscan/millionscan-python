"""Example 1 — Quickstart.

Five-minute walkthrough: pull the top 10 featured traders, print
their score and 30-day ROI, and inspect the live open positions of
the highest-scored row.

Set MILLIONSCAN_API_KEY in your environment before running:

    export MILLIONSCAN_API_KEY=msk_live_...
    python examples/01_quickstart.py

Don't have a key yet? Issue one at https://millionscan.com/developers
($89 / 30-day metered access). Informational and research use only.
"""

from __future__ import annotations

import millionscan


def main() -> None:
    client = millionscan.Client()  # picks up MILLIONSCAN_API_KEY from env

    leaderboard = client.leaderboard(tier="featured", page_size=10)
    print(f"Top {leaderboard.page_size} featured traders by score:\n")
    print(f"{'Trader':<12} {'Score':>6} {'30D ROI':>10} {'30D PnL':>14} {'Win rate':>10}")
    print("-" * 56)
    for trader in leaderboard.traders:
        score = f"{trader.score:.0f}" if trader.score is not None else "—"
        roi = f"{trader.roi_30d:.1f}%" if trader.roi_30d is not None else "—"
        pnl = f"${trader.pnl_30d:,.0f}" if trader.pnl_30d is not None else "—"
        wr = f"{trader.win_rate * 100:.0f}%" if trader.win_rate is not None else "—"
        print(f"#{trader.public_id:<11} {score:>6} {roi:>10} {pnl:>14} {wr:>10}")

    if leaderboard.traders:
        top = leaderboard.traders[0]
        print(f"\nLive open positions for top-scored trader #{top.public_id}:\n")
        positions = client.positions(top.public_id)
        for p in positions.open_positions:
            unrealized = (
                f"${p.unrealized_pnl:+,.0f}"
                if p.unrealized_pnl is not None
                else "—"
            )
            print(f"  {p.coin:<6} {p.side:<5} {unrealized}")


if __name__ == "__main__":
    main()
