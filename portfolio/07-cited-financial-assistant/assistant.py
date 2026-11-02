"""Retrieve exact source spans; optionally generate and validate a cited draft."""
import argparse
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from retrieval import retrieve
from model import generate

ROOT = Path(__file__).resolve().parent


def number_tokens(value):
    found = {(Decimal(m.group(1)), 'percent' if m.group(2) else 'number') for m in
             re.finditer(r'(?<![\w.])(-?\d+(?:\.\d+)?)(%)?', value)}
    found |= {(Decimal(year), 'fiscal_year') for year in re.findall(r'\bFY(\d{4})\b', value, re.I)}
    return found


def validate_answer(candidate, evidence):
    if not isinstance(candidate, dict) or set(candidate) != {'status', 'claims'}:
        raise ValueError('Invalid response keys')
    claims = candidate['claims']
    if not isinstance(claims, list):
        raise ValueError('Claims must be a list')
    if candidate['status'] == 'insufficient_evidence' and not claims:
        return []
    if candidate['status'] != 'answer' or not 1 <= len(claims) <= 5:
        raise ValueError('Invalid answer status/claim count')
    by_id = {e['span_id']: e for e in evidence}
    checked = []
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {'text', 'citations'}:
            raise ValueError('Invalid claim keys')
        text, citations = claim['text'], claim['citations']
        if not isinstance(text, str) or not text.strip() or len(text) > 1500:
            raise ValueError('Invalid claim text')
        if not isinstance(citations, list) or not 1 <= len(citations) <= 3:
            raise ValueError('Missing or excessive citations')
        resolved, quotes = [], []
        for citation in citations:
            if not isinstance(citation, dict) or set(citation) != {'span_id', 'quote'}:
                raise ValueError('Invalid citation keys')
            span_id, quote = citation['span_id'], citation['quote']
            if not isinstance(span_id, str) or span_id not in by_id:
                raise ValueError('Citation not in retrieved context')
            if not isinstance(quote, str) or len(quote.strip()) < 12:
                raise ValueError('Quote missing or too short')
            source = by_id[span_id]
            position = source['quote'].find(quote)
            if position < 0:
                raise ValueError('Quote does not match exact source text')
            quotes.append(quote)
            start = source['start'] + position
            resolved.append({'span_id': span_id, 'source_id': source['source_id'],
                             'source_sha256': source['source_sha256'],
                             'start': start, 'end': start + len(quote), 'quote': quote})
        if not number_tokens(text) <= number_tokens(' '.join(quotes)):
            raise ValueError('Claim contains a number/percent token absent from cited quotes')
        currencies = lambda s: set(re.findall(r'\b(?:USD|EUR|TRY|GBP)\b', s))
        if not currencies(text) <= currencies(' '.join(quotes)):
            raise ValueError('Claim currency absent from cited quotes')
        checked.append({'text': text, 'citations': resolved})
    return checked


def answer(corpus, query, entity, period, use_ai=False, transport=None):
    evidence = retrieve(corpus, query, entity, period)
    fingerprint = hashlib.sha256(json.dumps(corpus, sort_keys=True, ensure_ascii=False,
                                            allow_nan=False).encode()).hexdigest()
    report = {'project': 'Cited Financial Document Assistant', 'question': query,
              'filters': {'entity': entity, 'period': period}, 'corpus_sha256': fingerprint,
              'retrieval': evidence, 'retrieval_method': 'paragraph BM25; query coverage >=0.6; top_k=3',
              'status': 'source_excerpts' if evidence else 'insufficient_evidence',
              'excerpts': [{'text': e['quote'], 'citation': {k: e[k] for k in
                           ('span_id', 'source_id', 'start', 'end', 'source_sha256')}} for e in evidence],
              'generated_answer': {'status': 'not_requested'}, 'requires_human_review': True,
              'limitations': ['Lexical relevance does not establish answerability or entailment.',
                              'Citation validation checks exact text and limited number tokens, not truth.',
                              'Sources and filters must be independently verified. No investment decisions are made.']}
    if use_ai and evidence:
        result = generate(query, evidence, transport)
        if result['status'] == 'received':
            try:
                checked = validate_answer(result['candidate'], evidence)
                report['generated_answer'] = {'status': 'validated_citations_unverified_meaning' if checked
                                              else 'insufficient_evidence', 'claims': checked,
                                              'metadata': result['metadata']}
            except ValueError as exc:
                report['generated_answer'] = {'status': 'rejected', 'reason': str(exc),
                                              'metadata': result['metadata']}
        else:
            report['generated_answer'] = result
    elif use_ai:
        report['generated_answer'] = {'status': 'skipped_no_evidence'}
    return report


def render(report):
    lines = ['# Cited Financial Document Assistant', '', f"Status: {report['status']}", '',
             f"Question: {report['question']}", '', '## Retrieved excerpts', '']
    for e in report['retrieval']:
        lines += [f"### {e['span_id']}", '',
                  f"Source: {e['title']} · characters [{e['start']}, {e['end']})", '',
                  *['> ' + s for s in e['quote'].splitlines()], '']
    lines += ['## Generated draft', '', f"Status: {report['generated_answer']['status']}", '']
    for claim in report['generated_answer'].get('claims', []):
        lines += [claim['text'], '', 'Citations: ' + ', '.join(c['span_id'] for c in claim['citations']), '']
    lines += ['Human review required. Citation presence does not verify the meaning of a claim.', '']
    return '\n'.join(lines)


def read_corpus(path):
    if path.stat().st_size > 1000000:
        raise ValueError('Corpus file exceeds 1 MB cap')
    return json.loads(path.read_text())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', default='What was ExampleCo revenue in FY2025?')
    parser.add_argument('--entity', default='ExampleCo')
    parser.add_argument('--period', default='FY2025')
    parser.add_argument('--corpus', type=Path, default=ROOT / 'corpus.json')
    parser.add_argument('--ai', action='store_true', help='Opt-in paid API request; keys/model from environment')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--markdown', type=Path)
    args = parser.parse_args()
    try:
        report = answer(read_corpus(args.corpus), args.question, args.entity, args.period, args.ai)
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.output:
            args.output.write_text(rendered)
        if args.markdown:
            args.markdown.write_text(render(report))
        print(rendered, end='')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f'Assistant error: {exc}\n')
