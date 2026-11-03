"""Bounded, local evaluation gateway with persistent SQLite quotas and attempt telemetry."""
import argparse
import hashlib
import hmac
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_BODY = 8192
MAX_OUTPUT = 256
MAX_ATTEMPTS = 3
RETRYABLE = {429, 500, 502, 503, 504}


def utc():
    return datetime.now(timezone.utc).isoformat()


def db(path):
    connection = sqlite3.connect(path, timeout=5, isolation_level=None)
    connection.execute('PRAGMA busy_timeout=5000')
    connection.execute('CREATE TABLE IF NOT EXISTS budgets (day TEXT PRIMARY KEY, reserved INTEGER NOT NULL)')
    connection.execute('CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL, prompt_sha TEXT NOT NULL, status TEXT NOT NULL, reserved INTEGER NOT NULL, actual INTEGER NOT NULL DEFAULT 0)')
    connection.execute('CREATE TABLE IF NOT EXISTS attempts (request_id INTEGER NOT NULL, number INTEGER NOT NULL, at_utc TEXT NOT NULL, latency_ms REAL NOT NULL, http_status INTEGER NOT NULL, input_tokens INTEGER, output_tokens INTEGER, outcome TEXT NOT NULL, FOREIGN KEY(request_id) REFERENCES requests(id))')
    return connection


def reserve(path, prompt_hash, capacity, daily_budget, per_minute, now):
    day = datetime.fromtimestamp(now, timezone.utc).date().isoformat()
    with closing(db(path)) as c, c:
        c.execute('BEGIN IMMEDIATE')
        count = c.execute('SELECT count(*) FROM requests WHERE at>?', (now - 60,)).fetchone()[0]
        used = c.execute('SELECT reserved FROM budgets WHERE day=?', (day,)).fetchone()
        if count >= per_minute:
            return None, 'rate_limit'
        if (used[0] if used else 0) + capacity > daily_budget:
            return None, 'budget_limit'
        c.execute('INSERT INTO budgets(day,reserved) VALUES(?,?) ON CONFLICT(day) DO UPDATE SET reserved=reserved+excluded.reserved', (day, capacity))
        rid = c.execute('INSERT INTO requests(at,prompt_sha,status,reserved) VALUES(?,?,?,?)', (now, prompt_hash, 'pending', capacity)).lastrowid
        return rid, None


def finish(path, rid, day, reserved, actual, status):
    with closing(db(path)) as c, c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('UPDATE requests SET status=?,actual=? WHERE id=?', (status, actual, rid))
        c.execute('UPDATE budgets SET reserved=reserved-? WHERE day=?', (reserved - actual, day))


def record(path, rid, attempt, latency, http_status, input_tokens, output_tokens, outcome):
    with closing(db(path)) as c, c:
        c.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?)', (rid, attempt, utc(), latency, http_status, input_tokens, output_tokens, outcome))


