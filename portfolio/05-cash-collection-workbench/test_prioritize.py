import json
import unittest
from decimal import Decimal
from pathlib import Path
from prioritize import analyze


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('customers.json').read_text())

    def test_expected_queue(self):
        report = analyze(self.data)
        self.assertEqual(report['items'][0]['id'], 'customer-A')
        by_id = {i['id']: i for i in report['items']}
        self.assertEqual(by_id['customer-C']['finding'], 'resolve_dispute')
        self.assertEqual(by_id['customer-D']['finding'], 'await_active_promise')
        self.assertEqual(by_id['customer-E']['finding'], 'not_overdue')
        self.assertEqual(by_id['customer-F']['finding'], 'settled')
        self.assertEqual(by_id['customer-G']['finding'], 'review_collection_action')

    def test_scenarios_exclude_disputes_and_promises(self):
        report = analyze(self.data)
        # A:8000*.20, B:5000*.65, G:2000*.40; all others excluded.
        self.assertEqual(Decimal(report['scenario_collection_amounts']['base']), 5650)

    def test_zero_balances_do_not_divide_by_zero(self):
        for row in self.data['customers']:
            row['balance'] = row['disputed_amount'] = '0'
        report = analyze(self.data)
        self.assertTrue(all(Decimal(i['priority_score']) == 0 for i in report['items']))
        self.assertEqual(Decimal(report['scenario_collection_amounts']['base']), 0)

    def test_invalid_dispute_rejected(self):
        self.data['customers'][0]['disputed_amount'] = '10001'
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_rates_cannot_exceed_one(self):
        self.data['scenarios']['base']['1-30'] = '1.1'
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_future_contact_rejected(self):
        self.data['customers'][0]['last_contact_date'] = '2026-11-01'
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_due_today_not_overdue(self):
        self.data['customers'][0]['due_date'] = self.data['as_of']
        item = next(i for i in analyze(self.data)['items'] if i['id'] == 'customer-A')
        self.assertEqual(item['finding'], 'not_overdue')

    def test_promise_today_is_active(self):
        self.data['customers'][0]['promise_date'] = self.data['as_of']
        item = next(i for i in analyze(self.data)['items'] if i['id'] == 'customer-A')
        self.assertEqual(item['finding'], 'await_active_promise')

    def test_input_order_does_not_change_priority(self):
        before = analyze(self.data)['items']
        self.data['customers'].reverse()
        self.assertEqual(before, analyze(self.data)['items'])


if __name__ == '__main__':
    unittest.main()
