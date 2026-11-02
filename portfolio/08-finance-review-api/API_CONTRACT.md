# HTTP contract

Base URL: `http://127.0.0.1:8080`. Apart from health, requests require
`Authorization: Bearer <configured-token>`. Mutations require one
`Idempotency-Key` of 8–128 letters, digits, underscore, dot or hyphen.
POST uses `Content-Type: application/json`, one valid `Content-Length` and a
1–65,536 byte body. Chunked requests, duplicate JSON keys and NaN/Infinity are rejected.

| Method | Path | Required role | Result |
|---|---|---|---|
| GET | `/health` | None | 200, minimal local-demo health |
| POST | `/v1/reviews` | analyst | 201, create DRAFT v1 |
| GET | `/v1/reviews/{id}` | Any configured role | 200, current review and immutable report |
| GET | `/v1/reviews/{id}/events` | Any configured role | 200, ordered successful transition events |
| POST | `/v1/reviews/{id}/submit` | analyst who created review | DRAFT → SUBMITTED |
| POST | `/v1/reviews/{id}/approve` | approver, different from creator | SUBMITTED → APPROVED |
| POST | `/v1/reviews/{id}/reject` | approver, different from creator | SUBMITTED → REJECTED |
| POST | `/v1/reviews/{id}/mock-post` | operator | APPROVED → MOCK_POSTED |

IDs are 32 lowercase hexadecimal characters. Mutation success returns 200
except creation (201), with full review, version and any local mock receipt.
Successful replay has `Idempotency-Replayed: true` and the original status/body.

## Create request

Exactly `title`, `source_project`, `report`; extra top-level keys are rejected.
Title must be nonempty and at most 200 characters. `source_project` is `04`,
`05`, `06` or `07`. `report.project` must match that project's title. The report
must carry a 64-character lowercase hexadecimal `input_sha256` (04–06) or
`corpus_sha256` (07), and fit in 50 KB when canonically serialized.

Use `sample-request.json` as a complete example. The report is stored verbatim
as canonical JSON; its SHA256 is calculated by the API as `snapshot_sha`.
Supplied source hashes are references only, not evidence of authenticity.

## Transition request

```json
{
  "expected_version": 1,
  "note": "Checked the supplied financial evidence"
}
```

Only these two keys are accepted. Version is a positive JSON integer (not a
boolean); note is nonempty and at most 1,000 characters. Each successful action
increments version. Replays are checked before version/state validation so a
lost response can be safely requested again using the same key and body.
Invalid requests are not saved as idempotency successes.

## Errors

| HTTP | Meaning |
|---|---|
| 400 | Invalid JSON, duplicate keys, unsupported transfer framing or missing/invalid idempotency key |
| 401 | Missing/invalid bearer credential |
| 403 | Role, creator or independent-review rule denied |
| 404 | Review or route not found |
| 409 | Changed payload under existing key, stale version or invalid state transition |
| 411 | Missing/ambiguous content length |
| 413 | Body/report size limit |
| 415 | Unsupported content type |
| 422 | Invalid report envelope, fields, expected version or note |
| 500 | Database operation failed and transaction rolled back |
| 503 | Database unavailable/busy; retry using the same key |

Only GET/POST routes above are implemented. Unsupported HTTP methods use the
standard server's method rejection. No public docs UI or CORS support is served.
Successful transition events are audited; denied attempts are not persisted.
