"""Loopback-only standard-library HTTP API. Local prototype, not a production server."""
import argparse
import hashlib
import hmac
import json
import os
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from store import ACTIONS, APIError, Store, canonical


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def load_json(raw):
    def invalid_constant(value):
        raise ValueError('Non-finite JSON constant')
    return json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=invalid_constant)


def users_from_config(config):
    if not isinstance(config, dict) or not config:
        raise ValueError('Non-empty FINANCE_API_USERS_JSON required')
    users, seen = [], set()
    for actor, settings in config.items():
        if not isinstance(actor, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', actor):
            raise ValueError('Invalid actor identifier')
        if not isinstance(settings, dict) or set(settings) != {'token', 'role'}:
            raise ValueError('Each actor needs token and role only')
        token, role = settings['token'], settings['role']
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,256}', token):
            raise ValueError('Tokens must have 32–256 URL-safe characters')
        if role not in ('analyst', 'approver', 'operator') or token in seen:
            raise ValueError('Invalid role or duplicate token')
        seen.add(token)
        users.append((actor, role, hashlib.sha256(token.encode()).digest()))
    return users


def create_server(database, config, port=0):
    users, store = users_from_config(config), Store(database)

    class Handler(BaseHTTPRequestHandler):
        server_version = 'FinanceReviewDemo'
        sys_version = ''

        def log_message(self, format, *args):
            pass  # Do not emit user-controlled paths, headers or payloads.

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def send_json(self, status, payload, replay=False):
            body = (canonical(payload) + '\n').encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Connection', 'close')
            if replay:
                self.send_header('Idempotency-Replayed', 'true')
            if status == 401:
                self.send_header('WWW-Authenticate', 'Bearer')
            self.end_headers()
            self.wfile.write(body)

        def authenticate(self):
            headers = self.headers.get_all('Authorization', [])
            if len(headers) != 1 or not headers[0].startswith('Bearer '):
                raise APIError(401, 'Bearer credential required')
            token = headers[0][7:]
            if not re.fullmatch(r'[A-Za-z0-9_-]{32,256}', token):
                raise APIError(401, 'Invalid credential')
            hashed, matched = hashlib.sha256(token.encode()).digest(), None
            for actor, role, expected in users:
                if hmac.compare_digest(hashed, expected):
                    matched = (actor, role)
            if matched is None:
                raise APIError(401, 'Invalid credential')
            return matched

        def payload(self):
            if self.headers.get('Transfer-Encoding') is not None:
                raise APIError(400, 'Transfer-Encoding not supported')
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not re.fullmatch(r'[0-9]+', lengths[0]):
                raise APIError(411, 'One Content-Length required')
            size = int(lengths[0])
            if not 1 <= size <= 65536:
                raise APIError(413, 'Body must be 1–65536 bytes')
            if self.headers.get_content_type() != 'application/json':
                raise APIError(415, 'Content-Type must be application/json')
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise APIError(400, 'Incomplete request body')
            try:
                return load_json(raw)
            except (ValueError, UnicodeError, RecursionError):
                raise APIError(400, 'Invalid JSON body') from None

        def dispatch(self, method):
            try:
                if method == 'GET' and self.path == '/health':
                    return self.send_json(200, {'status': 'ok', 'mode': 'loopback_demo'})
                actor, role = self.authenticate()
                if method == 'POST':
                    payload = self.payload()
                    keys = self.headers.get_all('Idempotency-Key', [])
                    key = keys[0] if len(keys) == 1 else None
                    if self.path == '/v1/reviews':
                        status, result, replay = store.mutate(actor, role, self.path, key, payload)
                    else:
                        match = re.fullmatch(r'/v1/reviews/([a-f0-9]{32})/(submit|approve|reject|mock-post)', self.path)
                        if not match:
                            raise APIError(404, 'Route not found')
                        review_id, action = match.groups()
                        status, result, replay = store.mutate(actor, role, self.path, key, payload, review_id, action)
                    return self.send_json(status, result, replay)
                match = re.fullmatch(r'/v1/reviews/([a-f0-9]{32})(/events)?', self.path)
                if method == 'GET' and match:
                    review_id, events = match.groups()
                    return self.send_json(200, {'events': store.events(review_id)} if events else store.get(review_id))
                raise APIError(404, 'Route not found')
            except APIError as exc:
                self.send_json(exc.status, {'error': exc.message})
            except sqlite3.OperationalError:
                self.send_json(503, {'error': 'Database unavailable; retry with the same idempotency key'})
            except sqlite3.Error:
                self.send_json(500, {'error': 'Database operation failed; no transition committed'})
            except (TypeError, ValueError, RecursionError):
                self.send_json(422, {'error': 'Invalid request data'})

        def do_GET(self):
            self.dispatch('GET')

        def do_POST(self):
            self.dispatch('POST')

    class Server(ThreadingHTTPServer):
        # Wait for bounded request handlers before temporary DB cleanup.
        daemon_threads = False
        block_on_close = True
    return Server(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    try:
        if not 0 <= args.port <= 65535:
            raise ValueError('Port must be from 0 to 65535; 0 selects an ephemeral port')
        config = load_json(os.environ.get('FINANCE_API_USERS_JSON', ''))
        with create_server(args.db, config, args.port) as server:
            print(f'Local demo listening on http://127.0.0.1:{server.server_port}', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
    except (ValueError, OSError, sqlite3.Error):
        parser.exit(2, 'Startup failed: check user configuration, database path and port.\n')
