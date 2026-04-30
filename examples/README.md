# MillionScan Python SDK — examples

Drop-in scripts for the most common research and monitoring
patterns. Every example runs as-is once `MILLIONSCAN_API_KEY` is
exported in your shell:

```bash
export MILLIONSCAN_API_KEY=msk_live_...
python examples/01_quickstart.py
```

| File | What it does |
|---|---|
| `01_quickstart.py` | Pulls the top 10 featured traders + the live open positions of the highest-scored row. Five-minute walkthrough for first-time users. |
| `02_filter_top_traders.py` | Walks the active pool and keeps every trader whose score clears a configurable cutoff. First step of a research / cohort pipeline. |
| `03_live_position_stream.py` | Polling-based monitor — flags every OPEN / CLOSE on a watchlist by diffing live position snapshots every 30 s. |

## AI-coding workflows

The snippets above are written to paste straight into Claude Code,
Cursor, Cline, Aider, or any AI-assisted coding agent. Drop one of
them into your agent's context, ask it to adapt the watchlist /
cutoff / output destination to your project, and you should be
running in under a minute. The Pydantic models in
`millionscan/models.py` give the agent typed autocomplete on every
field.

For longer recipes (Telegram alert, Next.js dashboard, full-history
backtest) see the cookbook on the main site:
<https://millionscan.com/cookbook>.

## Disclaimer

Informational and research use only — not investment advice. The
SDK exposes a read-only data feed; what you build with the data is
your own software.
