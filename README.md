# Drop Shipping Automation

AI-assisted product research for a dropshipping/FBA store — scores candidate
products via the Claude API against margin, demand, and competition signals,
and hands back a ranked shortlist. It never places an order, sets a live
price, or spends money on its own — every score is decision support for a
human to act on.

## Why it's built this way

The riskiest part of "fully automate my store" is letting an AI act
autonomously with real money. This project draws the line at research:
the model only ever produces a ranked opinion from data you (or a future
provider) already gathered — it can't invent numbers, and a malformed
response fails loudly instead of guessing. Pricing/repricing automation
(with hard floor/ceiling guardrails) is the natural next module, once
research is proven out — see Roadmap below.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
```

## Usage

Fill in a CSV of candidates — see `data/sample_candidates.csv` for the
shape (name, category, supplier_cost, target_sell_price, and whatever
market signal you have: search volume, competitor count, competitor
rating, free-text notes).

```bash
python -m src.cli data/sample_candidates.csv --out ranked_report.csv
```

Prints a ranked shortlist to the console (score, verdict, reasoning, any
risk flags) and optionally writes it to CSV.

## Architecture

```
src/
  providers/    # ProductDataProvider interface + ManualCsvProvider (default, no API key needed)
  scoring/      # ClaudeScorer -- the one place this project calls an LLM
  reporting/    # merges candidates + scores into a ranked report
  cli.py        # entry point
```

`ProductDataProvider` is deliberately an interface, not a concrete
implementation baked into the pipeline: swap `ManualCsvProvider` for a
real Keepa or Jungle Scout provider later without touching scoring or
reporting. Same "swap the source, not the pipeline" principle used
throughout.

## Running tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Scoring tests mock the Anthropic client — no API key or network access
needed to run the suite.

## Roadmap

1. **Product research** (this repo, today) — AI-scored shortlist from
   manually-entered market data.
2. **Real data providers** — a Keepa or Jungle Scout `ProductDataProvider`
   to replace manual CSV entry with live market data.
3. **Pricing/repricing engine** — rule-bounded automated price
   adjustments (hard floor/ceiling you set, AI only adjusts within that
   band) once a product is live.
4. **Monitoring dashboard** — the "supervise only" surface: daily
   profit-per-SKU, stockout/hijacker alerts, exceptions queued for
   one-click approval instead of full autonomy.

## A note on scope

This is a research tool, not a storefront or a purchasing bot. It never
touches a marketplace account, never places a supplier order, and never
adjusts a live price — those stay deliberate, separate, human-gated steps
even as more of this pipeline gets built out.
