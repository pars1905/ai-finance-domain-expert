"""Normalize fictional supplier proposals and examine weight sensitivity."""
import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finance_tools import cli, dec, envelope, integer, text, unique_rows


def weights(values):
    if set(values) != {'cost', 'delivery', 'payment'}:
        raise ValueError('Weights need cost, delivery and payment')
    parsed = {k: dec(v, 0, 1) for k, v in values.items()}
    if sum(parsed.values()) != 1:
        raise ValueError('Weights must sum to one')
    return parsed


def rank(eligible, weight):
    if not eligible:
        return []
    costs = [dec(i['total_cost']) for i in eligible]
    lead = [i['delivery_days'] for i in eligible]
    low, high, fast, slow = min(costs), max(costs), min(lead), max(lead)
    result = []
    for i in eligible:
        # Identical values receive equal full credit, avoiding division by zero.
        cost = (high - dec(i['total_cost'])) / (high - low) if high != low else Decimal(1)
        delivery = Decimal(slow - i['delivery_days']) / (slow - fast) if slow != fast else Decimal(1)
        payment = Decimal(min(i['payment_days'], 90)) / 90
        score = 100 * (weight['cost'] * cost + weight['delivery'] * delivery + weight['payment'] * payment)
        result.append({'id': i['id'], 'score': str(score),
                       'components': {'cost': str(cost), 'delivery': str(delivery), 'payment': str(payment)}})
    return sorted(result, key=lambda r: (-dec(r['score']), r['id']))


def analyze(data):
    """Eligibility checks, total-cost comparison and explicit scoring assumptions."""
    quantity, years = integer(data['quantity'], 1), integer(data['contract_years'], 1)
    required = data['required_criteria']
    if not isinstance(required, list) or not required or any(not isinstance(c, str) or not c for c in required) or len(set(required)) != len(required):
        raise ValueError('Required criteria must be distinct non-empty strings')
    policy_weights = weights(data['weights'])
    sensitivities = {name: weights(w) for name, w in data['sensitivity_weights'].items()}
    if not sensitivities:
        raise ValueError('At least one sensitivity scenario is required')
    items = []
    numeric_fields = ('unit_price', 'freight', 'setup', 'annual_maintenance', 'delivery_days', 'payment_days')
    for bid in unique_rows(data['bids']):
        missing = [key for key in (*numeric_fields, 'criteria', 'currency', 'evidence_ref') if bid.get(key) is None]
        item = {'id': bid['id'], 'requires_human_review': True,
                'evidence': [bid['evidence_ref']] if isinstance(bid.get('evidence_ref'), str) else [],
                'missing_fields': missing, 'failed_criteria': [], 'total_cost': None}
        if missing:
            item['finding'] = 'incomplete'
            items.append(item)
            continue
        text(bid['evidence_ref'])
        if bid['currency'] != data['currency']:
            item['finding'] = 'currency_conversion_required'
            items.append(item)
            continue
        criteria = bid['criteria']
        if not isinstance(criteria, dict) or any(type(v) is not bool for v in criteria.values()):
            raise ValueError('Criterion answers must be true or false; omit unknown answers')
        item['missing_fields'] = [f'criteria/{k}' for k in required if k not in criteria]
        item['failed_criteria'] = [k for k in required if criteria.get(k) is False]
        unit, freight, setup, annual = (dec(bid[k], 0, 1000000000) for k in numeric_fields[:4])
        delivery, payment = integer(bid['delivery_days']), integer(bid['payment_days'])
        total = quantity * unit + freight + setup + years * annual
        if total <= 0:
            raise ValueError('Total contract cost must be positive')
        item.update(total_cost=str(total), delivery_days=delivery, payment_days=payment,
                    cost_components={'goods': str(quantity * unit), 'freight': str(freight),
                                     'setup': str(setup), 'maintenance': str(years * annual)})
        item['finding'] = ('ineligible' if item['failed_criteria'] else
                           ('incomplete' if item['missing_fields'] else 'eligible_for_comparison'))
        items.append(item)
    eligible = [i for i in items if i['finding'] == 'eligible_for_comparison']
    ranking = rank(eligible, policy_weights)
    scenarios = {name: rank(eligible, w) for name, w in sensitivities.items()}
    return envelope(data, 'Supplier Proposal Comparison Assistant', items,
                    quantity=quantity, contract_years=years, ranking=ranking,
                    weights=data['weights'], sensitivity_rankings=scenarios,
                    decision='human_selection_required' if ranking else 'no_comparable_bid',
                    limitations=['Relative cost/delivery scores depend on the eligible comparison set.',
                                 'Totals exclude tax, discounting and FX conversion; all bids must use comparable net terms.',
                                 'Criteria and evidence references are supplied, not independently authenticated.',
                                 'No purchase order is created; no supplier is automatically selected.'])


if __name__ == '__main__':
    cli(analyze, Path(__file__).with_name('bids.json'))
