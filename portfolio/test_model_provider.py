import copy
import io
import json
import os
import unittest
from unittest.mock import patch

from llm_commentary import summarize
from model_provider import normalize_response, request_for, settings


def gemini_response(text='Synthetic briefing.'):
    return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}],
            'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 5},
            'modelVersion': 'gemini-mock', 'responseId': 'mock-response'}


GEMINI_ENV = {'AI_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'synthetic-test-key',
              'GEMINI_MODEL': 'gemini-mock', 'GEMINI_FREE_TIER_CONFIRMED': '1'}


class GeminiProviderTests(unittest.TestCase):
    def test_requires_explicit_provider_credentials_and_free_tier_confirmation(self):
        for missing in ('GEMINI_API_KEY', 'GEMINI_MODEL', 'GEMINI_FREE_TIER_CONFIRMED'):
            environment = {k: v for k, v in GEMINI_ENV.items() if k != missing}
            environment.update(OPENAI_API_KEY='must-not-fall-back', OPENAI_MODEL='other')
            with self.subTest(missing=missing), patch.dict(os.environ, environment, clear=True):
                with self.assertRaises(ValueError):
                    settings()
                self.assertEqual(summarize({}, lambda *a, **k: self.fail('Network called'))['status'],
                                 'unavailable')

    def test_native_request_keeps_key_out_of_url_and_payload(self):
        payload = {'model': 'gemini-mock', 'input': 'Fictional report',
                   'instructions': 'Use supplied data', 'max_output_tokens': 80,
                   'text': {'format': {'schema': {'type': 'object'}}}}
        request = request_for(payload, 'synthetic-secret', 'gemini')
        self.assertEqual(request.full_url,
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-mock:generateContent')
        self.assertNotIn('synthetic-secret', request.full_url + request.data.decode())
        self.assertEqual(request.get_header('X-goog-api-key'), 'synthetic-secret')
        data = json.loads(request.data)
        self.assertEqual(data['contents'][0]['parts'][0]['text'], payload['input'])
        self.assertEqual(data['generationConfig']['maxOutputTokens'], 80)
        self.assertEqual(data['generationConfig']['responseJsonSchema'], {'type': 'object'})

    def test_model_cannot_change_destination(self):
        for model in ('../other', 'models/example', 'https://other.example', 'x?key=foo'):
            with self.subTest(model=model), self.assertRaises(ValueError):
                request_for({'model': model}, 'synthetic', 'gemini')

    def test_normalizes_usage_and_excludes_thought_text(self):
        data = gemini_response()
        data['candidates'][0]['content']['parts'].insert(0, {'thought': True, 'text': 'private reasoning'})
        data['usageMetadata']['thoughtsTokenCount'] = 3
        result = normalize_response(data, 'gemini')
        self.assertEqual(result['usage'], {'input_tokens': 10, 'output_tokens': 8})
        self.assertEqual(result['output'][0]['content'][0]['text'], 'Synthetic briefing.')

    def test_blocked_truncated_and_malformed_results_rejected(self):
        for finish in ('MAX_TOKENS', 'SAFETY', None):
            data = gemini_response()
            data['candidates'][0]['finishReason'] = finish
            with self.subTest(finish=finish), self.assertRaises(ValueError):
                normalize_response(data, 'gemini')
        for usage in ({}, {'promptTokenCount': True, 'candidatesTokenCount': 5}):
            data = gemini_response()
            data['usageMetadata'] = usage
            with self.assertRaises(ValueError):
                normalize_response(data, 'gemini')

    def test_commentary_gemini_integration_preserves_calculations(self):
        report = {'items': [{'id': 'example', 'variance': '12.50'}]}
        original = copy.deepcopy(report)
        def fake(request, timeout):
            self.assertIn('generativelanguage.googleapis.com', request.full_url)
            self.assertEqual(timeout, 30)
            return io.BytesIO(json.dumps(gemini_response('example: İnceleme gerekli.')).encode())
        with patch.dict(os.environ, GEMINI_ENV, clear=True):
            result = summarize(report, fake)
        self.assertEqual(result['provider'], 'gemini')
        self.assertEqual(result['status'], 'unverified_ai_commentary')
        self.assertEqual(report, original)


if __name__ == '__main__':
    unittest.main()
