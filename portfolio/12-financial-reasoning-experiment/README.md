# 12 — Financial Reasoning Experiment

Research question: does explicit unit checking reduce false acceptance of numerically plausible wrong-unit financial answers? Baseline and treatment use the same project-01 `assess` implementation and the same 12 authored gross-margin answers. The single ablation changes only the unit check. Eight negative answers contain four wrong units and four wrong numbers. The baseline ignores unit names; treatment enforces them. Five fixed resampling seeds each generate 500 paired bootstrap replicates for descriptive intervals. The wrong-number cases provide an explicit negative result: unit checking does not fix their arithmetic.

```bash
python portfolio/12-financial-reasoning-experiment/experiment.py --output portfolio/12-financial-reasoning-experiment/sample-report.json
python -m unittest discover -s portfolio/12-financial-reasoning-experiment -v
```

This measures a deterministic checker on hand-authored fixtures, not an LLM's financial reasoning. Cases were designed to show the unit issue; bootstrap intervals reflect only this tiny case set and do not imply generalization. No live model, human adjudication, independent held-out sample or causal field impact. For future work, preregister an independently authored question set, freeze checker versions, collect permitted model answers, and blind-review labels.
