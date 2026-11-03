import unittest
from classify import fixture, evaluate


class ClassifierTests(unittest.TestCase):
    def test_group_separation_and_reproducibility(self):
        a = evaluate(fixture())
        self.assertEqual(a, evaluate(fixture()))
        groups = [set(a[k]['groups']) for k in ('train', 'validation', 'test')]
        self.assertFalse(groups[0] & groups[1] | groups[0] & groups[2] | groups[1] & groups[2])
        self.assertEqual(sum(a[k]['n'] for k in ('train', 'validation', 'test')), 240)

    def test_imbalance_metrics_and_threshold(self):
        a = evaluate(fixture())
        self.assertTrue(0 < a['threshold_selected_on_validation'] < 1)
        self.assertEqual(sum(a['test']['confusion_matrix_tn_fp_fn_tp']), a['test']['n'])
        self.assertLess(a['test']['positives'], a['test']['n'])

    def test_invalid_groups_and_nonfinite(self):
        with self.assertRaises(ValueError):
            evaluate(fixture()[:8])
        rows = fixture()
        rows[0]['absolute_variance'] = float('nan')
        with self.assertRaises(ValueError):
            evaluate(rows)
