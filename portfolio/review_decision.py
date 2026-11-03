"""Record a local human review against an immutable report digest; no external actions."""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from contextlib import closing
from pathlib import Path
from finance_tools import digest, text


def record(report, item_id, decision, reviewer, note, database):
    text(reviewer)
    text(note)
    if decision not in ('acknowledge', 'request_changes'):
        raise ValueError('Unsupported review decision')
    matches = [i for i in report['items'] if i['id'] == item_id]
    if len(matches) != 1 or matches[0].get('requires_human_review') is not True:
        raise ValueError('Item must uniquely identify a reviewable finding')
    fingerprint = digest(report)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute('''CREATE TABLE IF NOT EXISTS reviews (
            report_sha TEXT NOT NULL, item_id TEXT NOT NULL, decision TEXT NOT NULL,
            reviewer TEXT NOT NULL, note TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY (report_sha, item_id))''')
        # Atomic insert makes repeated identical submissions idempotent.
        connection.execute('INSERT OR IGNORE INTO reviews VALUES (?, ?, ?, ?, ?, ?)',
                           (fingerprint, item_id, decision, reviewer, note,
                            datetime.now(timezone.utc).isoformat()))
        row = connection.execute('SELECT decision,reviewer,note,created_at FROM reviews '
                                 'WHERE report_sha=? AND item_id=?', (fingerprint, item_id)).fetchone()
        if row[:3] != (decision, reviewer, note):
            raise ValueError('An existing review is immutable; generate a new report after correcting inputs.')
    return {'report_sha256': fingerprint, 'item_id': item_id, 'decision': row[0],
            'reviewer': row[1], 'note': row[2], 'created_at': row[3],
            'effect': 'local review record only; no message, payment, purchase or other external action'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--item-id', required=True)
    parser.add_argument('--decision', choices=('acknowledge', 'request_changes'), required=True)
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--note', required=True)
    parser.add_argument('--db', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = record(json.loads(args.report.read_text()), args.item_id, args.decision,
                        args.reviewer, args.note, args.db)
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
        parser.exit(2, f'Review error: {exc}\n')
