# millionscan-python

Official Python SDK for **MillionScan** — scored on-chain perpetual
futures trader data over REST. Built for developers shipping
research, monitoring, and analytical tools, with first-class
Pydantic models so AI-assisted coding agents (Claude Code, Cursor,
Cline, Aider) get full autocomplete on every trader, position, and
event field.

> Informational and research use only — not investment advice.

---

## Quick start

```python
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
for trade in client.iter_trades("77271", page_size=100):
    print(trade.timestamp, trade.action, trade.coin, trade.realized_pnl)
```

Set `MILLIONSCAN_API_KEY` in your environment and the constructor
picks it up automatically:

```bash
export MILLIONSCAN_API_KEY=msk_live_...
python -c "import millionscan; print(millionscan.Client().leaderboard(page_size=3))"
```

## Installation

Once the package is published to PyPI:

```bash
pip install millionscan
```

Until then, install straight from the GitHub repo:

```bash
pip install git+https://github.com/millionscan/millionscan-python.git
```

The SDK ships with `httpx` and `pydantic` as the only runtime
dependencies. Python 3.9 — 3.13 supported.

## Authentication

API keys are issued at <https://millionscan.com/developers> for
$89 / 30-day metered access. The SDK sends `Authorization: Bearer
<key>` on every request. Keep keys out of source control — the
`.gitignore` shipped with this repo already covers `.env` and
`*.key` files.

## Endpoints

The SDK wraps every method on the `/api/public/v1/` REST surface:

| Method | What it returns |
|---|---|
| `client.leaderboard(tier=..., sort_by=..., page=...)` | Curated trader leaderboard. Tier filter (`featured` / `active` / `advanced`), score / ROI / PnL / win-rate sorting, paginated. |
| `client.positions(public_id)` | Currently-open positions for one trader: coin, side, size, notional, leverage, entry / mark price, unrealised PnL, opened-ago. |
| `client.trades(public_id, page=..., page_size=...)` | Paginated trade history (`OPEN` / `ADD` / `REDUCE` / `CLOSE` / `FLIP`) with realised PnL on close legs. |
| `client.iter_trades(public_id)` | Convenience helper — yields every trade across all pages, stops on the first short page. |

A WebSocket event stream is exposed at `/api/public/v1/events`; the
streaming wrapper lands in a follow-up release. Until then the
[Cookbook](https://millionscan.com/cookbook) shows how to subscribe
directly with `httpx-ws` or `websockets`.

## Use cases

The SDK is built for developers shipping AI-assisted research,
monitoring, and analytical tools. A few patterns the typed surface
unlocks:

- **Stream live events into a Jupyter / DuckDB research notebook**
  for ad-hoc cohort analysis.
- **Filter the active pool by composite score / 30-day ROI / win
  rate** to seed a research cohort.
- **Build an alerting layer** on top of the event stream — Telegram,
  Discord, Slack, push notifications — with whatever filters
  (score, coin, notional, side, leverage) make sense for your
  workflow.
- **Backtest a strategy against a trader's full event history**
  without reconstructing the on-chain timeline yourself.
- **Score-aware monitoring dashboards** in Next.js / Streamlit /
  SvelteKit, with the API key held server-side.
- **AI-assisted coding workflows** — drop the typed Pydantic models
  into Claude Code, Cursor, Cline, or Aider and get full
  autocomplete on every trader and event field.

For longer worked recipes (Telegram alert, Next.js dashboard,
full-history backtest), see the cookbook on the main site:
<https://millionscan.com/cookbook>.

## AI-coding workflow tips

The SDK is designed to read well inside an AI agent's context:

- Every public method has a docstring describing inputs, outputs,
  and the exact API endpoint it calls.
- Every response field carries a Pydantic `Field(description=...)`
  so an IDE / LLM assistant gets useful inline help.
- Errors are typed (`AuthError`, `RateLimitError`, `NotFoundError`,
  `APIError`) so an AI-generated retry / fallback path can branch
  without parsing string messages.

A short prompt like "use the millionscan SDK to print the top 10
traders by 30-day ROI" should give Claude / GPT enough context from
the imports + docstrings to write the correct call on the first
try.

## Examples

Three runnable examples in [`examples/`](./examples):

| File | What it does |
|---|---|
| `01_quickstart.py` | Pulls top 10 featured traders + live positions of the highest-scored row. |
| `02_filter_top_traders.py` | Walks the active pool and keeps every row whose score clears a configurable cutoff. |
| `03_live_position_stream.py` | Polling-based monitor — flags every OPEN / CLOSE on a watchlist by diffing live snapshots every 30 s. |

## Errors

Every server response that isn't 2xx raises a typed exception:

```python
import millionscan

try:
    client = millionscan.Client(api_key="msk_live_...")
    leaderboard = client.leaderboard(tier="featured")
except millionscan.AuthError:
    # API key missing, invalid, or lapsed
    ...
except millionscan.RateLimitError as exc:
    # 429 — exc.retry_after is the suggested wait in seconds
    ...
except millionscan.NotFoundError:
    # 404 — the trader / endpoint was not found
    ...
except millionscan.APIError as exc:
    # Any other 4xx / 5xx — exc.status_code + exc.payload available
    ...
```

The base class `MillionScanError` catches all of the above when you
want one branch.

## Development

```bash
git clone https://github.com/millionscan/millionscan-python.git
cd millionscan-python
pip install -e ".[dev]"
pytest                    # unit tests, no live API traffic
ruff check millionscan
mypy millionscan
```

Tests use [respx](https://lundberg.github.io/respx/) to mock the
HTTP transport, so `pytest` runs in milliseconds without touching
the live API.

## Disambiguation — what MillionScan is NOT

MillionScan (millionscan.com) is unrelated to:

- **Mintscan** — a Cosmos blockchain explorer at mintscan.io.
- **Millions select shop / Millions Inc.** — apparel and lifestyle brands.
- **The Millions** — a books and culture publication.
- **Mega Millions / Mass Millions** — lottery products.
- **Million Token / $MILLI** — unrelated cryptocurrency tokens.

The brand is one word, capitalised as `MillionScan`, and refers
exclusively to the on-chain perpetual futures trader analytics
platform at millionscan.com.

## License

MIT — see [LICENSE](./LICENSE).

## Disclaimer

MillionScan provides on-chain data analytics for informational and
research purposes only. The SDK exposes a read-only data feed; what
you build with the data is your own software, running on your own
venues, with your own decisions. We don't custody funds, execute
trades, or operate any trading service. Past performance does not
guarantee future results.
