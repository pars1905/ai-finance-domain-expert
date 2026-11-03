# 11 — Financial Time-Series Forecast Benchmark

A seeded synthetic monthly revenue series (72 periods) is forecast with rolling, one-step predictions from month 36 onward. Seasonal naive (`t−12`) is the baseline. A comparison adds the median historical matched-season change. The training prefix alone sets the MASE scale; historical residuals alone set an approximate 90% interval radius for each step. Report MAE, MASE and observed interval coverage, plus per-period predictions for failure inspection.

```bash
python portfolio/11-financial-forecast-benchmark/forecast.py --output portfolio/11-financial-forecast-benchmark/sample-report.json
python -m unittest discover -s portfolio/11-financial-forecast-benchmark -v
```

A future-value perturbation test verifies predictions through that date do not change. This is not a model for real revenue planning. The median drift is a transparent heuristic, and historical residual intervals offer no coverage guarantee under changing regimes. One synthetic series, no exogenous data, no independent forecast verification.
