"""Evaluate lexical retrieval and abstention on authored development/holdout cases."""
import argparse
import hashlib
import json
from pathlib import Path
from assistant import read_corpus
from retrieval import retrieve, validate_corpus

ROOT = Path(__file__).resolve().parent


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def evaluate(corpus, fixture, split='both'):
    validate_corpus(corpus)
    cases = fixture['cases']
    ids = [c['id'] for c in cases]
    if not cases or len(ids) != len(set(ids)) or any(c['split'] not in ('development', 'holdout') for c in cases):
        raise ValueError('Invalid evaluation IDs/splits')
    if split not in ('development', 'holdout', 'both'):
        raise ValueError('Invalid requested split')
    reports = {}
    sources = {d['id']: d['text'] for d in corpus['documents']}
    for partition in ('development', 'holdout'):
        if split != 'both' and partition != split:
            continue
        rows = []
        for c in cases:
            if c['split'] != partition:
                continue
            if type(c['expected_evidence']) is not bool:
                raise ValueError('Evaluation label must be boolean')
            evidence = retrieve(corpus, c['question'], c['entity'], c['period'])
            supported = c['expected_evidence']
            hit = any(e['source_id'] == c['expected_source'] and
                      c['expected_quote_contains'] in e['quote'] for e in evidence) if supported else None
            spans_valid = all(sources[e['source_id']][e['start']:e['end']] == e['quote'] for e in evidence)
            rows.append({'id': c['id'], 'expected_evidence': supported,
                         'returned_evidence': bool(evidence), 'supported_hit_at_3': hit,
                         'correct_abstention': not evidence if not supported else None,
                         'exact_spans_valid': spans_valid,
                         'retrieved_span_ids': [e['span_id'] for e in evidence]})
        positives = [r for r in rows if r['expected_evidence']]
        negatives = [r for r in rows if not r['expected_evidence']]
        reports[partition] = {'cases': len(rows),
                              'supported_cases': len(positives),
                              'supported_hits_at_3': sum(r['supported_hit_at_3'] for r in positives),
                              'unsupported_cases': len(negatives),
                              'correct_abstentions': sum(r['correct_abstention'] for r in negatives),
                              'all_returned_spans_valid': all(r['exact_spans_valid'] for r in rows),
                              'results': rows}
    return {'scope': 'authored synthetic retrieval tests; not generated-answer or real model accuracy',
            'corpus_sha256': fingerprint(corpus), 'evaluation_sha256': fingerprint(fixture),
            'policy_version': 'bm25-coverage-v1', 'partitions': reports,
            'limitations': ['Holdout is separately authored, not independently reviewed.',
                            'Tiny fixtures cannot establish generalization or semantic grounding.',
                            'No LLM is called or evaluated by this script.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, default=ROOT / 'corpus.json')
    parser.add_argument('--cases', type=Path, default=ROOT / 'evaluation_cases.json')
    parser.add_argument('--split', choices=('development', 'holdout', 'both'), default='both')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(read_corpus(args.corpus), json.loads(args.cases.read_text()), args.split)
        rendered = json.dumps(result, indent=2) + '\n'
        if args.output:
            args.output.write_text(rendered)
        print(rendered, end='')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f'Evaluation error: {exc}\n')
