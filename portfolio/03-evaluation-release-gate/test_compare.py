import copy
import json
import unittest
from pathlib import Path
from compare import compare, p95


class ReleaseChecks(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('runs.json').read_text())

    def run_comparison(self):
        return compare(self.data['baseline'], self.data['candidate'], self.data['policy'])

    def test_improvement_cannot_hide_critical_failure(self):
        report = self.run_comparison()
        self.assertGreater(report['accuracy_delta'], 0)
        self.assertEqual(report['decision'], 'block')
        self.assertFalse(report['gates']['critical_failures'])
        self.assertEqual(len(report['improved_case_ids']), 4)
        self.assertEqual(len(report['regressed_case_ids']), 2)

    def test_identical_good_runs_eligible(self):
        self.data['candidate'] = copy.deepcopy(self.data['baseline'])
        report = self.run_comparison()
        self.assertEqual(report['decision'], 'eligible_for_human_review')
        self.assertEqual(report['exact_mcnemar_p_value'], 1)

    def test_exact_significance(self):
        for i in range(6):
            self.data['baseline'][i]['passed'] = False
        self.data['candidate'] = copy.deepcopy(self.data['baseline'])
        for i in range(6):
            self.data['candidate'][i]['passed'] = True
        self.assertEqual(self.run_comparison()['exact_mcnemar_p_value'], .03125)

    def test_missing_case_rejected(self):
        self.data['candidate'].pop()
        with self.assertRaises(ValueError):
            self.run_comparison()

    def test_duplicate_case_rejected(self):
        self.data['candidate'].append(self.data['candidate'][0])
        with self.assertRaises(ValueError):
            self.run_comparison()

    def test_cost_and_latency_gates(self):
        self.data['policy']['max_mean_cost_usd'] = .001
        self.data['policy']['max_p95_latency_ms'] = 100
        gates = self.run_comparison()['gates']
        self.assertFalse(gates['cost'])
        self.assertFalse(gates['latency'])

    def test_nonfinite_telemetry_rejected(self):
        self.data['candidate'][0]['latency_ms'] = float('nan')
        with self.assertRaises(ValueError):
            self.run_comparison()

    def test_no_bool_coercion(self):
        self.data['candidate'][0]['passed'] = 'false'
        with self.assertRaises(ValueError):
            self.run_comparison()

    def test_quality_regression_gate(self):
        self.data['candidate'] = copy.deepcopy(self.data['baseline'])
        self.data['candidate'][0]['passed'] = False
        self.assertFalse(self.run_comparison()['gates']['quality'])

    def test_p95_nearest_rank(self):
        self.assertEqual(p95(list(range(1, 21))), 19)


if __name__ == '__main__':
    unittest.main()
