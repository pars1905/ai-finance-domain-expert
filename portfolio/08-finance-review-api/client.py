"""Loopback-only demo client; bearer tokens are never included in returned reports."""
import json
import urllib.error
import urllib.parse
import urllib.request
import argparse
import os
from pathlib import Path


def request(base_url, token, method, path, payload=None, key=None, raw=None, content_type='application/json'):
    url = urllib.parse.urlsplit(base_url)
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.path or url.query or url.fragment or url.username:
        raise ValueError('Demo client accepts a loopback HTTP base URL only')
    if not path.startswith('/') or path.startswith('//'):
        raise ValueError('Invalid request path')
    headers = {'Content-Type': content_type}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if key:
        headers['Idempotency-Key'] = key
    body = raw if raw is not None else (json.dumps(payload, allow_nan=False).encode() if payload is not None else None)
    req = urllib.request.Request(base_url + path, data=body, headers=headers, method=method)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
    try:
        response = opener.open(req, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, json.loads(response.read()), dict(response.headers)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actor', required=True, help='Actor configured in FINANCE_API_USERS_JSON')
    parser.add_argument('--method', choices=('GET', 'POST'), default='GET')
    parser.add_argument('--path', required=True)
    parser.add_argument('--payload', type=Path)
    parser.add_argument('--key')
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    try:
        config = json.loads(os.environ['FINANCE_API_USERS_JSON'])
        token = config[args.actor]['token']
        payload = json.loads(args.payload.read_text()) if args.payload else None
        status, body, headers = request(args.base_url, token, args.method, args.path, payload, args.key)
        print(json.dumps({'http_status': status, 'replayed': headers.get('Idempotency-Replayed') == 'true',
                          'body': body}, indent=2))
        raise SystemExit(0 if status < 400 else 1)
    except (OSError, ValueError, TypeError, KeyError):
        parser.exit(2, 'Client failed: check local server, actor configuration and input files.\n')
