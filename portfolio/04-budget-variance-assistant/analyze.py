"""Reconcile budget variances and route material items to an analyst."""
import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finance_tools import cli, dec, envelope, integer, text, unique_rows


def analyze(data):
    """Revenue/expense price-volume bridge with analyst review; no causal inference."""
    policy = data['policy']
    absolute = dec(policy['absolute_threshold'], 0)
    relative = dec(policy['relative_threshold'], 0, 1)
    period = text(data['period'])
    items = []
    totals = {k: Decimal(0) for k in ('budget', 'actual', 'variance', 'volume_effect', 'price_effect')}
    for row in unique_rows(data['lines']):
        if row['kind'] not in ('revenue', 'expense'):
            raise ValueError('Kind must be revenue or expense')
        # Whole units and two-decimal unit prices avoid a hidden rounding residual.
        bq, aq = integer(row['budget_qty']), integer(row['actual_qty'])
        bp, ap = dec(row['budget_unit_price'], 0, 1000000000), dec(row['actual_unit_price'], 0, 1000000000)
        if bp != bp.quantize(Decimal('.01')) or ap != ap.quantize(Decimal('.01')):
            raise ValueError('Unit prices must have at most two decimal places')
        budget, actual = bq * bp, aq * ap
        variance = actual - budget
        volume, price = (aq - bq) * bp, aq * (ap - bp)
        for key, expected in [('budget_total', budget), ('actual_total', actual)]:
            if key in row and dec(row[key], 0) != expected:
                raise ValueError(f"{row['id']}: {key} does not reconcile")
        favorable = variance >= 0 if row['kind'] == 'revenue' else variance <= 0
        ratio = abs(variance) / budget if budget else None
        material = abs(variance) >= absolute and (ratio is None or ratio >= relative)
        material = material and variance != 0
        effects = dict(budget=budget, actual=actual, variance=variance,
                       volume_effect=volume, price_effect=price)
        for k, v in effects.items():
            totals[k] += v if row['kind'] == 'revenue' else -v
        finding = ('no_variance' if variance == 0 else
                   ('favorable' if favorable else 'unfavorable'))
        items.append({'id': row['id'], 'kind': row['kind'], 'period': period,
                      **{k: str(v) for k, v in effects.items()},
                      'absolute_variance_ratio': str(ratio) if ratio is not None else None,
                      'finding': finding, 'requires_human_review': material,
                      'evidence': [f"lines/{row['id']}/{k}" for k in
                                   ('budget_qty', 'actual_qty', 'budget_unit_price', 'actual_unit_price')],
                      'review_questions': ['Verify source quantities and prices.',
                                           'Investigate mix, timing or one-off effects; causes are unproven.']
                                          if material else []})
    return envelope(data, 'Budget Variance Investigation Assistant', items,
                    period=period, policy=policy,
                    operating_contribution={k: str(v) for k, v in totals.items()},
                    decomposition='volume=(Aq-Bq)*Bp; price=Aq*(Ap-Bp); revenue minus expense totals',
                    limitations=['Arithmetic drivers are not causal explanations.',
                                 'Whole-unit quantities; two-decimal prices; single currency and period.'])


if __name__ == '__main__':
    cli(analyze, Path(__file__).with_name('budget.json'))
