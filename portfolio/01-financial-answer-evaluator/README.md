# 01 — Financial Answer Evaluator

A local evaluator for structured financial answers. It recomputes WACC,
Gordon-growth terminal value and gross margin with `Decimal`, checks the
response's units and returns `pass`, `fail` or `review` with a reason.
This is evaluation infrastructure, not a trained model or a free-text LLM judge.

## Run

Python 3.10+, standard library only. From this directory:

```bash
python evaluate.py
python evaluate.py cases.json --output sample-report.json
python -m unittest discover -v
```

From the repository root: `python portfolio/01-financial-answer-evaluator/evaluate.py`.

## Contract and formulas

Input is a JSON array of cases; see `cases.json` for the complete example.
Each case needs a unique `id`, `task`, `inputs`, and `response` object containing
`value` and `unit`. Values can be JSON numbers or decimal strings; decimal strings
avoid binary floating point ambiguity. Booleans, NaN and infinities are rejected.
Optional `expected_verdict` is used only to measure fixture agreement, never scoring.

| Task | Inputs | Reference | Output unit |
|---|---|---|---|
| `wacc` | equity, debt, cost_equity, cost_debt, tax_rate | E/(E+D) × Re + D/(E+D) × Rd × (1−T) | `ratio` |
| `dcf_terminal` | fcf_current, discount_rate, growth_rate | FCF_current × (1+g)/(r−g) | `currency` |
| `gross_margin` | revenue, cogs | (revenue−cogs)/revenue | `ratio` |

Rates are decimal ratios: 12% is `0.12`. Currency inputs must share the same
currency and scale; the checker cannot infer or convert them. Terminal value
requires r>g and rates above −1. WACC requires non-negative capital and costs,
positive total capital and a tax rate in [0,1]. Revenue must be positive and
COGS non-negative. Negative margins and negative growth above −1 are supported.

Absolute tolerance is 0.0001 for ratios and 0.01 for currency. A wrong unit,
invalid answer or numeric mismatch fails; invalid assumptions or unsupported
tasks need review. Batch-level invalid IDs stop processing.

## Sample and limits

18 intentionally authored synthetic cases produce 6 passes, 7 failures and
5 reviews. All 18 agree with their authored labels. This is a software regression
check, not an independently labeled benchmark, model score, or held-out test.

The checker does not parse prose, inspect reasoning, validate source data,
judge market assumptions, or give investment recommendations. A coincidentally
correct number passes even if its explanation is wrong. Next step: collect
permitted real model outputs, independently label separate cases and assess
false accepts and false rejects before expanding coverage.
