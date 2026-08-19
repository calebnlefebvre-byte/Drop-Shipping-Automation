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
cp .env.example .env   # add ANTHROPIC_API_KEY; add KEEPA_API_KEY too if you want automatic discovery
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

## Monitoring dashboard -- the "supervise only" surface

This is the piece meant for daily/weekly glancing, not for running by
hand step by step. Feed it a sales ledger (units sold, revenue, ad spend,
refunds -- whatever you'd export from Shopify/Amazon, or enter by hand
for now) and it stays quiet unless something actually needs you:

```bash
python -m src.monitoring_cli data/sample_ledger.csv --out summary.csv
```

Per SKU it reuses the exact same fee-aware economics as research and
pricing (so "profitable" means the same thing everywhere in this
project), then only raises a flag for a real problem:

- **UNPROFITABLE** — net loss this period
- **MARGIN BELOW TARGET** — realized net margin fell under the
  `min_net_margin_pct` you set for that SKU, even if it's still profitable
- **STOCKOUT RISK** — inventory on hand at or below your reorder threshold

A SKU with none of those prints in the full summary but never in "needs
attention" -- same "alert on a real transition, not on every poll"
discipline you'd want from any monitor you're going to actually trust
enough to stop checking manually.

## Automatic product discovery (Keepa)

Requires a [Keepa](https://keepa.com/#!api) subscription (paid; they have
a free trial) — set `KEEPA_API_KEY` in `.env`. Queries Keepa's Product
Finder for candidates matching your filters, then writes them to a CSV in
the *exact same shape* `src/cli.py` already reads:

```bash
python -m src.discovery_cli --title-contains "silicone lid" --max-price 25 --min-rating 4 --limit 20
```

```bash
# then, after you fill in supplier_cost by hand (see below):
python -m src.cli data/discovered_candidates.csv --out ranked_report.csv
```

**Important — what Keepa can and can't tell you.** Keepa knows Amazon's
current price, sales rank, star rating, review count, and how many
sellers are competing on a listing. It has **no way to know what you'd
pay a supplier**, so `supplier_cost` is written blank — filling that in
from your own sourcing research (Alibaba, a wholesaler, etc.) is the one
manual step this doesn't automate, and it's the step nothing safely
could: guessing it would poison every downstream margin number. Two
other columns are deliberately left for you rather than guessed:
`est_ad_cost_per_sale` (Keepa doesn't run your ads), and
`est_monthly_searches` — Keepa's sales rank is a genuine demand signal
but it isn't a search-volume number, so it's written into `notes`
instead of a column it would misrepresent.

Useful filters (see `python -m src.discovery_cli --help` for the full
list): `--title-contains`, `--category` (Amazon browse-node ID),
`--max-sales-rank`, `--min-price`/`--max-price`, `--min-rating`,
`--min-reviews`. Anything Keepa's Finder supports beyond these flags can
be passed via `--selection-json path/to/filters.json`, merged into the
query. Each product lookup costs Keepa tokens (their usage-based limit);
the CLI reports tokens remaining after each run and warns when you're
running low.

**Honesty about verification**: this project's dev sandbox has no
outbound network access to `api.keepa.com` (or almost anything else
outside a small allowlist), so `src/discovery/` was built against
Keepa's documented request/response shape and covered with mocked
tests — it has never made a real call. Your first real run is the real
test; if a field looks off, check it against
[Keepa's API docs](https://keepa.com/#!discuss/t/api-overview/) (the CSV
type index table in `src/discovery/keepa_mapping.py` is the most likely
place a mismatch would show up).

## Architecture

```
src/
  providers/    # ProductDataProvider interface + ManualCsvProvider (default, no API key needed)
  discovery/    # Keepa client + response parsing -> writes candidate CSVs for src/cli.py
  economics/    # fee-aware net margin estimator (dropship + FBA) + breakeven floor-price solver
  pricing/      # deterministic, guardrail-bounded price recommendation engine
  monitoring/   # ledger -> per-SKU profit + only-real-problems alerts
  scoring/      # ClaudeScorer -- the one place this project calls an LLM
  reporting/    # merges candidates + economics + scores into a ranked report
  cli.py              # product research entry point
  discovery_cli.py    # Keepa discovery entry point
  pricing_cli.py      # pricing recommendation entry point
  monitoring_cli.py   # dashboard entry point
```

`ProductDataProvider` is deliberately an interface, not a concrete
implementation baked into the pipeline — `ManualCsvProvider` and
Keepa-discovered CSVs both feed `src/cli.py` through the same door.
Same "swap the source, not the pipeline" principle used throughout.

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
4. **Automatic product discovery** (this repo, today) — Keepa's Product
   Finder + Product API, writing straight into the shape `src/cli.py`
   reads. Skipped a free alternative first: an unofficial Google Trends
   scrape is fragile even when reachable (no official API, Google
   actively blocks it) and this project's dev sandbox couldn't reach it
   at all, so Keepa's paid, official, documented API was the sound
   choice instead.
5. **Live repricer/marketplace integration** — connect `pricing_cli`'s
   logic to a real feed (BQool/Seller Snap/Amazon SP-API) so
   recommendations can auto-apply within the guardrails, instead of you
   running the CLI by hand.
6. **Monitoring dashboard** (this repo, today) — per-SKU profit computed
   from a sales ledger, with unprofitable/margin/stockout alerts that
   only fire on a real problem.
7. **Automatic ledger ingestion** — pull orders/inventory directly from
   Shopify's or Amazon's own API instead of a hand-maintained CSV, once
   there's a live store to pull from.

## A note on scope

This is a decision-support toolkit, not a storefront or a purchasing bot.
It computes recommendations — which products look profitable, what a
listing's price should be — but never touches a marketplace account,
never places a supplier order, and never pushes a price change to a live
listing on its own. Applying a recommendation is always a deliberate,
separate, human-gated step, even once a real repricer feed is connected.
