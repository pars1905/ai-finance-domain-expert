# 03 — Evaluation Release Gate

Compare baseline and candidate evaluation runs on exactly matched case IDs.
Return improved/regressed cases, an exact paired test, mean cost and p95
latency. Block a release when a configured quality, cost, latency or critical
failure gate fails. Passing gates means eligible for human review, not automatic
deployment. The program makes no network calls and performs no deployment.

## Run

Python 3.10+, standard library only. From this directory:

```bash
python compare.py
python compare.py runs.json --output sample-report.json
python -m unittest discover -v
python compare.py runs.json --enforce
```

The final command deliberately exits **1** because the demo has a critical
failure; this enables use as a CI gate. Invalid input also exits nonzero.
Without `--enforce`, a blocked comparison is printed with exit code 0.

From repository root: `python portfolio/03-evaluation-release-gate/compare.py`.

## Inputs and metrics

See `runs.json`: `baseline` and `candidate` arrays need identical unique
string IDs and boolean `passed`/`critical_failure` flags. Critical failures
cannot also pass. `cost_usd` and `latency_ms` must be finite non-negative
numbers. Missing pairs, duplicate IDs and non-boolean quality flags are rejected.

Policy fields:

- `max_accuracy_drop`: fraction, not percentage points written as a whole number.
- `max_mean_cost_usd`: absolute mean cost cap for the candidate.
- `max_p95_latency_ms`: candidate nearest-rank 95th percentile cap.
- Any candidate critical failure always blocks.

Accuracy is the fraction of supplied pass flags; the evaluator does not decide
these labels. The exact two-sided McNemar/binomial test uses only discordant
pairs, assuming independent paired cases. It is descriptive and is not an
additional release gate. No multiple-comparison adjustment is made.

## Demonstration

Twenty simulated pairs: baseline 16/20, candidate 18/20, four improvements,
two regressions. Candidate mean cost is $0.012 and p95 latency 700 ms. One
critical failure blocks release despite the higher overall pass rate. p=0.6875
does not establish improvement. One 3000 ms outlier is outside nearest-rank
p95 in this small batch; p95 is not maximum latency.

All outcomes, costs and latencies are authored examples, not observed model
measurements. This small dataset cannot establish real-world quality or
statistical power. For actual use: version case IDs, prompts and scorer,
fix policies before evaluation, measure real telemetry, include sufficient
independent cases and have critical labels adjudicated by a human.
