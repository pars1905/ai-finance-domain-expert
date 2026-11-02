# 06 — Supplier Proposal Comparison Assistant

Compare fictional supplier bids using mandatory criteria, comparable net
contract cost and explicit tradeoff weights. Show whether ranking changes
when delivery/payment priorities change. A human retains supplier selection.

Python 3.10+, standard library only; keep the parent `portfolio` helper files.

## Run

From the repository root:

```bash
python portfolio/06-supplier-proposal-assistant/compare_bids.py
python portfolio/06-supplier-proposal-assistant/compare_bids.py --output /tmp/bids-report.json --markdown /tmp/bids-report.md
```

From this directory: `python -m unittest discover -v`. Pass a custom JSON path
as the first positional argument. `bids.json` contains the full schema; the
values were manually transcribed from [fictional proposals](synthetic-proposals.md).
The tool does not extract or independently authenticate these documents.

## Eligibility and total-cost contract

Unique bid IDs; positive whole quantity and contract years. Monetary fields are
non-negative net amounts in one currency. Missing fields/criteria are incomplete;
failed mandatory criteria are ineligible; different currencies require conversion
and are not ranked. Criteria must be JSON booleans, not the string `"false"`.
Whole numbers cap at 1,000,000; bid monetary fields cap at 1,000,000,000.

Total = quantity × unit_price + freight + setup + years × annual_maintenance.
Freight/setup are one-off; maintenance is per contract year, not per unit.
All bids must use comparable commercial scope. Tax, inflation, financing,
discounting, FX and risk-adjusted cash flows are excluded.

For eligible bids only:

- Cost score = (highest cost − bid cost)/(highest cost − lowest cost).
- Delivery score = (slowest days − bid days)/(slowest days − fastest days).
- Identical cost/delivery values receive equal full credit.
- Payment score = min(payment days, 90)/90; longer supplier credit scores higher.
- Total score = 100 × weighted sum. Non-negative cost/delivery/payment weights
  must sum exactly to one. Tied scores sort by ID; this does not break a business tie.

Relative normalization depends on which bids are eligible and can exhibit rank
reversal when the comparison set changes. Scores are a discussion aid, not an
objective optimum. Longer payment terms may conceal other commercial costs.

## Demonstration

Supplier A has 10,900 TRY total cost and ranks ahead under the base weights.
Supplier B ranks ahead when delivery is prioritized. C fails security review,
D lacks freight data, and E quotes EUR rather than TRY. See
[sample-report.md](sample-report.md) and [sample-report.json](sample-report.json).

```bash
python portfolio/review_decision.py /tmp/bids-report.json --item-id supplier-A --decision acknowledge --reviewer demo-buyer --note "Reviewed normalized cost and sensitivity" --db /tmp/supplier-reviews.db
```

Run from root. Acknowledgement is not award approval; no supplier selection,
purchase order or payment is executed. See [BUSINESS_SPEC.md](BUSINESS_SPEC.md)
and [shared AI/review instructions](../BUSINESS_TOOLS.md).
