"""Transactional review workflow, immutable report snapshots and local mock receipts."""
import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

PROJECTS = {'04': 'Budget Variance Investigation Assistant',
            '05': 'Cash Collection Prioritization Workbench',
            '06': 'Supplier Proposal Comparison Assistant',
            '07': 'Cited Financial Document Assistant'}
ACTIONS = {'submit': ('analyst', 'DRAFT', 'SUBMITTED'),
           'approve': ('approver', 'SUBMITTED', 'APPROVED'),
           'reject': ('approver', 'SUBMITTED', 'REJECTED'),
           'mock-post': ('operator', 'APPROVED', 'MOCK_POSTED')}


class APIError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def nonempty(value, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise APIError(422, 'Invalid text field')
    return value


def create_payload(payload):
    if not isinstance(payload, dict) or set(payload) != {'title', 'source_project', 'report'}:
        raise APIError(422, 'Expected title, source_project and report only')
    nonempty(payload['title'], 200)
    project, report = payload['source_project'], payload['report']
    if not isinstance(project, str) or project not in PROJECTS or not isinstance(report, dict):
        raise APIError(422, 'Unsupported source project/report')
    if report.get('project') != PROJECTS[project]:
        raise APIError(422, 'Report project does not match source_project')
    field = 'corpus_sha256' if project == '07' else 'input_sha256'
    if not isinstance(report.get(field), str) or not re.fullmatch('[a-f0-9]{64}', report[field]):
        raise APIError(422, 'Report must carry its source input/corpus SHA256')
    if len(canonical(report).encode()) > 50000:
        raise APIError(413, 'Report exceeds 50 KB cap')


class Store:
    def __init__(self, database):
        self.database = str(database)
        if self.database == ':memory:':
            raise ValueError('Use a file database for per-request connections')
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, source_project TEXT NOT NULL,
                    report_json TEXT NOT NULL, snapshot_sha TEXT NOT NULL, creator TEXT NOT NULL,
                    status TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, review_id TEXT NOT NULL REFERENCES reviews(id),
                    actor TEXT NOT NULL, from_status TEXT, to_status TEXT NOT NULL,
                    note TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS mock_receipts (
                    review_id TEXT PRIMARY KEY REFERENCES reviews(id), receipt_id TEXT UNIQUE NOT NULL,
                    snapshot_sha TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS idempotency (
                    actor TEXT NOT NULL, route TEXT NOT NULL, key TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    status INTEGER NOT NULL, response_json TEXT NOT NULL,
                    PRIMARY KEY(actor, route, key));
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            yield db
        finally:
            db.close()

    def get(self, review_id, db=None):
        if db is None:
            with self.connect() as connection:
                return self.get(review_id, connection)
        row = db.execute('SELECT * FROM reviews WHERE id=?', (review_id,)).fetchone()
        if row is None:
            raise APIError(404, 'Review not found')
        result = dict(row)
        result['report'] = json.loads(result.pop('report_json'))
        receipt = db.execute('SELECT receipt_id,snapshot_sha,created_at FROM mock_receipts WHERE review_id=?',
                             (review_id,)).fetchone()
        result['mock_receipt'] = dict(receipt) if receipt else None
        return result

    def events(self, review_id):
        with self.connect() as db:
            self.get(review_id, db)
            return [dict(row) for row in db.execute('SELECT * FROM events WHERE review_id=? ORDER BY sequence', (review_id,))]

    def mutate(self, actor, role, route, key, payload, review_id=None, action=None):
        required_role = 'analyst' if action is None else ACTIONS[action][0]
        if role != required_role:
            raise APIError(403, 'Role cannot perform this action')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{8,128}', key):
            raise APIError(400, 'Valid Idempotency-Key required')
        fingerprint = sha(payload)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                previous = db.execute('SELECT * FROM idempotency WHERE actor=? AND route=? AND key=?',
                                      (actor, route, key)).fetchone()
                if previous:
                    if previous['fingerprint'] != fingerprint:
                        raise APIError(409, 'Idempotency key reused with different payload')
                    db.commit()
                    return previous['status'], json.loads(previous['response_json']), True
                if action is None:
                    create_payload(payload)
                    review_id = uuid.uuid4().hex
                    db.execute('INSERT INTO reviews VALUES (?,?,?,?,?,?,?,?,?)',
                               (review_id, payload['title'], payload['source_project'], canonical(payload['report']),
                                sha(payload['report']), actor, 'DRAFT', 1, now()))
                    old, new, version, note = None, 'DRAFT', 1, 'Snapshot created; source truth not verified.'
                    status = 201
                else:
                    if not isinstance(payload, dict) or set(payload) != {'expected_version', 'note'}:
                        raise APIError(422, 'Expected expected_version and note only')
                    if type(payload['expected_version']) is not int or payload['expected_version'] < 1:
                        raise APIError(422, 'expected_version must be a positive integer')
                    note = nonempty(payload['note'], 1000)
                    current = self.get(review_id, db)
                    if action == 'submit' and current['creator'] != actor:
                        raise APIError(403, 'Only creator can submit')
                    if action in ('approve', 'reject') and current['creator'] == actor:
                        raise APIError(403, 'Creator cannot decide own review')
                    if current['version'] != payload['expected_version']:
                        raise APIError(409, 'Stale review version; reload before deciding')
                    _, old, new = ACTIONS[action]
                    if current['status'] != old:
                        raise APIError(409, 'Invalid workflow transition')
                    version = current['version'] + 1
                    db.execute('UPDATE reviews SET status=?,version=? WHERE id=?', (new, version, review_id))
                    if action == 'mock-post':
                        db.execute('INSERT INTO mock_receipts VALUES (?,?,?,?)',
                                   (review_id, 'mock-' + uuid.uuid4().hex, current['snapshot_sha'], now()))
                    status = 200
                db.execute('INSERT INTO events(review_id,actor,from_status,to_status,note,version,created_at) '
                           'VALUES (?,?,?,?,?,?,?)', (review_id, actor, old, new, note, version, now()))
                result = self.get(review_id, db)
                db.execute('INSERT INTO idempotency VALUES (?,?,?,?,?,?)',
                           (actor, route, key, fingerprint, status, canonical(result)))
                db.commit()
                return status, result, False
            except BaseException:
                db.rollback()
                raise
