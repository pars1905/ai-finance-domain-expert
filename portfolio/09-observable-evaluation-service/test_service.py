import concurrent.futures
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
from service import Server, db, handler, metrics, run_evaluation

TOKEN = 'x' * 40
KEY = 'fake-key-for-injected-transport'


def success(payload, key, timeout):
    assert key == KEY and payload['store'] is False and timeout == 10
    return 200, json.dumps({'status': 'completed', 'usage': {'input_tokens': 2, 'output_tokens': 3},
                             'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': 'synthetic answer'}]}]}).encode()


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'test.db'

    def run_eval(self, **kw):
        return run_evaluation(self.path, 'ExampleCo FY2025 revenue?', 'mock-model', KEY,
                              transport=success, now=1760000000, sleeper=lambda _: None, **kw)

    def test_real_measured_latency_and_usage_persist(self):
        result = self.run_eval()
        self.assertEqual((result['status'], result['observed_tokens']), ('completed', 5))
        row = metrics(self.path)['requests'][0]
        self.assertEqual((row['input_tokens'], row['output_tokens'], row['outcome']), (2, 3, 'completed'))
        self.assertGreaterEqual(row['latency_ms'], 0)
        self.assertEqual(list(metrics(self.path)['daily_reserved_or_observed_tokens'].values()), [5])
        self.assertNotIn('ExampleCo', json.dumps(metrics(self.path)))
        self.assertNotIn(KEY, json.dumps(metrics(self.path)))

    def test_retry_bounded_and_failed_attempt_charged(self):
        calls = []
        def flaky(payload, key, timeout):
            calls.append(1)
            if len(calls) < 3:
                return 429, b'{}'
            return success(payload, key, timeout)
        r = run_evaluation(self.path, 'hello', 'mock', KEY, transport=flaky, now=1760000000, sleeper=lambda _: None)
        self.assertEqual((r['attempts'], r['observed_tokens']), (3, 2 * (5 + 256) + 5))
        self.assertEqual([x['outcome'] for x in metrics(self.path)['requests']], ['retryable', 'retryable', 'completed'])

    def test_non_retryable_stops(self):
        r = run_evaluation(self.path, 'hello', 'mock', KEY, transport=lambda *a: (400, b'{}'), now=1760000000)
        self.assertEqual((r['status'], r['attempts']), ('upstream_failure', 1))

    def test_network_error_bounded(self):
        def fail(*args):
            raise OSError('private upstream detail')
        r = run_evaluation(self.path, 'hello', 'mock', KEY, transport=fail, now=1760000000, sleeper=lambda _: None)
        self.assertEqual((r['status'], r['attempts']), ('upstream_failure', 3))
        self.assertNotIn('private', json.dumps(metrics(self.path)))

    def test_budget_and_rate_limit_no_upstream_call(self):
        no = lambda *a: self.fail('transport must not run')
        self.assertEqual(run_evaluation(self.path, 'hello', 'mock', KEY, daily_budget=5,
                         transport=no, now=1760000000)['status'], 'budget_limit')
        self.run_eval(per_minute=1)
        self.assertEqual(run_evaluation(self.path, 'hello', 'mock', KEY, per_minute=1,
                         transport=no, now=1760000001)['status'], 'rate_limit')

    def test_reservations_atomic_under_concurrency(self):
        barrier = threading.Barrier(4)
        def one(_):
            barrier.wait()
            return run_evaluation(self.path, 'hello', 'mock', KEY, daily_budget=783,
                                  transport=success, now=1760000000, sleeper=lambda _: None)['status']
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(one, range(4)))
        self.assertEqual(results.count('completed'), 1)
        self.assertEqual(results.count('budget_limit'), 3)

    def test_invalid_prompt_and_usage(self):
        with self.assertRaises(ValueError):
            run_evaluation(self.path, '', 'mock', KEY, transport=success)
        r = run_evaluation(self.path, 'hello', 'mock', KEY, transport=lambda *a: (200, b'{"status":"completed","usage":{}}'), now=1760000000, sleeper=lambda _: None)
        self.assertEqual((r['status'], r['attempts']), ('upstream_failure', 3))

    def test_live_local_http_auth_limits_and_metrics(self):
        db(self.path).close()
        server = Server(('127.0.0.1', 0), handler(self.path, TOKEN, 'mock', KEY, 5000, 1, success))
        t = threading.Thread(target=server.serve_forever)
        t.start()
        self.addCleanup(lambda: (server.shutdown(), t.join(), server.server_close()))
        def call(method, route, payload=None, auth=True, content_type='application/json'):
            c = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            headers = {'Content-Type': content_type}
            if auth:
                headers['Authorization'] = 'Bearer ' + TOKEN
            c.request(method, route, body=payload, headers=headers)
            response = c.getresponse()
            code = response.status
            data = json.loads(response.read())
            c.close()
            return code, data
        self.assertEqual(call('GET', '/health', auth=False)[0], 200)
        self.assertEqual(call('GET', '/v1/metrics', auth=False)[0], 401)
        self.assertEqual(call('POST', '/v1/evaluations', b'{"prompt":"hi"}', auth=False)[0], 401)
        self.assertEqual(call('POST', '/v1/evaluations', b'{"prompt":"hi"}', content_type='text/plain')[0], 415)
        self.assertEqual(call('POST', '/v1/evaluations', b'{"prompt":"hi","prompt":"bye"}')[0], 422)
        self.assertEqual(call('POST', '/v1/evaluations', b'{"prompt":"hi"}')[0], 200)
        self.assertEqual(call('POST', '/v1/evaluations', b'{"prompt":"hi"}')[0], 429)
        self.assertEqual(call('GET', '/v1/metrics')[1]['requests'][0]['outcome'], 'completed')


if __name__ == '__main__':
    unittest.main()
