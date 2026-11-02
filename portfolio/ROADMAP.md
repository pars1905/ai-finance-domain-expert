# Twelve-project roadmap

Projects 01–08 are implemented as local prototypes. Items 09–12 are plans, not completed work
and must not be listed as completed CV projects. Build and understand them in order.

| # | Role track | Project | Acceptance evidence |
|---|---|---|---|
| 01 | AI Evaluation Analyst / Quality Specialist | Financial Answer Evaluator | Runnable Decimal checker, authored failure cases, tests and report — implemented |
| 02 | AI Evaluation Analyst / Quality Specialist | Evidence Auditor | Exact quotes and typed facts checked against a local corpus, abstention on unsupported inference — implemented |
| 03 | AI Evaluation Analyst / Quality Specialist | Evaluation Release Gate | Matched case IDs, paired analysis, critical/cost/latency gates, enforceable CLI — implemented |
| 04 | AI Business Analyst / Finance Automation Consultant | [Budget Variance Investigation Assistant](04-budget-variance-assistant/) | Budget-versus-actual reconciliation, price/volume variance decomposition, evidence-linked explanations, analyst review and synthetic acceptance tests; separate calculated drivers from unverified causal hypotheses — implemented as offline prototype; optional AI adapter mocked, not live verified |
| 05 | AI Business Analyst / Finance Automation Consultant | [Cash Collection Prioritization Workbench](05-cash-collection-workbench/) | Synthetic customer balance snapshots and collection histories, transparent overdue/exposure ranking, what-if cash scenarios and human-reviewed action queue; no customer messages or fabricated recovery results — implemented as offline prototype; optional AI adapter mocked, not live verified |
| 06 | AI Business Analyst / Finance Automation Consultant | [Supplier Proposal Comparison Assistant](06-supplier-proposal-assistant/) | Fictional supplier bids, required-criteria checks, total-cost normalization, evidence-linked tradeoffs and weight sensitivity; flag missing data and keep supplier selection with the reviewer — implemented as offline prototype; optional AI adapter mocked, not live verified |
| 07 | Applied AI Engineer — Finance | [Cited Financial Document Assistant](07-cited-financial-assistant/) | Filtered lexical retrieval, exact source spans, structured draft/citation validation, separate authored development/holdout cases, secrets via environment — prototype implemented; real API request path mocked end-to-end, live model validation still pending |
| 08 | Applied AI Engineer — Finance | [Finance Review API](08-finance-review-api/) | Authenticated loopback HTTP, role-separated approval, immutable report snapshots, persistent SQLite, transactional idempotency and optimistic version checks — real HTTP/concurrency/rollback tests implemented; local mock receipts only, no real ERP writes |
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

