"""Shared validation, reproducible reporting, and offline-first CLI helpers."""
import argparse
import hashlib
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


def dec(value, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('Expected a finite decimal')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal') from exc
    if not result.is_finite() or abs(result) > Decimal('1e15'):
        raise ValueError('Non-finite or out-of-scope number')
    if minimum is not None and result < minimum:
        raise ValueError('Number below minimum')
    if maximum is not None and result > maximum:
        raise ValueError('Number above maximum')
    return result


def integer(value, minimum=0):
    result = dec(value, minimum, 1000000)
    if result != result.to_integral_value():
        raise ValueError('Expected whole number')
    return int(result)


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected non-empty text')
    return value


def iso_date(value):
    text(value)
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError('Date must use YYYY-MM-DD')
    return parsed


def unique_rows(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected non-empty item list')
    ids = [text(r['id']) for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate item IDs')
    return rows


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def envelope(data, project, items, **summary):
    return {'project': project, 'input_sha256': digest(data),
            'data_provenance': data.get('provenance', 'user supplied; not independently verified'),
            'currency': text(data['currency']), 'items': items, **summary,
            'ai_commentary': {'status': 'not_requested'},
            'execution': 'local decision support; no external actions performed'}


def markdown(report):
    # Escape cells so user-controlled text cannot break table structure.
    def cell(v):
        return str(v).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    lines = [f"# {report['project']}", '',
             f"Input SHA256: `{report['input_sha256']}`", '',
             'Calculated observations; source inputs remain unverified.', '',
             '| Item | Finding | Human review |', '|---|---|---|']
    for item in report['items']:
        lines.append('| ' + ' | '.join(cell(v) for v in
                     (item['id'], item['finding'], item['requires_human_review'])) + ' |')
    lines += ['', 'Full numeric details and evidence references are in the JSON report.',
              'Optional AI commentary is unverified and cannot authorize an action.', '']
    return '\n'.join(lines)


def cli(analyze, default_input):
    parser = argparse.ArgumentParser(description=analyze.__doc__)
    parser.add_argument('input', nargs='?', type=Path, default=Path(default_input))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--markdown', type=Path)
    parser.add_argument('--ai', action='store_true', help='Send report to the configured provider; requires key and model')
    args = parser.parse_args()
    try:
        report = analyze(json.loads(args.input.read_text()))
        if args.ai:
            from llm_commentary import summarize
            report['ai_commentary'] = summarize(report)
        rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        if args.output:
            args.output.write_text(rendered)
        if args.markdown:
            args.markdown.write_text(markdown(report))
        print(rendered, end='')
    except (ValueError, KeyError, TypeError, OSError, ArithmeticError) as exc:
        parser.exit(2, f'Input/report error: {exc}\n')
