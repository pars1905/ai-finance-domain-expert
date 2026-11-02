import copy
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from finance_tools import dec, digest, iso_date, markdown
from llm_commentary import summarize
from review_decision import record


class BusinessInfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.report = {'project': 'Test', 'input_sha256': 'example', 'items': [
            {'id': 'case-1', 'finding': 'review', 'requires_human_review': True}]}

    def test_numeric_schema_rejects_nonfinite_boolean_and_huge(self):
        for value in (True, None, 'NaN', 'Infinity', '1e40'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                dec(value)

    def test_date_is_strict(self):
        for value in ('20261031', '2026-02-30'):
            with self.assertRaises(ValueError):
                iso_date(value)

    def test_digest_independent_of_key_order(self):
        self.assertEqual(digest({'a': 1, 'b': 2}), digest({'b': 2, 'a': 1}))

    def test_review_persists_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / 'reviews.db'
            a = record(self.report, 'case-1', 'acknowledge', 'demo-reviewer', 'Checked source', db)
            b = record(self.report, 'case-1', 'acknowledge', 'demo-reviewer', 'Checked source', db)
            self.assertEqual(a, b)
            with sqlite3.connect(db) as connection:
                self.assertEqual(connection.execute('select count(*) from reviews').fetchone()[0], 1)
            with self.assertRaises(ValueError):
                record(self.report, 'case-1', 'request_changes', 'other', 'Changed decision', db)

    def test_changed_report_gets_new_review(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / 'reviews.db'
            a = record(self.report, 'case-1', 'acknowledge', 'demo', 'Checked', db)
            self.report['items'][0]['finding'] = 'updated finding'
            b = record(self.report, 'case-1', 'request_changes', 'demo', 'Needs work', db)
            self.assertNotEqual(a['report_sha256'], b['report_sha256'])

    def test_cannot_review_missing_or_nonreviewable_item(self):
        self.report['items'][0]['requires_human_review'] = False
        with self.assertRaises(ValueError):
            record(self.report, 'case-1', 'acknowledge', 'demo', 'Checked', ':memory:')

    def test_markdown_escapes_table_separator(self):
        self.report['items'][0]['finding'] = 'x|y\nz'
        self.assertIn('x\\|y z', markdown(self.report))

    def test_ai_without_credentials_does_not_call_network(self):
        with patch.dict(os.environ, {}, clear=True):
            def fail(*args, **kwargs):
                self.fail('Unexpected network call')
            self.assertEqual(summarize(self.report, fail)['status'], 'unavailable')

    def test_ai_mock_checks_request_and_preserves_report(self):
        before = copy.deepcopy(self.report)
        def fake(request, timeout):
            data = json.loads(request.data)
            self.assertFalse(data['store'])
            self.assertEqual(data['max_output_tokens'], 700)
            self.assertNotIn('tools', data)
            self.assertEqual(timeout, 30)
            return io.BytesIO(json.dumps({'status': 'completed', 'id': 'mock', 'model': 'test-model',
                'output': [{'type': 'message', 'role': 'assistant', 'content': [
                    {'type': 'output_text', 'text': 'case-1: İnceleme gerekli.'}]}]}).encode())
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}, clear=True):
            response = summarize(self.report, fake)
        self.assertEqual(response['status'], 'unverified_ai_commentary')
        self.assertEqual(self.report, before)

    def test_ai_error_is_bounded_and_does_not_expose_error_body(self):
        def fake(*args, **kwargs):
            raise OSError('secret test-key')
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}, clear=True):
            result = summarize(self.report, fake)
        self.assertEqual(result['status'], 'unavailable')
        self.assertNotIn('test-key', json.dumps(result))

    def test_incomplete_model_response_not_accepted(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'x', 'OPENAI_MODEL': 'x'}, clear=True):
            result = summarize(self.report, lambda *a, **k: io.BytesIO(b'{"status":"incomplete"}'))
        self.assertEqual(result['status'], 'unavailable')

    def test_malformed_model_payload_preserves_calculations(self):
        payloads = [[], {'status': 'completed', 'output': ['invalid']},
                    {'status': 'completed', 'output': [{'type': 'message', 'role': 'assistant', 'content': [None]}]}]
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'x', 'OPENAI_MODEL': 'x'}, clear=True):
            for payload in payloads:
                result = summarize(self.report, lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
                self.assertEqual(result['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
