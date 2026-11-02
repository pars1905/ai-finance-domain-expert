import copy
import json
import unittest
from pathlib import Path
from evaluate import assess, evaluate, number, reference


class FinancialChecks(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads(Path(__file__).with_name('cases.json').read_text())

    def test_authored_cases(self):
        for case in self.cases:
            with self.subTest(case=case['id']):
                self.assertEqual(assess(case)['verdict'], case['expected_verdict'])

    def test_reject_nonfinite_and_boolean(self):
        for x in ('Infinity', '-Infinity', 'NaN', True, None, [], {}):
            with self.subTest(value=x), self.assertRaises(ValueError):
                number(x)

    def test_margin_tolerance_boundary(self):
        case = copy.deepcopy(self.cases[11])
        case['response']['value'] = '0.3501'
        self.assertEqual(assess(case)['verdict'], 'pass')
        case['response']['value'] = '0.3501001'
        self.assertEqual(assess(case)['verdict'], 'fail')

    def test_monotonic_tax_shield(self):
        inputs = self.cases[0]['inputs'].copy()
        lower, _ = reference('wacc', inputs)
        inputs['tax_rate'] = '0'
        higher, _ = reference('wacc', inputs)
        self.assertLess(lower, higher)

    def test_invalid_inputs_need_review(self):
        for inputs in (None, {}, {'revenue': 'NaN', 'cogs': 1}, {'revenue': 1, 'cogs': -1}):
            self.assertEqual(assess({'task': 'gross_margin', 'inputs': inputs})['verdict'], 'review')

    def test_bad_response_fails(self):
        case = copy.deepcopy(self.cases[0])
        for response in (None, {}, {'value': True, 'unit': 'ratio'}):
            case['response'] = response
            self.assertEqual(assess(case)['verdict'], 'fail')

    def test_empty_or_duplicate_batch_rejected(self):
        for cases in ([], [self.cases[0], self.cases[0]]):
            with self.assertRaises(ValueError):
                evaluate(cases)


if __name__ == '__main__':
    unittest.main()
