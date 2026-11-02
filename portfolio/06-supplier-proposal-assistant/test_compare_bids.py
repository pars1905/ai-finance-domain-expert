import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from compare_bids import analyze


class SupplierTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('bids.json').read_text())

    def test_cost_reconciles_and_criteria_filter(self):
        report = analyze(self.data)
        by_id = {i['id']: i for i in report['items']}
        self.assertEqual(Decimal(by_id['supplier-A']['total_cost']), 10900)
        self.assertEqual(by_id['supplier-C']['finding'], 'ineligible')
        self.assertEqual(by_id['supplier-D']['finding'], 'incomplete')
        self.assertEqual(by_id['supplier-E']['finding'], 'currency_conversion_required')
        self.assertEqual({r['id'] for r in report['ranking']}, {'supplier-A', 'supplier-B'})

    def test_weight_sensitivity_changes_leader(self):
        report = analyze(self.data)
        self.assertEqual(report['ranking'][0]['id'], 'supplier-A')
        self.assertEqual(report['sensitivity_rankings']['delivery_priority'][0]['id'], 'supplier-B')
        self.assertEqual(report['decision'], 'human_selection_required')

    def test_invalid_weights_rejected(self):
        self.data['weights']['cost'] = '.9'
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_false_string_not_coerced_to_true(self):
        self.data['bids'][0]['criteria']['warranty'] = 'false'
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_missing_criterion_prevents_ranking(self):
        del self.data['bids'][0]['criteria']['security_review']
        report = analyze(self.data)
        self.assertEqual(report['items'][0]['finding'], 'incomplete')
        self.assertNotIn('supplier-A', [r['id'] for r in report['ranking']])

    def test_single_bid_safe_normalization(self):
        self.data['bids'] = self.data['bids'][:1]
        report = analyze(self.data)
        self.assertEqual(report['ranking'][0]['components']['cost'], '1')
        self.assertEqual(report['ranking'][0]['components']['delivery'], '1')

    def test_identical_bids_equal_score(self):
        twin = copy.deepcopy(self.data['bids'][0])
        twin['id'] = 'supplier-AA'
        self.data['bids'] = [self.data['bids'][0], twin]
        ranking = analyze(self.data)['ranking']
        self.assertEqual(ranking[0]['score'], ranking[1]['score'])

    def test_no_eligible_bid_returns_no_selection(self):
        self.data['bids'] = self.data['bids'][2:]
        report = analyze(self.data)
        self.assertEqual(report['decision'], 'no_comparable_bid')
        self.assertEqual(report['ranking'], [])

    def test_negative_freight_rejected(self):
        self.data['bids'][0]['freight'] = '-1'
        with self.assertRaises(ValueError):
            analyze(self.data)


if __name__ == '__main__':
    unittest.main()
