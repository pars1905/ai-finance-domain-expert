# 09 — Observable Evaluation Service

A local, authenticated HTTP gateway for a bounded text evaluation request. It stores attempt latency, upstream HTTP status, token usage and outcome in SQLite. It reserves a worst-case token allowance before calling upstream, applies a per-minute request limit and a UTC-day budget, and retries only 429/500/502/503/504 or network/protocol failures, at most three attempts with bounded backoff. The default demo uses an injected synthetic transport; it does not call a live model.

## Reproduce

```bash
cd portfolio/09-observable-evaluation-service
python -m unittest discover -v
python demo.py --output sample-report.json
```

`sample-report.json` is local synthetic telemetry; latency and request IDs vary per run. The tests exercise real loopback HTTP, authentication, validation, concurrent quota reservations, retries and budget accounting.

## Optional local deployment with your own key

```bash
export EVAL_SERVICE_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='your-permitted-model'
python service.py --db telemetry.db --port 8081 --daily-token-budget 6000 --requests-per-minute 5
```

From another shell in that same environment:

```bash
curl -sS http://127.0.0.1:8081/health
curl -sS -H "Authorization: Bearer $EVAL_SERVICE_TOKEN" -H 'Content-Type: application/json' \
  -d '{"prompt":"Summarize this fictional financial statement."}' http://127.0.0.1:8081/v1/evaluations
curl -sS -H "Authorization: Bearer $EVAL_SERVICE_TOKEN" http://127.0.0.1:8081/v1/metrics
```

An actual request can incur API charges. The example has **not** been verified with a real key, so upstream compatibility and latency must be confirmed in the user's environment. Keep real financial/customer data out of experiments until access and privacy arrangements are settled. The service binds to loopback only; it has no TLS, identity provider, multi-tenant separation, deployment automation, distributed quotas or production hardening. Protect `telemetry.db` as local operational data.

## Accounting and boundaries

- A prompt is limited to 2,000 characters and 8 KiB JSON body; output to 256 tokens. One call times out after ten seconds. Three attempts at most, with 0.1/0.2-second backoff. This is a request attempt bound, not a strict total wall-clock timeout.
- Before an upstream call the SQLite transaction reserves `3 × (UTF-8 prompt byte length + 256)` units. Bytes provide a conservative local estimate for typical tokenizer counts, **not** actual model tokens or monetary cost. A model whose input tokens exceed that estimate is treated as protocol failure; use a tokenizer-aware estimator for production.
- On completed responses, reported input/output usage becomes the actual observed count. On failed attempts without valid usage, the full attempt allowance remains charged. A failed 200 response with missing usage may be retried. The label `daily_reserved_or_observed_tokens` mixes verified usage and conservative estimates; it is **not** an invoice or precise cost.
- Quotas use a single SQLite file and an atomic `BEGIN IMMEDIATE` reservation. In-flight reservations count against budget. Requests have no idempotency key, so a client retry may create a second evaluation. Per-minute window counts accepted requests, including failures.
- Telemetry stores a SHA-256 prompt fingerprint rather than raw prompt, and excludes API credentials. The generated output is returned to the caller, not persisted. Local SQLite is not tamper-proof audit logging. No quality judgement or evidence citation validation is performed here; project 07 handles citation checks separately.

**CV wording after personally reproducing it:** “Built a local evaluation gateway with authenticated HTTP, SQLite-backed quota reservations, bounded retries and per-attempt latency/token telemetry; tested with synthetic transport and loopback HTTP.” Do not describe this as deployed or live-model validated.
