# 10 — Budget Exception Classifier

A logistic-regression baseline for routing synthetic budget variances to human review. This extends project 04 instead of duplicating the user's existing invoice repository. Features are variance percentage, absolute variance, days since review and missing-evidence flag. The unit ID is used only for grouped splitting, never as a feature. A fixed outer group split holds out units; the inner group split creates validation units. F1 threshold is selected only on validation; the test set is scored once in the code path. Report precision, recall, average precision and confusion matrix to expose class imbalance.

```bash
python -m pip install -r portfolio/10-budget-exception-classifier/requirements.txt
python portfolio/10-budget-exception-classifier/classify.py --output portfolio/10-budget-exception-classifier/sample-report.json
python -m unittest discover -s portfolio/10-budget-exception-classifier -v
```

The fixture contains 240 authored rows in 30 groups; labels follow a noisy rule related to the features. Metrics therefore test software workflow, not actual financial exception detection. No invoice data, real client decisions, calibrated probabilities or autonomous approvals. See [MODEL_CARD.md](MODEL_CARD.md).