def real_transport(payload, key, timeout):
    req = urllib.request.Request('https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode(), method='POST',
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as response:
            return response.status, response.read(65537)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(65537)


def run_evaluation(path, prompt, model, api_key, daily_budget=6000, per_minute=5,
                   transport=None, now=None, sleeper=time.sleep):
    if not isinstance(prompt, str) or not 1 <= len(prompt) <= 2000 or not prompt.strip():
        raise ValueError('prompt must be 1–2000 characters')
    if any(not isinstance(v, str) or not v.strip() for v in (model, api_key)):
        raise ValueError('model and upstream API key required')
    if any(type(v) is not int or v < 1 for v in (daily_budget, per_minute)):
        raise ValueError('Budgets and rate limits must be positive integers')
    now = time.time() if now is None else now
    # Conservative reservation: each of three attempts may use the full output cap.
    input_estimate = max(1, len(prompt.encode('utf-8')))
    capacity = MAX_ATTEMPTS * (input_estimate + MAX_OUTPUT)
    rid, refusal = reserve(path, hashlib.sha256(prompt.encode()).hexdigest(), capacity, daily_budget, per_minute, now)
    if refusal:
        return {'status': refusal, 'request_id': None, 'attempts': 0}
    day = datetime.fromtimestamp(now, timezone.utc).date().isoformat()
    total = 0
    status = 'upstream_failure'
    response_text = None
    attempts = 0
    send = transport or real_transport
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            attempts = attempt
            started = time.monotonic()
            code, body, outcome, it, ot = 0, b'', 'network_error', None, None
            try:
                code, body = send({'model': model, 'input': prompt, 'store': False,
                                   'max_output_tokens': MAX_OUTPUT}, api_key, 10)
                if len(body) > 65536:
                    raise ValueError('upstream response too large')
                try:
                    parsed = json.loads(body)
                    if not isinstance(parsed, dict):
                        raise ValueError('invalid upstream response')
                except (ValueError, UnicodeError):
                    if code == 200:
                        raise
                    parsed = {}  # Error bodies may be HTML or empty; retry by HTTP status.
                usage = parsed.get('usage', {})
                it = usage.get('input_tokens') if isinstance(usage, dict) else None
                ot = usage.get('output_tokens') if isinstance(usage, dict) else None
                if code == 200:
                    if parsed.get('status') != 'completed' or type(it) is not int or type(ot) is not int or it < 0 or ot < 0 or it > input_estimate or ot > MAX_OUTPUT:
                        raise ValueError('missing or out-of-bound token usage')
                    fragments = [p.get('text', '') for item in parsed.get('output', []) if item.get('type') == 'message' for p in item.get('content', []) if p.get('type') == 'output_text']
                    response_text = ''.join(fragments)
                    if not response_text or len(response_text) > 8192:
                        raise ValueError('missing or oversized output')
                    total += it + ot
                    outcome, status = 'completed', 'completed'
                else:
                    # Failed responses may report usage; otherwise reserve the full attempt allowance.
                    if type(it) is int and type(ot) is int and 0 <= it <= input_estimate and 0 <= ot <= MAX_OUTPUT:
                        total += it + ot
                    else:
                        total += input_estimate + MAX_OUTPUT
                    outcome = 'retryable' if code in RETRYABLE else 'upstream_error'
            except (OSError, ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError):
                total += input_estimate + MAX_OUTPUT
                outcome = ('upstream_error' if code and code != 200 and code not in RETRYABLE
                           else 'network_or_protocol_error')
                code = code or 0
                it = ot = None
            latency = round((time.monotonic() - started) * 1000, 3)
            record(path, rid, attempt, latency, code, it if type(it) is int else None,
                   ot if type(ot) is int else None, outcome)
            if outcome == 'completed' or outcome not in ('retryable', 'network_or_protocol_error') or attempt == MAX_ATTEMPTS:
                break
            sleeper(min(0.1 * 2 ** (attempt - 1), 0.4))
    finally:
        finish(path, rid, day, capacity, total, status)
    return {'status': status, 'request_id': rid, 'attempts': attempts,
            'observed_tokens': total, 'output': response_text if status == 'completed' else None}


def metrics(path):
    with closing(db(path)) as c, c:
        rows = c.execute('SELECT r.id,r.status,a.number,a.latency_ms,a.http_status,a.input_tokens,a.output_tokens,a.outcome FROM requests r JOIN attempts a ON r.id=a.request_id ORDER BY r.id,a.number').fetchall()
        budgets = c.execute('SELECT day,reserved FROM budgets ORDER BY day').fetchall()
    return {'scope': 'local service telemetry; failed attempt usage can be an upper-bound estimate',
            'requests': [{'id': r[0], 'status': r[1], 'attempt': r[2], 'latency_ms': r[3], 'http_status': r[4], 'input_tokens': r[5], 'output_tokens': r[6], 'outcome': r[7]} for r in rows],
            'daily_reserved_or_observed_tokens': dict(budgets)}


class Server(ThreadingHTTPServer):
    daemon_threads = False
    block_on_close = True


def handler(db_path, token, model, upstream_key, daily_budget, per_minute, transport=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Avoid logging prompt, authorization header, and query string.

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def reply(self, code, payload):
            raw = json.dumps(payload, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(raw)

        def authorized(self):
            headers = self.headers.get_all('Authorization', [])
            return len(headers) == 1 and hmac.compare_digest(
                headers[0].encode('utf-8'), ('Bearer ' + token).encode('utf-8'))

        def do_GET(self):
            if self.path == '/health':
                return self.reply(200, {'status': 'ok'})
            if not self.authorized():
                return self.reply(401, {'error': 'unauthorized'})
            if self.path == '/v1/metrics':
                try:
                    return self.reply(200, metrics(db_path))
                except sqlite3.Error:
                    return self.reply(503, {'error': 'database unavailable'})
            return self.reply(404, {'error': 'not_found'})

        def do_POST(self):
            if not self.authorized():
                return self.reply(401, {'error': 'unauthorized'})
            if self.path != '/v1/evaluations':
                return self.reply(404, {'error': 'not_found'})
            if self.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                return self.reply(415, {'error': 'application/json required'})
            try:
                lengths = self.headers.get_all('Content-Length', [])
                if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
                    raise ValueError('one content length required')
                length = int(lengths[0])
            except (KeyError, ValueError, TypeError):
                return self.reply(411, {'error': 'valid content length required'})
            if length < 1 or length > MAX_BODY or self.headers.get('Transfer-Encoding'):
                return self.reply(413, {'error': 'invalid body size or framing'})
            try:
                def unique(pairs):
                    obj = {}
                    for k, v in pairs:
                        if k in obj:
                            raise ValueError('duplicate key')
                        obj[k] = v
                    return obj
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError('incomplete body')
                body = json.loads(raw, object_pairs_hook=unique,
                                  parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
                if not isinstance(body, dict) or set(body) != {'prompt'}:
                    raise ValueError('only prompt is allowed')
                result = run_evaluation(db_path, body['prompt'], model, upstream_key,
                                        daily_budget, per_minute, transport=transport)
            except (ValueError, TypeError, UnicodeDecodeError, RecursionError):
                return self.reply(422, {'error': 'invalid evaluation request'})
            except sqlite3.Error:
                return self.reply(503, {'error': 'database unavailable'})
            code = 200 if result['status'] == 'completed' else 429 if result['status'] in ('rate_limit', 'budget_limit') else 502
            return self.reply(code, result)
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=ROOT / 'telemetry.db')
    parser.add_argument('--port', type=int, default=8081)
    parser.add_argument('--daily-token-budget', type=int, default=6000)
    parser.add_argument('--requests-per-minute', type=int, default=5)
    args = parser.parse_args()
    token = os.environ.get('EVAL_SERVICE_TOKEN', '')
    key = os.environ.get('OPENAI_API_KEY', '')
    model = os.environ.get('OPENAI_MODEL', '')
    if len(token) < 32 or not key or not model or args.daily_token_budget < 1 or args.requests_per_minute < 1 or not 0 <= args.port <= 65535:
        parser.exit(2, 'Configuration error: valid EVAL_SERVICE_TOKEN (32+), OPENAI_API_KEY, OPENAI_MODEL and positive limits required.\n')
    db(args.db).close()
    with Server(('127.0.0.1', args.port), handler(args.db, token, model, key, args.daily_token_budget, args.requests_per_minute)) as server:
        print('Local evaluation service ready on 127.0.0.1:' + str(server.server_port), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
