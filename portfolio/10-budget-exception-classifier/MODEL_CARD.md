# Model card — synthetic budget exception baseline

- Intended use: show a review-priority classifier workflow; a person must inspect every consequential flag.
- Data: 30 fictional units × 8 periods; code-generated and seeded. Labels come from a rule involving generated features and noise. No customer, employee or invoice data.
- Split: held-out groups are disjoint between train, validation and test. Validation F1 chooses a threshold from 0.10–0.90; test labels do not influence it. Group periods may still share a synthetic generation mechanism.
- Model: standardized four numeric features plus balanced logistic regression. Class weighting is a baseline response to imbalance, not a fairness guarantee.
- Evidence: see generated `sample-report.json` for partition sizes, positive counts, precision/recall/F1, average precision and confusion matrices. The small single-seed test is descriptive only.
- Limitations: artificial labels share assumptions with the features; no independent expert labels, temporal holdout, probability calibration, error costs, subgroup fairness audit or prospective pilot. Do not use for decisions on actual budgets without those checks.
