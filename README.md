# Drop Shipping Automation

AI-assisted product research for a dropshipping/FBA store — scores candidate
products via the Claude API against margin, demand, and competition signals,
and hands back a ranked shortlist. It never places an order, sets a live
price, or spends money on its own — every score is decision support for a
human to act on.

## Why it's built this way

The riskiest part of "fully automate my store" is letting an AI act
autonomously with real money. This project draws a hard line: the LLM is
used for product research, where a ranked opinion is genuinely useful and
low-stakes to get wrong — it can't invent numbers, and a malformed
response fails loudly instead of guessing. Pricing is the opposite case —
the actual number that moves money — so `src/pricing/` is deliberately
rule-only, with **no LLM call anywhere in that path**. See Roadmap below
for what's built and what's next.

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

## Pricing guardrail engine (no AI involved)

Once you have a live listing, `src/pricing_cli.py` recommends a price —
deterministic rules only, never an LLM call, because the number that
actually moves money should never come from a model's judgment. See
`data/sample_listings.csv` for the shape.

```bash
python -m src.pricing_cli data/sample_listings.csv --out price_recommendations.csv
```

For each listing it:
1. Resolves a **floor** — either the one you set, or solved from your
   `min_net_margin_pct` using the same fee model as `src/economics/`
   (`src/economics/breakeven.py`), so the floor always reflects your real
   minimum profitable price, not a guess.
2. Resolves a **ceiling** — either the one you set, or a 3x-floor
   placeholder that's clearly flagged in the output as needing a real
   number before you trust it.
3. Recommends undercutting the lowest competitor price you provide by a
   cent, clamped hard to `[floor, ceiling]` — it is structurally
   impossible for this to recommend a price outside that band, no matter
   what the competitor data says.

This is the guardrail layer to have in place *before* ever connecting a
live repricer (BQool, Seller Snap) or Amazon's own SP-API — those can
call this logic (or logic like it) to decide what to actually push,
instead of trusting a black-box vendor algorithm with no floor.

## Architecture

```
src/
  providers/    # ProductDataProvider interface + ManualCsvProvider (default, no API key needed)
  economics/    # fee-aware net margin estimator (dropship + FBA) + breakeven floor-price solver
  pricing/      # deterministic, guardrail-bounded price recommendation engine
  scoring/      # ClaudeScorer -- the one place this project calls an LLM
  reporting/    # merges candidates + economics + scores into a ranked report
  cli.py            # product research entry point
  pricing_cli.py    # pricing recommendation entry point
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
3. **Pricing/repricing engine** (this repo, today) — deterministic,
   floor/ceiling-bounded price recommendations; no AI in the pricing
   decision itself.
4. **Real data providers** — a live source for competitor prices,
   demand, and Buy Box data, to replace manual CSV entry. **Tried and
   deliberately skipped for now**: an unofficial Google Trends scrape —
   it's fragile even when reachable (Google actively blocks it, no
   official API), and wasn't reachable at all from this project's dev
   sandbox. Keepa's official paid API is the reliable path once you're
   ready to spend on it; a `KeepaProvider` implementing
   `ProductDataProvider` slots in without touching anything downstream.
5. **Live repricer/marketplace integration** — connect `pricing_cli`'s
   logic to a real feed (BQool/Seller Snap/Amazon SP-API) so
   recommendations can auto-apply within the guardrails, instead of you
   running the CLI by hand.
6. **Monitoring dashboard** — the "supervise only" surface: daily
   profit-per-SKU, stockout/hijacker alerts, exceptions queued for
   one-click approval instead of full autonomy.

## A note on scope

This is a decision-support toolkit, not a storefront or a purchasing bot.
It computes recommendations — which products look profitable, what a
listing's price should be — but never touches a marketplace account,
never places a supplier order, and never pushes a price change to a live
listing on its own. Applying a recommendation is always a deliberate,
separate, human-gated step, even once a real repricer feed is connected.
