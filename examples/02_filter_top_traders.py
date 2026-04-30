"""Example 2 — Filter top traders by score.

Walks every page of the active pool and keeps the rows whose score
clears a configurable cutoff. Useful as the first step of a research
pipeline (e.g. cohort analysis, AI-prompt context priming).

Set MILLIONSCAN_API_KEY in your environment before running:

    export MILLIONSCAN_API_KEY=msk_live_...
    python examples/02_filter_top_traders.py

Informational and research use only.
"""

from __future__ import annotations

import millionscan

SCORE_CUTOFF = 65   # 65+ = top tier on the 0-68 composite scale
PAGE_SIZE = 100     # max page size on the public API


def main() -> None:
    client = millionscan.Client()
    matches: list[millionscan.PublicTrader] = []

    page = 1
    while True:
        batch = client.leaderboard(
            tier="active",
            page=page,
            page_size=PAGE_SIZE,
            sort_by="score",
            sort_order="desc",
        )
        for trader in batch.traders:
            if trader.score is None:
                continue
            if trader.score < SCORE_CUTOFF:
                # Sorted desc by score → first below-cutoff row means
                # nothing later in the pagination will qualify either.
                _print_summary(matches)
                return
            matches.append(trader)

        if len(batch.traders) < PAGE_SIZE:
            break
        page += 1

    _print_summary(matches)


def _print_summary(matches: list[millionscan.PublicTrader]) -> None:
    print(f"Found {len(matches)} traders with score >= {SCORE_CUTOFF}\n")
    print(f"{'Trader':<12} {'Score':>6} {'30D ROI':>10} {'30D PnL':>14}")
    print("-" * 46)
    for t in matches[:25]:  # cap the printout for readability
        roi = f"{t.roi_30d:.1f}%" if t.roi_30d is not None else "—"
        pnl = f"${t.pnl_30d:,.0f}" if t.pnl_30d is not None else "—"
        score = f"{t.score:.0f}" if t.score is not None else "—"
        print(f"#{t.public_id:<11} {score:>6} {roi:>10} {pnl:>14}")
    if len(matches) > 25:
        print(f"... and {len(matches) - 25} more")


if __name__ == "__main__":
    main()
