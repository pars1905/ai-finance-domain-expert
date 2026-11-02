"""Prioritize fictional business customer balances, with explicit scenario assumptions."""
import sys
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finance_tools import cli, dec, envelope, integer, iso_date, unique_rows


def analyze(data):
    """Transparent heuristic collection queue; scenarios are not recovery forecasts."""
    as_of = iso_date(data['as_of'])
    scenarios = data['scenarios']
    if not scenarios:
        raise ValueError('At least one collection scenario is required')
    for rates in scenarios.values():
        for bucket in ('1-30', '31-60', '61+'):
            dec(rates[bucket], 0, 1)
    items = []
    for row in unique_rows(data['customers']):
        balance, disputed = dec(row['balance'], 0), dec(row['disputed_amount'], 0)
        if disputed > balance:
            raise ValueError('Dispute cannot exceed balance')
        days = max(0, (as_of - iso_date(row['due_date'])).days)
        broken = integer(row['broken_promises'])
        contact = iso_date(row['last_contact_date']) if row.get('last_contact_date') else None
        if contact and contact > as_of:
            raise ValueError('Last contact cannot be in the future')
        promise = iso_date(row['promise_date']) if row.get('promise_date') else None
        available = balance - disputed
        if balance == 0:
            finding = 'settled'
        elif not days:
            finding = 'not_overdue'
        elif available == 0:
            finding = 'resolve_dispute'
        elif promise and promise >= as_of:
            finding = 'await_active_promise'
        else:
            finding = 'review_collection_action'
        bucket = '1-30' if days <= 30 else ('31-60' if days <= 60 else '61+')
        items.append({'id': row['id'], 'balance': str(balance), 'disputed_amount': str(disputed),
                      'undisputed_balance': str(available), 'days_overdue': days, 'bucket': bucket,
                      'broken_promises': broken, 'finding': finding,
                      'requires_human_review': finding in ('resolve_dispute', 'review_collection_action'),
                      'priority_score': '0', 'evidence': [f"customers/{row['id']}"],
                      'suggested_action': {'resolve_dispute': 'Investigate disputed amount before collection.',
                                           'review_collection_action': 'Review balance and choose a contact plan.',
                                           'await_active_promise': 'Monitor agreed promise; no automatic contact.'
                                           }.get(finding, 'Monitor only.')})
    actionable = [i for i in items if i['finding'] == 'review_collection_action']
    max_balance = max((dec(i['undisputed_balance']) for i in actionable), default=Decimal(1))
    for item in actionable:
        amount_component = 50 * dec(item['undisputed_balance']) / max_balance
        age_component = Decimal(30) * min(item['days_overdue'], 90) / 90
        history_component = Decimal(20) * min(item['broken_promises'], 3) / 3
        item['priority_score'] = str((amount_component + age_component + history_component).quantize(Decimal('.01')))
    items.sort(key=lambda i: (-dec(i['priority_score']), -dec(i['undisputed_balance']), i['id']))
    estimates = {}
    for name, rates in scenarios.items():
        cash = sum((dec(i['undisputed_balance']) * dec(rates[i['bucket']]) for i in actionable), Decimal(0))
        estimates[name] = str(cash.quantize(Decimal('.01')))
    return envelope(data, 'Cash Collection Prioritization Workbench', items,
                    as_of=data['as_of'], scenario_collection_amounts=estimates,
                    scenario_rates=scenarios,
                    scenario_scope='Actionable overdue undisputed balances only; excludes active promises.',
                    score_formula='50*balance/max_actionable_balance + 30*min(days,90)/90 + 20*min(broken_promises,3)/3',
                    limitations=['Heuristic ordering is not a repayment probability or credit assessment.',
                                 'Scenario amounts are assumptions, not observed or predicted recoveries.',
                                 'One due date per customer snapshot; not an invoice aging ledger.'])


if __name__ == '__main__':
    cli(analyze, Path(__file__).with_name('customers.json'))
