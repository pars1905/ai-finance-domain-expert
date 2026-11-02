# 04 — Budget Variance Investigation Assistant

An FP&A decision-support prototype: reconcile budget and actual amounts, split
variances into price and volume effects, and route material findings to an
analyst. Arithmetic is deterministic; optional AI commentary is separate.
Python 3.10+, standard library only. Keep the parent `portfolio` helper files.

## Run

From the repository root:

```bash
python portfolio/04-budget-variance-assistant/analyze.py
python portfolio/04-budget-variance-assistant/analyze.py --output /tmp/budget-report.json --markdown /tmp/budget-report.md
```

From this directory, run `python -m unittest discover -v`. A custom JSON input
can be passed as the first argument. `budget.json` is a complete input example.

## Calculation contract

One currency and period per input; `kind` is revenue or expense. Quantities
are whole non-negative units up to 1,000,000; unit prices are non-negative
decimals up to 1,000,000,000 with at most two decimal places. Optional supplied
`budget_total`/`actual_total` must exactly reconcile or the entire run fails.
Use decimal strings for monetary values. Duplicate IDs and invalid inputs fail.

- Budget = budget quantity × budget unit price.
- Actual = actual quantity × actual unit price.
- Volume effect = (actual quantity − budget quantity) × budget unit price.
- Price effect = actual quantity × (actual unit price − budget unit price).
- Price + volume = actual − budget. The interaction is allocated to price.
- Contribution totals are revenue minus expense, not a full profit statement.
- Review requires nonzero variance meeting **both** absolute and relative
  policy thresholds (inclusive). With zero budget, only the absolute threshold applies.
- Revenue increases are favorable; expense increases are unfavorable.

Evidence paths use stable logical row IDs, for example `lines/sales/actual_qty`;
they are not JSON array indexes or externally verified source documents.

## Synthetic demonstration

Four authored lines. Sales variance is +2,800 TRY: volume +4,000 and price −1,200.
Materials cost rises 2,200 TRY; unbudgeted service cost is 500 TRY. Operating
contribution moves from 7,000 to 7,100 TRY. Three lines require analyst review.
See [sample-report.md](sample-report.md) and [sample-report.json](sample-report.json).

These are arithmetic drivers, **not established causes**. Timing, mix, returns,
partial units, FX, tax, headcount economics and accounting accruals are outside
this narrow model. There is no observed saving or real business improvement.

## Analyst workflow

Read [BUSINESS_SPEC.md](BUSINESS_SPEC.md). To record a local review:

```bash
python portfolio/review_decision.py /tmp/budget-report.json --item-id sales --decision acknowledge --reviewer demo-analyst --note "Checked quantities and price bridge" --db /tmp/budget-reviews.db
```

Use the command from repository root. Acknowledgement records review, not a
budget adjustment. See [shared AI/review instructions](../BUSINESS_TOOLS.md)
for optional `--ai`, test scope, and limitations.
