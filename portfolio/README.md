# Finance AI portfolio — evaluation first

Three runnable evaluation projects, followed by a nine-project learning roadmap.
Python 3.10+; standard library only; no API keys, network calls, or paid services.
These are local portfolio prototypes built with AI assistance, not deployed client work.
All examples are authored synthetic data; none are actual Mercor prompts, responses,
client documents, or measured model outputs.

| Order | Project | Demonstrated skill | Status |
|---|---|---|---|
| 01 | [Financial Answer Evaluator](01-financial-answer-evaluator/) | Decimal calculations, answer contracts, error taxonomy | Runnable |
| 02 | [Evidence Auditor](02-evidence-auditor/) | Exact quotation and period/unit-aware fact checks | Runnable |
| 03 | [Evaluation Release Gate](03-evaluation-release-gate/) | Paired regression analysis, quality/cost/latency gates | Runnable |

From the repository root:

```bash
python portfolio/run_checks.py
```

This runs 24 unit tests and regenerates three `sample-report.json` files. Each
project also accepts a user-supplied JSON input. The projects are independent:
run each directory's tests with `python -m unittest discover -v` inside it.

## How to read the demos

1. Project 01 checks 18 authored structured answers: 6 pass, 7 fail, 5 need review.
   Its 18/18 agreement with fixture labels checks intended software behavior;
   it does not measure a real LLM's accuracy or generalization.
2. Project 02 checks nine authored claims: 2 pass, 3 fail, 4 need review.
   An exact quote can be genuine while its surrounding interpretation is wrong.
3. Project 03 uses 20 simulated paired outcomes. Candidate pass rate rises
   from 80% to 90%, but one critical failure blocks release. The exact paired
   test gives p=0.6875; this tiny example is not evidence of improvement.

See [ROADMAP.md](ROADMAP.md) for all 12 planned projects and acceptance criteria.
See [LEARNING_GUIDE_TR.md](LEARNING_GUIDE_TR.md) before putting these on a CV.

## Next validation step

Choose a permitted model and generate real outputs on a separately authored,
versioned test set. Record model identifier, prompt, parameters, timestamp,
tokens and observed latency. Have an independent domain reviewer adjudicate
labels. Report failures and confidence intervals, not only a single score.
Current prototypes do not call, train, fine-tune, or deploy an LLM.
