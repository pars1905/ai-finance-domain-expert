import copy
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from assistant import answer, number_tokens, render, validate_answer
from evaluate import evaluate
from model import generate
from retrieval import chunks, retrieve

ROOT = Path(__file__).resolve().parent


class CitedAssistantTests(unittest.TestCase):
    def test_gemini_structured_generation_and_citations(self):
        def fake(request, timeout):
            payload = json.loads(request.data)
            self.assertIn('responseJsonSchema', payload['generationConfig'])
            self.assertEqual(request.get_header('X-goog-api-key'), 'mock-gemini-key')
            return io.BytesIO(json.dumps({
                'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
                    {'text': json.dumps(self.candidate)}]}}],
                'usageMetadata': {'promptTokenCount': 100, 'candidatesTokenCount': 30},
                'modelVersion': 'gemini-mock',
            }).encode())
        with patch.dict(os.environ, {'AI_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'mock-gemini-key',
                'GEMINI_MODEL': 'gemini-mock', 'GEMINI_FREE_TIER_CONFIRMED': '1'}, clear=True):
            result = answer(self.corpus, self.query, 'ExampleCo', 'FY2025', True, fake)
        self.assertEqual(result['generated_answer']['status'], 'validated_citations_unverified_meaning')
        self.assertEqual(result['generated_answer']['metadata']['provider'], 'gemini')

    def setUp(self):
        self.corpus = json.loads((ROOT / 'corpus.json').read_text())
        self.query = 'What was ExampleCo revenue in FY2025?'
        self.evidence = retrieve(self.corpus, self.query, 'ExampleCo', 'FY2025')
        self.quote = self.evidence[0]['quote']
        self.candidate = {'status': 'answer', 'claims': [{'text': 'Revenue was USD 120 million.',
                    'citations': [{'span_id': self.evidence[0]['span_id'], 'quote': self.quote}]}]}

    def test_revenue_retrieval_and_exact_offsets(self):
        self.assertIn('USD 120 million', self.quote)
        for e in self.evidence:
            doc = next(d for d in self.corpus['documents'] if d['id'] == e['source_id'])
            self.assertEqual(doc['text'][e['start']:e['end']], e['quote'])

    def test_company_and_year_are_isolated(self):
        current = retrieve(self.corpus, 'revenue', 'OtherCo', 'FY2025')
        prior = retrieve(self.corpus, 'revenue', 'ExampleCo', 'FY2024')
        self.assertIn('USD 250 million', current[0]['quote'])
        self.assertIn('USD 100 million', prior[0]['quote'])
        self.assertTrue(all(e['entity'] == 'ExampleCo' and e['period'] == 'FY2025' for e in self.evidence))

    def test_conflicting_period_abstains(self):
        self.assertEqual(retrieve(self.corpus, 'revenue FY2024', 'ExampleCo', 'FY2025'), [])

    def test_unknown_topic_and_missing_company_abstain(self):
        self.assertEqual(retrieve(self.corpus, 'dividends paid', 'ExampleCo', 'FY2025'), [])
        self.assertEqual(retrieve(self.corpus, 'revenue', 'UnknownCo', 'FY2025'), [])

    def test_explicit_turkish_term_aliases(self):
        evidence = retrieve(self.corpus, 'ExampleCo FY2025 geliri nedir?', 'ExampleCo', 'FY2025')
        self.assertIn('USD 120 million', evidence[0]['quote'])

    def test_empty_question_rejected(self):
        with self.assertRaises(ValueError):
            retrieve(self.corpus, '', 'ExampleCo', 'FY2025')

    def test_duplicate_document_ids_rejected(self):
        self.corpus['documents'].append(copy.deepcopy(self.corpus['documents'][0]))
        with self.assertRaises(ValueError):
            retrieve(self.corpus, self.query, 'ExampleCo', 'FY2025')

    def test_unicode_offsets_use_python_characters(self):
        self.corpus['documents'][0]['text'] = 'Özel € notu.\n\nExampleCo revenue was USD 120 million.'
        evidence = retrieve(self.corpus, 'revenue', 'ExampleCo', 'FY2025')
        quote = evidence[0]
        self.assertEqual(quote['start'], len('Özel € notu.\n\n'))
        self.assertEqual(self.corpus['documents'][0]['text'][quote['start']:quote['end']], quote['quote'])

    def test_long_paragraph_is_bounded(self):
        self.corpus['documents'][0]['text'] = ('revenue ' * 400)
        rows = chunks(self.corpus, 'ExampleCo', 'FY2025')
        self.assertTrue(all(len(row['quote']) <= 1000 for row in rows))

    def test_valid_subquote_resolves_exact_start(self):
        subquote = 'revenue was USD 120 million.'
        self.candidate['claims'][0]['citations'][0]['quote'] = subquote
        result = validate_answer(self.candidate, self.evidence)
        c = result[0]['citations'][0]
        source = self.corpus['documents'][0]['text']
        self.assertEqual(source[c['start']:c['end']], subquote)

    def test_unknown_citation_rejected(self):
        self.candidate['claims'][0]['citations'][0]['span_id'] = 'invented'
        with self.assertRaises(ValueError):
            validate_answer(self.candidate, self.evidence)

    def test_fabricated_quote_rejected(self):
        self.candidate['claims'][0]['citations'][0]['quote'] = 'Revenue was USD 999 million.'
        with self.assertRaises(ValueError):
            validate_answer(self.candidate, self.evidence)

    def test_unsupported_number_year_and_currency_rejected(self):
        for text in ('Revenue was USD 999 million.', 'Revenue in FY2024 was USD 120 million.', 'Revenue was EUR 120 million.'):
            self.candidate['claims'][0]['text'] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_answer(self.candidate, self.evidence)

    def test_percent_is_not_plain_number(self):
        self.assertNotEqual(number_tokens('30%'), number_tokens('30'))

    def test_nonempty_abstention_and_extra_keys_rejected(self):
        self.candidate['status'] = 'insufficient_evidence'
        with self.assertRaises(ValueError):
            validate_answer(self.candidate, self.evidence)
        with self.assertRaises(ValueError):
            validate_answer({'status': 'insufficient_evidence', 'claims': [], 'extra': 'x'}, self.evidence)

    def test_semantic_error_is_known_limit(self):
        self.candidate['claims'][0]['text'] = 'Revenue collapsed to USD 120 million.'
        # Exact citations/numbers can pass even when the interpretation is unsupported.
        self.assertTrue(validate_answer(self.candidate, self.evidence))
        self.assertTrue(answer(self.corpus, self.query, 'ExampleCo', 'FY2025')['requires_human_review'])

    def test_offline_mode_never_calls_transport(self):
        def fail(*a, **kw):
            self.fail('Unexpected network call')
        report = answer(self.corpus, self.query, 'ExampleCo', 'FY2025', transport=fail)
        self.assertEqual(report['status'], 'source_excerpts')
        self.assertEqual(report['generated_answer']['status'], 'not_requested')
        self.assertIn(self.evidence[0]['span_id'], render(report))

    def test_no_evidence_skips_even_requested_model(self):
        def fail(*a, **kw):
            self.fail('Unexpected network call')
        report = answer(self.corpus, 'dividends paid', 'ExampleCo', 'FY2025', True, fail)
        self.assertEqual(report['generated_answer']['status'], 'skipped_no_evidence')

    def test_no_key_does_not_silently_generate(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(generate(self.query, self.evidence)['status'], 'unavailable')

    def transport(self, candidate):
        def fake(request, timeout):
            payload = json.loads(request.data)
            self.assertFalse(payload['store'])
            self.assertTrue(payload['text']['format']['strict'])
            self.assertNotIn('tools', payload)
            self.assertEqual(timeout, 30)
            return io.BytesIO(json.dumps({'status': 'completed', 'id': 'mock', 'model': 'mock-model',
                'usage': {'input_tokens': 100, 'output_tokens': 30},
                'output': [{'type': 'message', 'role': 'assistant', 'content': [
                    {'type': 'output_text', 'text': json.dumps(candidate)}]}]}).encode())
        return fake

    def test_mocked_structured_generation_is_validated(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'mock-key', 'OPENAI_MODEL': 'mock-model'}, clear=True):
            report = answer(self.corpus, self.query, 'ExampleCo', 'FY2025', True, self.transport(self.candidate))
        generated = report['generated_answer']
        self.assertEqual(generated['status'], 'validated_citations_unverified_meaning')
        self.assertEqual(generated['metadata']['usage']['output_tokens'], 30)
        self.assertEqual(len(generated['claims']), 1)

    def test_invalid_generation_is_rejected_without_exposing_draft(self):
        self.candidate['claims'][0]['text'] = 'Revenue was USD 999 million.'
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'mock', 'OPENAI_MODEL': 'mock'}, clear=True):
            report = answer(self.corpus, self.query, 'ExampleCo', 'FY2025', True, self.transport(self.candidate))
        self.assertEqual(report['generated_answer']['status'], 'rejected')
        self.assertNotIn('999', json.dumps(report))
        self.assertTrue(report['excerpts'])

    def test_valid_model_abstention(self):
        candidate = {'status': 'insufficient_evidence', 'claims': []}
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'mock', 'OPENAI_MODEL': 'mock'}, clear=True):
            report = answer(self.corpus, self.query, 'ExampleCo', 'FY2025', True, self.transport(candidate))
        self.assertEqual(report['generated_answer']['status'], 'insufficient_evidence')

    def test_network_error_preserves_excerpts_and_redacts_message(self):
        def fail(*a, **kw):
            raise OSError('mock-secret must not be returned')
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'mock', 'OPENAI_MODEL': 'mock'}, clear=True):
            report = answer(self.corpus, self.query, 'ExampleCo', 'FY2025', True, fail)
        self.assertEqual(report['generated_answer']['status'], 'unavailable')
        self.assertNotIn('mock-secret', json.dumps(report))
        self.assertTrue(report['excerpts'])

    def test_malformed_and_incomplete_api_payloads_unavailable(self):
        payloads = [[], {'status': 'incomplete'}, {'status': 'completed', 'output': [None]},
                    {'status': 'completed', 'output': [{'type': 'message', 'role': 'assistant', 'content': [
                        {'type': 'refusal', 'refusal': 'No'}]}]}]
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'mock', 'OPENAI_MODEL': 'mock'}, clear=True):
            for payload in payloads:
                result = generate(self.query, self.evidence, lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
                self.assertEqual(result['status'], 'unavailable')

    def test_evaluation_partitions_and_hashes(self):
        fixture = json.loads((ROOT / 'evaluation_cases.json').read_text())
        result = evaluate(self.corpus, fixture, 'development')
        self.assertEqual(set(result['partitions']), {'development'})
        self.assertEqual(len(result['evaluation_sha256']), 64)
        self.assertTrue(result['partitions']['development']['all_returned_spans_valid'])


if __name__ == '__main__':
    unittest.main()
