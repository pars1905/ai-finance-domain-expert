"""Deterministic lexical retrieval with explicit company/period filters."""
import hashlib
import math
import re
from collections import Counter

STOP = set('what was were is are the a an of in for and to how much tell me about '
           'please reported report financial statement statements did does company '
           'nedir ne kadar ve ile bir bu icin için hakkında'.split())
ALIASES = {'gelir': 'revenue', 'geliri': 'revenue', 'ciro': 'revenue',
           'brüt': 'gross', 'marj': 'margin', 'marjı': 'margin',
           'nakit': 'cash', 'akışı': 'flows', 'borç': 'debt', 'borcu': 'debt'}


def tokens(text):
    return [ALIASES.get(t, t) for t in re.findall(r'\w+', text.casefold()) if t not in STOP]


def validate_corpus(corpus):
    if not isinstance(corpus, dict) or not isinstance(corpus.get('documents'), list):
        raise ValueError('Corpus must contain a documents list')
    documents = corpus['documents']
    if not 1 <= len(documents) <= 50:
        raise ValueError('Corpus must have 1–50 documents')
    seen = set()
    for doc in documents:
        if not isinstance(doc, dict):
            raise ValueError('Malformed document')
        for key in ('id', 'entity', 'period', 'title', 'text', 'provenance'):
            if not isinstance(doc.get(key), str) or not doc[key].strip():
                raise ValueError('Document fields must be nonempty strings')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', doc['id']) or doc['id'] in seen:
            raise ValueError('Document IDs must be unique safe identifiers')
        if len(doc['text']) > 50000:
            raise ValueError('Document text exceeds 50,000 characters')
        seen.add(doc['id'])
    return documents


def chunks(corpus, entity, period):
    rows = []
    for doc in validate_corpus(corpus):
        if doc['entity'].casefold() != entity.casefold() or doc['period'].casefold() != period.casefold():
            continue
        fingerprint = hashlib.sha256(doc['text'].encode()).hexdigest()
        for paragraph in re.finditer(r'\S[\s\S]*?(?=\n[ \t]*\n|\Z)', doc['text']):
            text = paragraph.group().rstrip()
            for offset in range(0, len(text), 1000):
                start = paragraph.start() + offset
                end = min(start + 1000, paragraph.start() + len(text))
                rows.append({'span_id': f"{doc['id']}:{start}-{end}",
                             'source_id': doc['id'], 'title': doc['title'],
                             'entity': doc['entity'], 'period': doc['period'],
                             'start': start, 'end': end, 'source_sha256': fingerprint,
                             'quote': doc['text'][start:end]})
    return rows


def retrieve(corpus, query, entity, period, top_k=3):
    if not isinstance(query, str) or not query.strip() or len(query) > 1000:
        raise ValueError('Question must contain 1–1000 characters')
    if any(not isinstance(v, str) or not v.strip() for v in (entity, period)):
        raise ValueError('Entity and period filters are required')
    if type(top_k) is not int or not 1 <= top_k <= 5:
        raise ValueError('top_k must be an integer from 1 to 5')
    rows = chunks(corpus, entity, period)
    # Explicit FY mentions must agree with the caller-supplied period filter.
    periods = set(re.findall(r'\bfy\d{4}\b', query.casefold()))
    if periods and periods != {period.casefold()}:
        return []
    terms = set(tokens(query)) - set(tokens(entity)) - set(tokens(period))
    if not rows or not terms:
        return []
    counts = [Counter(tokens(row['quote'])) for row in rows]
    lengths = [sum(c.values()) for c in counts]
    average = sum(lengths) / len(rows) or 1
    frequency = {term: sum(term in c for c in counts) for term in terms}
    scored = []
    for row, count, length in zip(rows, counts, lengths):
        matched = terms & count.keys()
        coverage = len(matched) / len(terms)
        # A disclosed heuristic, not a calibrated answerability probability.
        if coverage < .6:
            continue
        score = 0.
        for term in matched:
            tf, df = count[term], frequency[term]
            idf = math.log(1 + (len(rows) - df + .5) / (df + .5))
            score += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * length / average))
        scored.append({**row, 'score': round(score, 8),
                       'query_term_coverage': coverage, 'matched_terms': sorted(matched)})
    return sorted(scored, key=lambda r: (-r['score'], r['span_id']))[:top_k]
