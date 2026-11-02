import copy
import json
import secrets
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from api import create_server, users_from_config
from client import request
from store import APIError, Store, sha


class ReviewAPITests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / 'reviews.db'
        self.config = {actor: {'role': role, 'token': secrets.token_urlsafe(32)} for actor, role in
                       [('maker', 'analyst'), ('maker2', 'analyst'), ('checker', 'approver'), ('operator', 'operator')]}
        self.server = create_server(self.database, self.config)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'
        self.payload = json.loads(Path(__file__).with_name('sample-request.json').read_text())

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.directory.cleanup()

    def call(self, actor, method, path, body=None, key=None, **kwargs):
        token = self.config[actor]['token'] if actor else None
        return request(self.base, token, method, path, body, key, **kwargs)

    def create(self, actor='maker', key='create-0001'):
        status, result, _ = self.call(actor, 'POST', '/v1/reviews', self.payload, key)
        self.assertEqual(status, 201)
        return result

    def action(self, item, action, actor, version, key=None):
        return self.call(actor, 'POST', f"/v1/reviews/{item['id']}/{action}",
                         {'expected_version': version, 'note': 'Checked fictional evidence'},
                         key or 'action-' + secrets.token_hex(8))

    def approved(self):
        item = self.create()
        self.assertEqual(self.action(item, 'submit', 'maker', 1)[0], 200)
        status, current, _ = self.action(item, 'approve', 'checker', 2)
        self.assertEqual(status, 200)
        return current

    def test_health_and_authentication(self):
        self.assertEqual(self.call(None, 'GET', '/health')[0], 200)
        self.assertEqual(self.call(None, 'POST', '/v1/reviews', self.payload, 'create-0001')[0], 401)
        self.assertEqual(request(self.base, 'x' * 40, 'GET', '/v1/reviews/' + 'a' * 32)[0], 401)

    def test_loopback_binding(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')

    def test_create_snapshot_and_authenticated_read(self):
        item = self.create()
        self.assertEqual(item['creator'], 'maker')
        self.assertEqual(item['snapshot_sha'], sha(self.payload['report']))
        self.assertEqual(item['status'], 'DRAFT')
        status, fetched, _ = self.call('checker', 'GET', '/v1/reviews/' + item['id'])
        self.assertEqual(status, 200)
        self.assertEqual(fetched['report'], self.payload['report'])

    def test_creator_cannot_spoof_actor_field(self):
        self.payload['creator'] = 'checker'
        self.assertEqual(self.call('maker', 'POST', '/v1/reviews', self.payload, 'create-0001')[0], 422)

    def test_roles_cannot_create_or_decide_incorrectly(self):
        self.assertEqual(self.call('checker', 'POST', '/v1/reviews', self.payload, 'create-0001')[0], 403)
        item = self.create()
        self.assertEqual(self.action(item, 'approve', 'maker', 1)[0], 403)
        self.assertEqual(self.action(item, 'approve', 'operator', 1)[0], 403)

    def test_only_creator_can_submit(self):
        item = self.create()
        self.assertEqual(self.action(item, 'submit', 'maker2', 1)[0], 403)

    def test_self_approval_blocked_even_if_actor_role_changes(self):
        item = self.create()
        self.action(item, 'submit', 'maker', 1)
        with self.assertRaises(APIError) as caught:
            Store(self.database).mutate('maker', 'approver', f"/v1/reviews/{item['id']}/approve", 'approve-own-1',
                                       {'expected_version': 2, 'note': 'Role rotated'}, item['id'], 'approve')
        self.assertEqual(caught.exception.status, 403)

    def test_full_workflow_and_actor_audit(self):
        item = self.approved()
        status, posted, _ = self.action(item, 'mock-post', 'operator', 3)
        self.assertEqual(status, 200)
        self.assertEqual(posted['status'], 'MOCK_POSTED')
        self.assertEqual(posted['version'], 4)
        self.assertEqual(posted['report'], self.payload['report'])
        self.assertEqual(posted['mock_receipt']['snapshot_sha'], posted['snapshot_sha'])
        events = self.call('checker', 'GET', '/v1/reviews/' + item['id'] + '/events')[1]['events']
        self.assertEqual([e['actor'] for e in events], ['maker', 'maker', 'checker', 'operator'])
        self.assertEqual([e['version'] for e in events], [1, 2, 3, 4])

    def test_cannot_skip_submission_or_approval(self):
        item = self.create()
        self.assertEqual(self.action(item, 'approve', 'checker', 1)[0], 409)
        self.assertEqual(self.action(item, 'mock-post', 'operator', 1)[0], 409)

    def test_rejected_review_is_terminal(self):
        item = self.create()
        self.action(item, 'submit', 'maker', 1)
        status, rejected, _ = self.action(item, 'reject', 'checker', 2)
        self.assertEqual(status, 200)
        self.assertEqual(rejected['status'], 'REJECTED')
        self.assertEqual(self.action(item, 'mock-post', 'operator', 3)[0], 409)
        self.assertEqual(self.action(item, 'submit', 'maker', 3)[0], 409)

    def test_stale_version_rejected(self):
        item = self.create()
        self.action(item, 'submit', 'maker', 1)
        self.assertEqual(self.action(item, 'approve', 'checker', 1)[0], 409)

    def test_idempotent_create_is_original_response(self):
        item = self.create()
        self.action(item, 'submit', 'maker', 1)
        status, replay, headers = self.call('maker', 'POST', '/v1/reviews', self.payload, 'create-0001')
        self.assertEqual(status, 201)
        self.assertEqual(replay, item)
        self.assertEqual(headers['Idempotency-Replayed'], 'true')
        self.assertEqual(len(Store(self.database).events(item['id'])), 2)

    def test_key_reuse_with_changed_payload_conflicts(self):
        self.create()
        self.payload['title'] = 'Different submission'
        self.assertEqual(self.call('maker', 'POST', '/v1/reviews', self.payload, 'create-0001')[0], 409)

    def test_idempotency_key_required(self):
        self.assertEqual(self.call('maker', 'POST', '/v1/reviews', self.payload)[0], 400)

    def test_concurrent_identical_creates_make_one_review(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(lambda _: self.call('maker', 'POST', '/v1/reviews', self.payload, 'concurrent-1'), range(4)))
        self.assertEqual({r[0] for r in responses}, {201})
        self.assertEqual(len({r[1]['id'] for r in responses}), 1)
        self.assertEqual(sum(r[2].get('Idempotency-Replayed') == 'true' for r in responses), 3)

    def test_concurrent_decisions_allow_one_transition(self):
        item = self.create()
        self.action(item, 'submit', 'maker', 1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda action: self.action(item, action, 'checker', 2), ('approve', 'reject')))
        self.assertEqual(sorted(r[0] for r in responses), [200, 409])
        self.assertEqual(len(Store(self.database).events(item['id'])), 3)

    def test_post_replay_and_new_key_do_not_duplicate_receipt(self):
        item = self.approved()
        a = self.action(item, 'mock-post', 'operator', 3, 'mock-post-1')
        b = self.action(item, 'mock-post', 'operator', 3, 'mock-post-1')
        self.assertEqual(a[1], b[1])
        self.assertEqual(self.action(item, 'mock-post', 'operator', 4, 'mock-post-2')[0], 409)
        with Store(self.database).connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM mock_receipts').fetchone()[0], 1)

    def test_receipt_failure_rolls_back_status_event_and_key(self):
        item = self.approved()
        with Store(self.database).connect() as db:
            db.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON mock_receipts BEGIN SELECT RAISE(ABORT,'injected'); END")
        self.assertEqual(self.action(item, 'mock-post', 'operator', 3, 'mock-failure-1')[0], 500)
        current = Store(self.database).get(item['id'])
        self.assertEqual(current['status'], 'APPROVED')
        self.assertEqual(current['version'], 3)
        self.assertIsNone(current['mock_receipt'])
        self.assertEqual(len(Store(self.database).events(item['id'])), 3)
        with Store(self.database).connect() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM idempotency WHERE key=?', ('mock-failure-1',)).fetchone()[0], 0)
            db.execute('DROP TRIGGER fail_receipt')
        self.assertEqual(self.action(item, 'mock-post', 'operator', 3, 'mock-failure-1')[0], 200)

    def test_database_reopen_preserves_snapshot(self):
        item = self.create()
        self.assertEqual(Store(self.database).get(item['id']), item)

    def test_duplicate_json_and_nonfinite_values_rejected(self):
        for raw in (b'{"title":"one","title":"two"}', b'{"value":NaN}', b'not JSON'):
            self.assertEqual(self.call('maker', 'POST', '/v1/reviews', key='invalid-0001', raw=raw)[0], 400)

    def test_payload_limits_and_content_type(self):
        self.assertEqual(self.call('maker', 'POST', '/v1/reviews', key='large-0001', raw=b'x'*65537)[0], 413)
        self.assertEqual(self.call('maker', 'POST', '/v1/reviews', self.payload, 'type-0001', content_type='text/plain')[0], 415)

    def test_version_and_report_schema(self):
        bad = copy.deepcopy(self.payload)
        bad['report']['project'] = 'Wrong project'
        self.assertEqual(self.call('maker', 'POST', '/v1/reviews', bad, 'bad-report-1')[0], 422)
        item = self.create()
        status = self.call('maker', 'POST', f"/v1/reviews/{item['id']}/submit",
                           {'expected_version': True, 'note': 'Invalid boolean'}, 'bad-version-1')[0]
        self.assertEqual(status, 422)

    def test_no_snapshot_update_endpoint(self):
        item = self.create()
        self.assertEqual(self.call('maker', 'POST', '/v1/reviews/' + item['id'], self.payload, 'update-0001')[0], 404)
        self.assertEqual(Store(self.database).get(item['id'])['report'], self.payload['report'])

    def test_actor_key_scope_is_separate(self):
        a = self.create('maker', 'shared-key-1')
        b = self.create('maker2', 'shared-key-1')
        self.assertNotEqual(a['id'], b['id'])

    def test_missing_review_and_unknown_route(self):
        self.assertEqual(self.call('maker', 'GET', '/v1/reviews/' + 'a'*32)[0], 404)
        self.assertEqual(self.call('maker', 'GET', '/unknown')[0], 404)

    def test_bad_configuration_fails_closed(self):
        for config in ({}, {'user': {'token': 'short', 'role': 'analyst'}},
                       {'user': {'token': 'x'*40, 'role': 'admin'}},
                       {'a': {'token': 'x'*40, 'role': 'analyst'}, 'b': {'token': 'x'*40, 'role': 'approver'}}):
            with self.assertRaises(ValueError):
                users_from_config(config)


if __name__ == '__main__':
    unittest.main()
