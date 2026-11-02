# 02 — Evidence Auditor

A local evidence-consistency checker for quotations and typed financial facts.
It flags invented quotations, unknown source IDs and mismatched values, and
routes missing periods/units and unsupported inference to human review.

## Run

Python 3.10+, standard library only. From this directory:

```bash
python audit.py
python audit.py claims.json --output sample-report.json
python -m unittest discover -v
```

From the repository root: `python portfolio/02-evidence-auditor/audit.py`.

## Contract

`claims.json` shows the complete format. Top-level `sources` and `claims` are
arrays with unique IDs. Sources contain `text` and a `facts` list. Each fact
has `metric`, `period`, `unit` and `value`. Fact values are finite decimals;
prefer decimal strings. Claims reference a `source_id` and one of:

- `kind: quote`, with a non-empty `quote`: exact case-sensitive substring check.
- `kind: fact`, with metric/period/unit/value: exactly one supplied fact must
  match all three dimensions, then the decimal values must be equal.

No matching or multiple matching facts return review; numeric disagreement
returns fail. No currency conversion, rounding tolerance or period inference is
applied. Source facts are manually supplied, not automatically extracted or
externally verified. Duplicate IDs or malformed source schemas abort the batch.

## Sample and limits

Nine fictional claims yield 2 passes, 3 failures and 4 reviews. ExampleCo and
all its figures are invented. No web requests or model calls are made.

This is **not a complete hallucination detector**. A quotation can appear in
a source while the surrounding claim misrepresents it. A fact can match a
source that is itself incorrect. Arbitrary inference is not scored. Next step:
evaluate quote attribution and claim entailment separately on an independently
reviewed corpus, preserving source version and exact evidence spans.
