"""Exercise a real ephemeral loopback server with generated credentials and a temporary database."""
import argparse
import json
import secrets
import tempfile
import threading
from pathlib import Path
from api import create_server
from client import request

ROOT = Path(__file__).resolve().parent


def demo():
    config = {actor: {'role': role, 'token': secrets.token_urlsafe(32)} for actor, role in
              [('demo-analyst', 'analyst'), ('demo-approver', 'approver'), ('demo-operator', 'operator')]}
    payload = json.loads((ROOT / 'sample-request.json').read_text())
    with tempfile.TemporaryDirectory() as folder:
        with create_server(Path(folder) / 'reviews.db', config) as server:
            thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            steps = []
            def call(actor, method, path, body=None, key=None, expected=200):
                token = config[actor]['token'] if actor else None
                status, result, headers = request(base, token, method, path, body, key)
                if status != expected:
                    raise RuntimeError(f'Demo step expected {expected}, got {status}')
                steps.append({'actor': actor or 'unauthenticated', 'method': method, 'path': path,
                              'http_status': status, 'replayed': headers.get('Idempotency-Replayed') == 'true',
                              'result_status': result.get('status'), 'error': result.get('error')})
                return result
            try:
                call(None, 'POST', '/v1/reviews', payload, 'create-demo-1', expected=401)
                created = call('demo-analyst', 'POST', '/v1/reviews', payload, 'create-demo-1', expected=201)
                replay = call('demo-analyst', 'POST', '/v1/reviews', payload, 'create-demo-1', expected=201)
                assert replay == created
                path = '/v1/reviews/' + created['id']
                call('demo-analyst', 'POST', path + '/approve', {'expected_version': 1, 'note': 'Own approval forbidden'},
                     'deny-own-approve', expected=403)
                call('demo-analyst', 'POST', path + '/submit', {'expected_version': 1, 'note': 'Evidence ready for independent review'}, 'submit-demo-1')
                call('demo-approver', 'POST', path + '/approve', {'expected_version': 1, 'note': 'Stale view'}, 'stale-demo-1', expected=409)
                call('demo-approver', 'POST', path + '/approve', {'expected_version': 2, 'note': 'Checked fictional source excerpt'}, 'approve-demo-1')
                posted = call('demo-operator', 'POST', path + '/mock-post', {'expected_version': 3, 'note': 'Record local mock receipt only'}, 'post-demo-1')
                repeated = call('demo-operator', 'POST', path + '/mock-post', {'expected_version': 3, 'note': 'Record local mock receipt only'}, 'post-demo-1')
                assert posted == repeated
                call('demo-operator', 'POST', path + '/mock-post', {'expected_version': 4, 'note': 'A second receipt must be blocked'}, 'post-demo-2', expected=409)
                audit = call('demo-approver', 'GET', path + '/events')['events']
                final = call('demo-analyst', 'GET', path)
            finally:
                server.shutdown()
                thread.join(timeout=5)
    return {'project': 'Finance Review API', 'scope': 'real local HTTP integration over fictional financial evidence',
            'steps': steps, 'final_status': final['status'], 'final_version': final['version'],
            'snapshot_sha256': final['snapshot_sha'], 'mock_receipt': final['mock_receipt'],
            'events': audit, 'credentials': 'ephemeral; not saved or displayed',
            'external_effects': 'none; mock receipt exists only in the temporary SQLite database',
            'limitations': ['Loopback HTTP demo, not a production server or identity provider.',
                            'Stored source evidence is supplied, not independently authenticated.',
                            'This service performs no model call or real ERP/payment operation.']}


def markdown(report):
    lines = ['# Finance Review API — local HTTP demonstration', '',
             '| Actor | Request | HTTP | Replayed |', '|---|---|---|---|']
    for step in report['steps']:
        lines.append(f"| {step['actor']} | {step['method']} {step['path']} | {step['http_status']} | {step['replayed']} |")
    lines += ['', f"Final state: **{report['final_status']}**, version {report['final_version']}.", '',
              'Four audited transitions; exactly one local mock receipt. No external system was contacted.',
              'Demo credentials and temporary database are discarded after the run.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--markdown', type=Path)
    args = parser.parse_args()
    report = demo()
    rendered = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    if args.markdown:
        args.markdown.write_text(markdown(report))
    print(rendered, end='')
