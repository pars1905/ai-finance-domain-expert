"""Rolling one-step revenue forecast with historical-only seasonal benchmarks."""
import argparse
import json
import math
import random
from pathlib import Path


def series(seed=43, n=72):
    rng = random.Random(seed)
    return [round(100 + .7 * t + 8 * math.sin(2 * math.pi * t / 12) + rng.gauss(0, 3), 2)
            for t in range(n)]


def median(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def evaluate(values, start=36, season=12):
    if len(values) < start + 12 or start < season * 2 or season < 2 or any(not math.isfinite(v) for v in values):
        raise ValueError('Insufficient finite history')
    rows = []
    for t in range(start, len(values)):
        history = values[:t]
        naive = history[-season]
        # Estimate drift from only historical matched-season differences.
        diffs = [history[i] - history[i-season] for i in range(season, t)]
        drift = median(diffs)
        adjusted = naive + drift
        calibration = [abs(history[i] - (history[i-season] + median(diffs[:i-season])))
                       for i in range(2*season, t)]
        radius = sorted(calibration)[max(0, math.ceil(.9 * len(calibration)) - 1)] if calibration else 0
        rows.append({'time': t, 'actual': values[t], 'seasonal_naive': round(naive, 2),
                     'seasonal_drift': round(adjusted, 2), 'lower': round(adjusted-radius, 2),
                     'upper': round(adjusted+radius, 2), 'calibration_n': len(calibration)})
    scale = sum(abs(values[i] - values[i-season]) for i in range(season, start)) / (start-season)
    if scale <= 0:
        raise ValueError('MASE scale must be positive')
    def metrics(key):
        errors = [abs(r['actual'] - r[key]) for r in rows]
        return {'mae': round(sum(errors)/len(errors), 4), 'mase': round(sum(errors)/len(errors)/scale, 4)}
    return {'scope': 'authored synthetic monthly revenue; rolling one-step forecasts', 'seed': 43,
            'start': start, 'season': season, 'mase_training_scale': round(scale, 4),
            'seasonal_naive': metrics('seasonal_naive'), 'seasonal_drift': metrics('seasonal_drift'),
            'interval_coverage': round(sum(r['lower'] <= r['actual'] <= r['upper'] for r in rows)/len(rows), 4),
            'rows': rows, 'limitations': ['Intervals use historical residual quantiles, no finite-sample coverage guarantee.',
                                          'Synthetic trend and seasonality do not establish real financial forecast performance.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    result = json.dumps(evaluate(series()), indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    print(result, end='')
