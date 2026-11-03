"""Paired ablation: does a unit check reject numerically plausible wrong-unit answers?"""
import argparse
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / '01-financial-answer-evaluator' / 'evaluate.py'
spec = importlib.util.spec_from_file_location('financial_evaluator', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def cases():
    base = {'task': 'gross_margin', 'inputs': {'revenue': '100', 'cogs': '60'}}
    samples = []
    for i in range(12):
        kind = ('correct', 'wrong_unit', 'wrong_number')[i % 3]
        response = {'value': '0.4' if kind != 'wrong_number' else '0.7',
                    'unit': 'percent' if kind == 'wrong_unit' else 'ratio'}
        samples.append({'id': str(i), **base, 'kind': kind, 'response': response})
    return samples


def decision(case, check_unit):
    if check_unit:
        return module.assess(case)['verdict'] == 'pass'
    altered = {**case, 'response': {**case['response'], 'unit': 'ratio'}}
    return module.assess(altered)['verdict'] == 'pass'


def run(rows=None, seeds=(7, 11, 23, 47, 91)):
    rows = cases() if rows is None else rows
    ids = [c['id'] for c in rows]
    if len(ids) != len(set(ids)) or not rows or any(c['kind'] not in ('correct', 'wrong_unit', 'wrong_number') for c in rows):
        raise ValueError('Invalid authored cases')
    paired = [{'id': c['id'], 'kind': c['kind'], 'baseline_accept': decision(c, False),
               'unit_check_accept': decision(c, True)} for c in rows]
    def false_accept(sample, key):
        negatives = [r for r in sample if r['kind'] != 'correct']
        return sum(r[key] for r in negatives) / len(negatives) if negatives else 0
    baseline = false_accept(paired, 'baseline_accept')
    treatment = false_accept(paired, 'unit_check_accept')
    bootstrap = []
    for seed in seeds:
        rng = random.Random(seed)
        negatives = [r for r in paired if r['kind'] != 'correct']
        diffs = []
        for _ in range(500):
            sample = rng.choices(negatives, k=len(negatives))
            diffs.append(false_accept(sample, 'baseline_accept') - false_accept(sample, 'unit_check_accept'))
        bootstrap.append({'seed': seed, 'mean_improvement': round(sum(diffs)/len(diffs), 4),
                          'percentile_interval': [round(sorted(diffs)[12], 4), round(sorted(diffs)[487], 4)]})
    return {'question': 'Does checking the unit reduce false acceptance of authored financial answers?',
            'scope': 'deterministic checker ablation on authored gross-margin answers; no model or human participants',
            'baseline_false_accept': baseline, 'unit_check_false_accept': treatment,
            'paired_improvement': baseline-treatment, 'bootstrap': bootstrap,
            'negative_result': 'The unit check does not change rejection of wrong-number answers.',
            'rows': paired, 'limitations': ['Cases deliberately contain wrong units; effect is fixture-dependent.',
                                           'Bootstrap resamples authored cases and does not prove real-world generalization.',
                                           'Seeds change uncertainty resampling, not the deterministic checker.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    rendered = json.dumps(run(), indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end='')
