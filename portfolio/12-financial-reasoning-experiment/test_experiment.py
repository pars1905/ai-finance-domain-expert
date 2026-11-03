import unittest
from experiment import cases, decision, run


class ExperimentTests(unittest.TestCase):
    def test_paired_ablation_and_negative_result(self):
        result = run()
        self.assertEqual(result['baseline_false_accept'], .5)
        self.assertEqual(result['unit_check_false_accept'], 0)
        self.assertEqual(len(result['bootstrap']), 5)
        for row in result['rows']:
            if row['kind'] == 'wrong_number':
                self.assertFalse(row['baseline_accept'])
                self.assertFalse(row['unit_check_accept'])

    def test_reproducible_and_real_checker(self):
        self.assertEqual(run(), run())
        self.assertTrue(decision(cases()[0], True))
        self.assertFalse(decision(cases()[1], True))

    def test_duplicate_ids_rejected(self):
        rows = cases()
        rows[1]['id'] = rows[0]['id']
        with self.assertRaises(ValueError):
            run(rows)
