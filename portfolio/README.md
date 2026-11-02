# Finance AI portfolio — evaluation first

Six runnable projects, followed by six planned engineering/ML projects.
Python 3.10+; standard library only. Default demos are offline and need no keys.
Projects 04–06 optionally request model commentary with `--ai`; that mode needs
your API credentials and may incur charges. No real-key call has been verified.
These are local portfolio prototypes built with AI assistance, not deployed client work.
All examples are authored synthetic data; none are actual Mercor prompts, responses,
client documents, or measured model outputs.

| Order | Project | Demonstrated skill | Status |
|---|---|---|---|
| 01 | [Financial Answer Evaluator](01-financial-answer-evaluator/) | Decimal calculations, answer contracts, error taxonomy | Runnable |
| 02 | [Evidence Auditor](02-evidence-auditor/) | Exact quotation and period/unit-aware fact checks | Runnable |
| 03 | [Evaluation Release Gate](03-evaluation-release-gate/) | Paired regression analysis, quality/cost/latency gates | Runnable |
| 04 | [Budget Variance Investigation Assistant](04-budget-variance-assistant/) | Reconciled price/volume bridges and materiality review | Runnable |
| 05 | [Cash Collection Prioritization Workbench](05-cash-collection-workbench/) | Dispute/promise-aware queue and explicit cash scenarios | Runnable |
| 06 | [Supplier Proposal Comparison Assistant](06-supplier-proposal-assistant/) | Total contract cost, eligibility and weight sensitivity | Runnable |

From the repository root:

```bash
python portfolio/run_checks.py
```

This runs 63 unit tests and regenerates six `sample-report.json` files plus
Markdown reports for projects 04–06. Each project accepts a custom JSON input.
Run each directory's tests with `python -m unittest discover -v` inside it.
Projects 04–06 use shared parent helpers; retain the portfolio folder structure.

## How to read the demos

1. Project 01 checks 18 authored structured answers: 6 pass, 7 fail, 5 need review.
   Its 18/18 agreement with fixture labels checks intended software behavior;
   it does not measure a real LLM's accuracy or generalization.
2. Project 02 checks nine authored claims: 2 pass, 3 fail, 4 need review.
   An exact quote can be genuine while its surrounding interpretation is wrong.
3. Project 03 uses 20 simulated paired outcomes. Candidate pass rate rises
   from 80% to 90%, but one critical failure blocks release. The exact paired
   test gives p=0.6875; this tiny example is not evidence of improvement.
4. Project 04 reconciles four budget lines; net contribution rises by 100 TRY,
   with a +1,900 quantity effect and −1,800 price effect. These are arithmetic drivers.
5. Project 05 routes seven customer snapshots; base scenario cash is 5,650 TRY,
   explicitly an assumption-based amount, not predicted or recovered cash.
6. Project 06 compares five fictional proposals, ranks only two eligible TRY
   bids, and shows the leading bid changes with delivery/payment weights.

See [ROADMAP.md](ROADMAP.md) for all 12 planned projects and acceptance criteria.
See [LEARNING_GUIDE_TR.md](LEARNING_GUIDE_TR.md) before putting these on a CV.

## Next validation step

Choose a permitted model and generate real outputs on a separately authored,
versioned test set. Record model identifier, prompt, parameters, timestamp,
tokens and observed latency. Have an independent domain reviewer adjudicate
labels. Report failures and confidence intervals, not only a single score.
Default prototypes do not call a model; projects 04–06 contain an optional
commentary adapter validated only through mocked HTTP tests. No model training,
fine-tuning or production deployment has been performed.

See [BUSINESS_TOOLS.md](BUSINESS_TOOLS.md) for bounded optional AI calls and
SQLite review acknowledgements. Those records perform no external actions.
