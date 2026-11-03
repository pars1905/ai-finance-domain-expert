"""Verify exact quotations and typed facts against a supplied local corpus."""
import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('Invalid fact value')
    try:
        v = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid fact value') from exc
    if not v.is_finite():
        raise ValueError('Non-finite fact')
    return v


def audit_claim(claim, sources):
    if not isinstance(claim, dict):
        return {'status': 'review', 'reason': 'malformed_claim'}
    if not isinstance(claim.get('source_id'), str):
        return {'status': 'review', 'reason': 'malformed_claim'}
    source = sources.get(claim.get('source_id'))
    if source is None:
        return {'status': 'fail', 'reason': 'unknown_source'}
    if claim.get('kind') == 'quote':
        quote = claim.get('quote')
        if not isinstance(quote, str) or not quote.strip():
            return {'status': 'review', 'reason': 'empty_quote'}
        # Deliberately exact, case-sensitive substring matching.
        present = quote in source['text']
        return {'status': 'pass' if present else 'fail',
                'reason': 'exact_quote_found' if present else 'quote_not_found'}
    if claim.get('kind') == 'fact':
        if any(not isinstance(claim.get(k), str) or not claim[k].strip()
               for k in ('metric', 'period', 'unit')):
            return {'status': 'review', 'reason': 'missing_or_ambiguous_fact'}
        matches = [f for f in source['facts']
                   if all(f.get(k) == claim.get(k) for k in ('metric', 'period', 'unit'))]
        if len(matches) != 1:
            return {'status': 'review', 'reason': 'missing_or_ambiguous_fact'}
        try:
            equal = decimal(matches[0]['value']) == decimal(claim['value'])
        except (KeyError, ValueError):
            return {'status': 'review', 'reason': 'invalid_fact_value'}
        return {'status': 'pass' if equal else 'fail',
                'reason': 'fact_matches' if equal else 'fact_mismatch'}
    return {'status': 'review', 'reason': 'unsupported_claim_kind'}


def audit(data):
    sources = data['sources']
    source_ids = [s['id'] for s in sources]
    claims = data['claims']
    claim_ids = [c['id'] for c in claims]
    if len(source_ids) != len(set(source_ids)) or len(claim_ids) != len(set(claim_ids)):
        raise ValueError('Duplicate source/claim IDs')
    if not claims:
        raise ValueError('No claims supplied')
    for s in sources:
        if (not isinstance(s.get('text'), str) or not isinstance(s.get('facts'), list)
                or any(not isinstance(f, dict) for f in s['facts'])):
            raise ValueError('Malformed source')
    corpus = {s['id']: s for s in sources}
    rows = [{'id': c['id'], **audit_claim(c, corpus)} for c in claims]
    return {'scope': 'quotation presence and supplied fact consistency only; not entailment',
            'results': rows,
            'counts': {v: sum(r['status'] == v for r in rows)
                       for v in ('pass', 'fail', 'review')}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path,
                        default=Path(__file__).with_name('claims.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(audit(json.loads(args.input.read_text())), indent=2)
    if args.output:
        args.output.write_text(result + '\n')
    print(result)
