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
rating, weight, an ad-cost-per-sale estimate, free-text notes — all but
name/category/cost/price are optional).

```bash
python -m src.cli data/sample_candidates.csv --channel dropship --out ranked_report.csv
# or, once you've graduated to FBA:
python -m src.cli data/sample_candidates.csv --channel fba --out ranked_report.csv
```

Prints a ranked shortlist to the console (net margin, net profit, score,
verdict, reasoning, risk flags, and the assumptions each estimate leaned
on) and optionally writes it to CSV.

## Net margin, not gross margin

The number that actually matters is what's left after real costs, not
`sell_price - supplier_cost`. `src/economics/` estimates true net margin
per candidate:

- **dropship**: subtracts payment processing (Shopify Payments' standard
  2.9% + $0.30) and any ad cost you provide.
- **fba**: subtracts an estimated Amazon referral fee, a weight-tiered FBA
  fulfillment fee, and any ad cost you provide.

Every estimate carries an `assumptions` list naming what it leaned on — a
default fee rate, an unknown weight, no ad cost provided — read as a
confidence caveat, not a filled-in number. **These are starting estimates,
not Amazon's or Shopify's actual current fee schedule** — cross-check a
real candidate against Amazon's own FBA Revenue Calculator before
committing capital. The scorer is instructed to weigh `net_margin_pct`
over the naive `gross_margin_pct` and to flag candidates whose economics
lean on shaky assumptions (especially "no ad cost provided," which tends
to overstate margin the most).

## Architecture

```
src/
  providers/    # ProductDataProvider interface + ManualCsvProvider (default, no API key needed)
  economics/    # fee-aware net margin estimator (dropship + FBA)
  scoring/      # ClaudeScorer -- the one place this project calls an LLM
  reporting/    # merges candidates + economics + scores into a ranked report
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
2. **Fee-aware net margin** (this repo, today) — real dropship/FBA
   economics behind every score, not naive gross margin.
3. **Real data providers** — a Keepa or Jungle Scout `ProductDataProvider`
   to replace manual CSV entry with live market data.
4. **Pricing/repricing engine** — rule-bounded automated price
   adjustments (hard floor/ceiling you set, AI only adjusts within that
   band) once a product is live.
5. **Monitoring dashboard** — the "supervise only" surface: daily
   profit-per-SKU, stockout/hijacker alerts, exceptions queued for
   one-click approval instead of full autonomy.

## A note on scope

This is a research tool, not a storefront or a purchasing bot. It never
touches a marketplace account, never places a supplier order, and never
adjusts a live price — those stay deliberate, separate, human-gated steps
even as more of this pipeline gets built out.
