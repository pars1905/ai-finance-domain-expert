"""Explicit provider selection and bounded Gemini generateContent adaptation.

No provider fallback: a missing Gemini key never triggers an OpenAI call.
Free-tier confirmation is a user assertion, not a billing verification API.
"""
import json
import os
import re
import urllib.request


def settings():
    provider = os.environ.get('AI_PROVIDER', 'openai').strip().lower()
    if provider not in ('openai', 'gemini'):
        raise ValueError('AI_PROVIDER must be openai or gemini')
    prefix = 'GEMINI' if provider == 'gemini' else 'OPENAI'
    key = os.environ.get(prefix + '_API_KEY', '').strip()
    model = os.environ.get(prefix + '_MODEL', '').strip()
    if not key or not model:
        raise ValueError(f'Set {prefix}_API_KEY and {prefix}_MODEL explicitly')
    if provider == 'gemini' and os.environ.get('GEMINI_FREE_TIER_CONFIRMED') != '1':
        raise ValueError('Confirm the project and model free tier before enabling Gemini calls')
    return provider, key, model


def request_for(payload, key, provider):
    if provider == 'openai':
        return urllib.request.Request('https://api.openai.com/v1/responses', method='POST',
            data=json.dumps(payload, allow_nan=False).encode(),
            headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    if provider != 'gemini':
        raise ValueError('Unsupported provider')
    model = payload['model']
    if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', model):
        raise ValueError('Use a Gemini model ID without URL or models/ prefix')
    native = {
        'contents': [{'role': 'user', 'parts': [{'text': payload['input']}]}],
        'generationConfig': {'maxOutputTokens': payload['max_output_tokens'],
                             'candidateCount': 1},
    }
    if payload.get('instructions'):
        native['systemInstruction'] = {'parts': [{'text': payload['instructions']}]}
    schema = payload.get('text', {}).get('format', {}).get('schema')
    if schema is not None:
        native['generationConfig'].update(responseMimeType='application/json',
                                           responseJsonSchema=schema)
    return urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        method='POST', data=json.dumps(native, allow_nan=False).encode(),
        headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})


def normalize_response(result, provider):
    if provider == 'openai':
        return result
    if not isinstance(result, dict):
        raise ValueError('Malformed Gemini response')
    candidates = result.get('candidates')
    if (result.get('promptFeedback', {}).get('blockReason')
            or not isinstance(candidates, list) or len(candidates) != 1
            or not isinstance(candidates[0], dict)):
        raise ValueError('Missing or blocked Gemini candidate')
    candidate = candidates[0]
    parts = candidate.get('content', {}).get('parts')
    if candidate.get('finishReason') != 'STOP' or not isinstance(parts, list):
        raise ValueError('Gemini did not complete the response')
    fragments = []
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError('Malformed Gemini content')
        if part.get('thought') is True:
            continue
        if 'text' in part:
            if not isinstance(part['text'], str):
                raise ValueError('Malformed Gemini text')
            fragments.append(part['text'])
    text = ''.join(fragments)
    if not text.strip():
        raise ValueError('No Gemini output text')
    usage = result.get('usageMetadata', {})
    if not isinstance(usage, dict):
        raise ValueError('Malformed Gemini usage')
    prompt, output = usage.get('promptTokenCount'), usage.get('candidatesTokenCount')
    thoughts = usage.get('thoughtsTokenCount', 0)
    if any(type(v) is not int or v < 0 for v in (prompt, output, thoughts)):
        raise ValueError('Missing or invalid Gemini usage')
    # Count thinking tokens as output too; quota accounting must not hide them.
    return {'status': 'completed', 'id': result.get('responseId'),
            'model': result.get('modelVersion'),
            'usage': {'input_tokens': prompt, 'output_tokens': output + thoughts},
            'output': [{'type': 'message', 'role': 'assistant',
                        'content': [{'type': 'output_text', 'text': text}]}]}
