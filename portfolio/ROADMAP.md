# Twelve-project roadmap

Only projects 01–03 are implemented. Items 04–12 are plans, not completed work
and must not be listed as completed CV projects. Build and understand them in order.

| # | Role track | Project | Acceptance evidence |
|---|---|---|---|
| 01 | AI Evaluation Analyst / Quality Specialist | Financial Answer Evaluator | Runnable Decimal checker, authored failure cases, tests and report — implemented |
| 02 | AI Evaluation Analyst / Quality Specialist | Evidence Auditor | Exact quotes and typed facts checked against a local corpus, abstention on unsupported inference — implemented |
| 03 | AI Evaluation Analyst / Quality Specialist | Evaluation Release Gate | Matched case IDs, paired analysis, critical/cost/latency gates, enforceable CLI — implemented |
| 04 | AI Business Analyst / Finance Automation Consultant | Accounts Payable Exception Workbench | Stakeholder requirements, process map, exception queue, reviewer audit trail, synthetic user acceptance tests; extend existing invoice prototype |
| 05 | AI Business Analyst / Finance Automation Consultant | EU Grant Compliance Intake | Versioned fictional eligibility rules, document checklist, explanations and human escalation; no claims of current legal advice |
| 06 | AI Business Analyst / Finance Automation Consultant | Finance Automation Pilot Scorecard | Measured manual-vs-assisted task time, quality guardrails, cost assumptions and sensitivity; separate observed data from scenario estimates |
| 07 | Applied AI Engineer — Finance | Cited Financial Document Assistant | Real model call, retrieval, exact source spans, structured output validation, unseen evaluation set, secrets via environment |
| 08 | Applied AI Engineer — Finance | Finance Review API | Authenticated API, database, idempotency, approval state transitions, integration tests; no real ERP writes in demo |
| 09 | Applied AI Engineer — Finance | Observable Evaluation Service | Deployment instructions, real latency/token logging, bounded retries, rate limits and budget controls; live verification separately recorded |
| 10 | ML Engineer / Research Engineer preparation | Invoice Exception Classifier | Logistic-regression baseline, grouped train/validation/test split, threshold choice on validation only, class-imbalance metrics and model card |
| 11 | ML Engineer / Research Engineer preparation | Financial Time-Series Forecast Benchmark | Rolling backtests, naive baseline, leakage checks, MAE/MASE, intervals and documented failure periods |
| 12 | ML Engineer / Research Engineer preparation | Financial Reasoning Experiment | Explicit research question, baseline, controlled ablation, multiple seeds, uncertainty and reproducible negative results |

## Progression rules

- Ship code, reproducible input, output report, limitations and tests together.
- Do not add a tool to the skills list unless you can explain and use it.
- Keep training and evaluation partitions separate; never tune on held-out results.
- A synthetic benchmark cannot substantiate production performance or client impact.
- Do not claim time saved, money saved or quality improved before measuring a pilot.
- ML portfolio work is preparation; three projects alone do not demonstrate
  professional ML engineering or research experience.
- Prefer improving existing relevant repositories over multiplying shallow demos.

For each completed project: run it, change an input, explain one failure, make
one reviewed code change, and record a short English walkthrough before using
it as interview evidence.
