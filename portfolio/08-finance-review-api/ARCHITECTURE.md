# Architecture and evidence

## Decision boundary

An analyst supplies an immutable snapshot of an earlier project's financial/AI
report. An independent approver checks that evidence and decides whether it may
advance. Only an operator can create a **local mock receipt**. No external ERP,
payment gateway or model endpoint exists in this service.

| Component | Responsibility | Limit |
|---|---|---|
| `api.py` | HTTP framing, credentials, routing, safe error responses | Loopback standard-library demo; not production serving infrastructure |
| `store.py` | Role checks, state machine, transactions, report hashes, idempotency | Single-file SQLite; no multi-tenant authorization |
| `client.py` | Local authenticated test/manual requests | Rejects non-loopback base URLs; never prints bearer headers |
| `demo.py` | Real ephemeral HTTP scenario with generated credentials | Temporary DB removed at end; no live deployment claim |
| `test_api.py` | Integration, concurrency and rollback checks | Software evidence on synthetic reports, not business effectiveness |

## Atomic mutation

For every successful mutation: authenticate actor → validate role → open write
transaction → check actor/route/key replay → validate immutable snapshot or
expected version/state → update review → write receipt if needed → append event
→ save original response → commit. A conflict/error rolls back all writes.

Snapshot, events, local receipt and idempotency response live in the same SQLite
database. Atomicity demonstrated here does not imply exactly-once behavior for
real external systems. A real ERP integration would need its own delivery and
reconciliation design, such as a transactional outbox and destination idempotency.

## Representative acceptance evidence

- `test_concurrent_identical_creates_make_one_review`: four real concurrent HTTP
  requests with one key produce one review and three replays.
- `test_concurrent_decisions_allow_one_transition`: approve/reject racing on one
  version produce one success and one 409.
- `test_receipt_failure_rolls_back_status_event_and_key`: inject a SQLite failure
  at receipt insertion; no state, audit or idempotency success is left behind;
  removing the fault allows a safe retry.
- `test_post_replay_and_new_key_do_not_duplicate_receipt`: one receipt per review,
  regardless of repeat key or a later new key.
- `test_self_approval_blocked_even_if_actor_role_changes`: creator restriction
  survives role reconfiguration, beyond the ordinary role check.
- `test_no_snapshot_update_endpoint`: evidence cannot be changed through the API.
- `test_database_reopen_preserves_snapshot`: persistent report survives new DB connection.
- `test_duplicate_json_and_nonfinite_values_rejected`: ambiguous/invalid JSON rejected.

## Before any real deployment

Replace local HTTP serving with an appropriate production stack; add TLS,
organization identity, short-lived credentials, per-resource/tenant policies,
monitoring, denial auditing, backups and migrations. Independently review security
and recovery behavior. This prototype does not claim those capabilities.

The sample financial figures are fictional. Approval means a configured actor
recorded a decision against that snapshot, not that the source or analysis is true.
