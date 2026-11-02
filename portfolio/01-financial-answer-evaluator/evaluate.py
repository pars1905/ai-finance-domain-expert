"""Deterministic checks of structured financial answers; no model judge."""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('Expected a decimal number')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal') from exc
    if not result.is_finite():
        raise ValueError('Non-finite number')
    return result


def reference(task, inputs):
    if not isinstance(inputs, dict):
        raise ValueError('Inputs must be an object')
    x = {k: number(v) for k, v in inputs.items()}
    if task == 'wacc':
        e, d, re, rd, tax = (x[k] for k in ('equity', 'debt', 'cost_equity', 'cost_debt', 'tax_rate'))
        if min(e, d, re, rd) < 0 or e + d <= 0 or not 0 <= tax <= 1:
            raise ValueError('Invalid WACC assumptions')
        return (e * re + d * rd * (1 - tax)) / (e + d), 'ratio'
    if task == 'dcf_terminal':
        fcf, rate, growth = (x[k] for k in ('fcf_current', 'discount_rate', 'growth_rate'))
        if rate <= growth or rate <= -1 or growth <= -1:
            raise ValueError('Terminal value requires r > g and rates > -1')
        return fcf * (1 + growth) / (rate - growth), 'currency'
    if task == 'gross_margin':
        revenue, cogs = (x[k] for k in ('revenue', 'cogs'))
        if revenue <= 0 or cogs < 0:
            raise ValueError('Revenue must be positive and COGS non-negative')
        return (revenue - cogs) / revenue, 'ratio'
    raise ValueError('Unsupported task')


def assess(case):
    """Input/assumption errors are review, never a silently accepted answer."""
    try:
        expected, unit = reference(case['task'], case['inputs'])
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        return {'verdict': 'review', 'reason': 'invalid_input', 'detail': str(exc)}
    try:
        response = case['response']
        answer = number(response['value'])
        if response['unit'] != unit:
            return {'verdict': 'fail', 'reason': 'unit_mismatch'}
    except (KeyError, TypeError, ValueError):
        return {'verdict': 'fail', 'reason': 'invalid_response'}
    # Absolute tolerance is in the returned unit; rates are decimal ratios.
    tolerance = Decimal('0.0001') if unit == 'ratio' else Decimal('0.01')
    passed = abs(answer - expected) <= tolerance
    return {'verdict': 'pass' if passed else 'fail',
            'reason': 'within_tolerance' if passed else 'numeric_mismatch',
            'expected': str(expected), 'actual': str(answer),
            'unit': unit, 'absolute_tolerance': str(tolerance)}


def evaluate(cases):
    ids = [c['id'] for c in cases]
    if not cases or len(ids) != len(set(ids)):
        raise ValueError('Cases must be non-empty and have unique IDs')
    rows = [{'id': c['id'], **assess(c)} for c in cases]
    report = {'scope': 'synthetic structured-answer checks; not model accuracy',
              'cases': len(rows), 'results': rows,
              'verdict_counts': {v: sum(r['verdict'] == v for r in rows)
                                 for v in ('pass', 'fail', 'review')}}
    labeled = [(c, r) for c, r in zip(cases, rows) if 'expected_verdict' in c]
    if labeled:
        report['checker_agreement'] = {
            'matches': sum(c['expected_verdict'] == r['verdict'] for c, r in labeled),
            'labeled_cases': len(labeled)}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path,
                        default=Path(__file__).with_name('cases.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(evaluate(json.loads(args.input.read_text())), indent=2)
    if args.output:
        args.output.write_text(result + '\n')
    print(result)
