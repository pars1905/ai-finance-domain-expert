import unittest
from forecast import evaluate, series, median


class ForecastTests(unittest.TestCase):
    def test_even_sample_median(self):
        self.assertEqual(median([1, 3, 9, 11]), 6)
        history = list(range(72))
        history[24] += 2
        report = evaluate(history)
        differences = [history[i] - history[i - 12] for i in range(12, 36)]
        self.assertEqual(report['rows'][0]['seasonal_drift'],
                         history[24] + median(differences))

    def test_invalid_window_parameters(self):
        for start, season in ((36.5, 12), (36, 12.5), (24, 12), (True, 12)):
            with self.subTest(start=start, season=season), self.assertRaises(ValueError):
                evaluate(series(), start=start, season=season)

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
