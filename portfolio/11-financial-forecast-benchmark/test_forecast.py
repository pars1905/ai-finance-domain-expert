import unittest
from forecast import evaluate, series


class ForecastTests(unittest.TestCase):
    def test_rolling_and_finite_metrics(self):
        r = evaluate(series())
        self.assertEqual(len(r['rows']), 36)
        self.assertEqual(r['rows'][0]['time'], 36)
        self.assertGreater(r['seasonal_naive']['mase'], 0)
        self.assertTrue(0 <= r['interval_coverage'] <= 1)

    def test_no_future_leakage(self):
        original = series()
        changed = original[:]
        changed[60:] = [99999] * 12
        a, b = evaluate(original)['rows'], evaluate(changed)['rows']
        for first, second in zip(a, b):
            if first['time'] <= 60:
                for field in ('seasonal_naive', 'seasonal_drift', 'lower', 'upper'):
                    self.assertEqual(first[field], second[field])

    def test_invalid_and_zero_scale(self):
        with self.assertRaises(ValueError):
            evaluate([1] * 72)
        with self.assertRaises(ValueError):
            evaluate([float('nan')] * 72)
        with self.assertRaises(ValueError):
            evaluate(series()[:24])
