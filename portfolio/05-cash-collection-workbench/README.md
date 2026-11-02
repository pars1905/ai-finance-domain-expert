# 05 — Cash Collection Prioritization Workbench

A transparent collection-review queue for fictional **business customer balance
snapshots**. This project does not parse or match invoices. It separates disputes,
active promises, current balances and settled balances, then ranks actionable
overdue amounts and applies explicit cash scenario rates.

Python 3.10+, standard library only; keep the parent `portfolio` helper files.

## Run

From the repository root:

```bash
python portfolio/05-cash-collection-workbench/prioritize.py
python portfolio/05-cash-collection-workbench/prioritize.py --output /tmp/collections-report.json --markdown /tmp/collections-report.md
```

From this directory: `python -m unittest discover -v`. Supply your JSON path
as the first positional argument; see `customers.json` for all fields.

## Rules and assumptions

`as_of` is required and explicit, never the host's current date. Dates use
YYYY-MM-DD. Monetary inputs are non-negative finite decimals; use strings.
Each unique customer has one balance and one due date, disputed amount,
non-negative whole broken-promise count, optional last-contact and promise dates.
Disputes cannot exceed balances; last contact cannot be in the future.
Whole numbers are capped at 1,000,000; decimal inputs at 1e15.

Ordering of classification: settled → not overdue → fully disputed → active
promise → collection review. A promise on the as-of date is active. Partial
disputes are excluded from actionable amounts. No collection is scheduled.

Actionable priority score (0–100):

`50 × undisputed_balance / max_actionable_balance + 30 × min(days_overdue,90)/90 + 20 × min(broken_promises,3)/3`

This is a disclosed heuristic, not repayment probability, a credit model or
evidence that a contact will succeed. The score changes when the peer set changes.
Ties use undisputed balance then ID for reproducibility. Non-actionable items
have score zero; disputes still need a separate human review.

Scenario amounts sum actionable undisputed balances × user-specified rates for
1–30, 31–60 and 61+ day buckets. Rates must be in [0,1]. The example produces
3,200 / 5,650 / 8,000 TRY under conservative/base/optimistic assumptions. These
are **what-if amounts**, not forecasts or recovered cash. No time horizon is
estimated; rate applicability must be justified before a real pilot.

## Review

```bash
python portfolio/review_decision.py /tmp/collections-report.json --item-id customer-A --decision acknowledge --reviewer demo-collector --note "Reviewed undisputed balance" --db /tmp/collection-reviews.db
```

Run from repository root. This only creates a local review record. It sends no
message, changes no customer balance and initiates no payment. See
[BUSINESS_SPEC.md](BUSINESS_SPEC.md), [sample-report.md](sample-report.md), and
[shared AI/review instructions](../BUSINESS_TOOLS.md).
