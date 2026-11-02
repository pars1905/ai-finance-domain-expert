import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path
from analyze import analyze


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('budget.json').read_text())

    def test_sales_price_volume_bridge(self):
        item = analyze(self.data)['items'][0]
        self.assertEqual(Decimal(item['budget']), 20000)
        self.assertEqual(Decimal(item['variance']), 2800)
        self.assertEqual(Decimal(item['volume_effect']), 4000)
        self.assertEqual(Decimal(item['price_effect']), -1200)
        self.assertEqual(item['finding'], 'favorable')

    def test_every_line_and_contribution_reconciles(self):
        report = analyze(self.data)
        for item in [*report['items'], report['operating_contribution']]:
            self.assertEqual(Decimal(item['variance']), Decimal(item['price_effect']) + Decimal(item['volume_effect']))
            self.assertEqual(Decimal(item['actual']) - Decimal(item['budget']), Decimal(item['variance']))
        self.assertEqual(Decimal(report['operating_contribution']['variance']), 100)

    def test_expense_and_new_spend_review(self):
        items = analyze(self.data)['items']
        self.assertEqual(items[1]['finding'], 'unfavorable')
        self.assertTrue(items[1]['requires_human_review'])
        self.assertIsNone(items[3]['absolute_variance_ratio'])
        self.assertTrue(items[3]['requires_human_review'])
        self.assertFalse(items[2]['requires_human_review'])

    def test_relative_and_absolute_thresholds_both_apply(self):
        self.data['policy']['absolute_threshold'] = '3000'
        self.assertFalse(analyze(self.data)['items'][0]['requires_human_review'])
        self.data['policy']['absolute_threshold'] = '500'
        self.data['policy']['relative_threshold'] = '.20'
        self.assertFalse(analyze(self.data)['items'][0]['requires_human_review'])

    def test_bad_ledger_total_rejected(self):
        self.data['lines'][0]['actual_total'] = '22801'
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_negative_and_fractional_quantities_rejected(self):
        for value in (-1, '1.5', True):
            self.data['lines'][0]['actual_qty'] = value
            with self.assertRaises(ValueError):
                analyze(self.data)

    def test_duplicate_ids_rejected(self):
        self.data['lines'].append(copy.deepcopy(self.data['lines'][0]))
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_subcent_price_rejected(self):
        self.data['lines'][0]['actual_unit_price'] = '190.001'
        with self.assertRaises(ValueError):
            analyze(self.data)

    def test_material_threshold_equality(self):
        self.data['policy'] = {'absolute_threshold': '2800', 'relative_threshold': '.14'}
        self.assertTrue(analyze(self.data)['items'][0]['requires_human_review'])


if __name__ == '__main__':
    unittest.main()
