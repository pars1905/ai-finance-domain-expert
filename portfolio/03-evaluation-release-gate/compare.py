"""Paired quality comparison with explicit release gates; no model calls."""
import argparse
import json
import math
from pathlib import Path


def validate(rows):
    if not rows:
        raise ValueError('Empty run')
    ids = [r['id'] for r in rows]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('Run IDs must be unique non-empty strings')
    for r in rows:
        if type(r['passed']) is not bool or type(r['critical_failure']) is not bool:
            raise ValueError('Quality flags must be booleans')
        for field in ('cost_usd', 'latency_ms'):
            v = r[field]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
                raise ValueError('Cost/latency must be finite non-negative numbers')
        if r['passed'] and r['critical_failure']:
            raise ValueError('A critical failure cannot pass')
    return {r['id']: r for r in rows}


def p95(values):
    return sorted(values)[math.ceil(.95 * len(values)) - 1]


def compare(baseline, candidate, policy):
    a, b = validate(baseline), validate(candidate)
    if a.keys() != b.keys():
        raise ValueError('Paired runs must contain exactly the same case IDs')
    for name in ('max_accuracy_drop', 'max_mean_cost_usd', 'max_p95_latency_ms'):
        value = policy[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('Invalid policy threshold')
    if policy['max_accuracy_drop'] > 1:
        raise ValueError('Accuracy drop must be a fraction in [0,1]')
    n = len(a)
    baseline_accuracy = sum(r['passed'] for r in a.values()) / n
    accuracy = sum(r['passed'] for r in b.values()) / n
    improved = [i for i in a if not a[i]['passed'] and b[i]['passed']]
    regressed = [i for i in a if a[i]['passed'] and not b[i]['passed']]
    discordant = len(improved) + len(regressed)
    # Exact two-sided McNemar/binomial test on discordant paired outcomes.
    tail = sum(math.comb(discordant, k) for k in range(min(len(improved), len(regressed)) + 1))
    p_value = min(1., 2 * tail / 2 ** discordant) if discordant else 1.
    mean_cost = sum(r['cost_usd'] for r in b.values()) / n
    latency = p95([r['latency_ms'] for r in b.values()])
    critical = [i for i in b if b[i]['critical_failure']]
    gates = {'quality': accuracy + 1e-12 >= baseline_accuracy - policy['max_accuracy_drop'],
             'cost': mean_cost <= policy['max_mean_cost_usd'],
             'latency': latency <= policy['max_p95_latency_ms'],
             'critical_failures': not critical}
    return {'scope': 'paired supplied outcomes; synthetic demo is not model performance',
            'cases': n, 'baseline_accuracy': baseline_accuracy,
            'candidate_accuracy': accuracy, 'accuracy_delta': accuracy - baseline_accuracy,
            'improved_case_ids': improved, 'regressed_case_ids': regressed,
            'critical_failure_case_ids': critical,
            'exact_mcnemar_p_value': p_value,
            'candidate_mean_cost_usd': mean_cost,
            'candidate_p95_latency_ms': latency,
            'policy': policy, 'gates': gates,
            'decision': 'eligible_for_human_review' if all(gates.values()) else 'block'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path,
                        default=Path(__file__).with_name('runs.json'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--enforce', action='store_true', help='Exit 1 for a blocked release')
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    report = compare(data['baseline'], data['candidate'], data['policy'])
    result = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(result + '\n')
    print(result)
    if args.enforce and report['decision'] == 'block':
        raise SystemExit(1)
