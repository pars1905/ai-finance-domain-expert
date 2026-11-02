import copy
import json
import unittest
from pathlib import Path
from audit import audit, audit_claim


class EvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('claims.json').read_text())

    def test_demo_expected_statuses(self):
        statuses = {r['id']: r['status'] for r in audit(self.data)['results']}
        self.assertEqual(statuses, dict(zip(
            ['quote-valid', 'quote-invented', 'quote-empty', 'unknown-source', 'fact-valid',
             'fact-wrong', 'wrong-period', 'wrong-unit', 'unsupported-inference'],
            ['pass', 'fail', 'review', 'fail', 'pass', 'fail', 'review', 'review', 'review'])))

    def test_duplicate_source_rejected(self):
        self.data['sources'] *= 2
        with self.assertRaises(ValueError):
            audit(self.data)

    def test_ambiguous_fact_needs_review(self):
        self.data['sources'][0]['facts'] *= 2
        result = audit(self.data)['results'][4]
        self.assertEqual(result['reason'], 'missing_or_ambiguous_fact')

    def test_nan_cannot_match(self):
        self.data['claims'][4]['value'] = 'NaN'
        self.assertEqual(audit(self.data)['results'][4]['status'], 'review')

    def test_negated_quote_not_substituted(self):
        self.data['claims'][0]['quote'] = 'Figures are audited.'
        self.assertEqual(audit(self.data)['results'][0]['status'], 'fail')

    def test_quote_presence_does_not_verify_inference(self):
        claim = copy.deepcopy(self.data['claims'][0])
        claim['interpretation'] = 'Therefore every figure is reliable.'
        sources = {s['id']: s for s in self.data['sources']}
        self.assertEqual(audit_claim(claim, sources)['reason'], 'exact_quote_found')
        claim['kind'] = 'inference'
        self.assertEqual(audit_claim(claim, sources)['status'], 'review')

    def test_empty_batch_rejected(self):
        self.data['claims'] = []
        with self.assertRaises(ValueError):
            audit(self.data)


if __name__ == '__main__':
    unittest.main()
