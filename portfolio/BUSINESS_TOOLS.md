# Shared analyst workflow, optional AI and validation

Projects 04–06 are local decision-support prototypes built with AI assistance.
Default runs are offline and free of third-party Python dependencies. Data,
stakeholder requirements and acceptance scenarios are authored examples. No
client engagement, production deployment or financial saving is demonstrated.

## Optional AI commentary

The report's `ai_commentary.status` is `not_requested` by default. To make a
real call, set `OPENAI_API_KEY` and `OPENAI_MODEL` in your own environment,
then add `--ai` to a project's normal command. Do not put secrets in input
files, source code or git. Choose a model your API project can access.

For example, after setting those variables, from repository root:

```bash
python portfolio/04-budget-variance-assistant/analyze.py --ai --output /tmp/budget-ai-report.json
```

This explicit flag sends the calculated report, including item identifiers
and evidence strings, to OpenAI and may incur usage charges. Use synthetic or
otherwise permitted data. There is no automatic retry: one request, a 30-second
timeout, 50 KB submitted-report cap and 700 output-token cap. Redirects are
disabled. The request uses `store: false`; this setting alone is not a guarantee
about all provider retention practices. No tools are supplied to the model.

The model is instructed to give a short Turkish briefing with item IDs and
separate observations from investigation questions. Its text is stored only in
`ai_commentary`, marked `unverified_ai_commentary`; it is not used for calculations,
scores, queue transitions or decisions. Input text is treated as untrusted data.
Prompt instructions do not guarantee factuality or eliminate prompt injection.
The commentary is not independently checked; human review is required.

API errors/refusals/incomplete responses leave the calculations available with
status `unavailable`. Usage, response ID, actual returned model, observed request
latency, prompt version and submitted-report hash are saved on a successful call.
Costs are not estimated from token counts because no pricing table is embedded.

Adapter behavior is tested with mocked HTTP responses. **No real-key model call
has been verified for these projects.** Offline sample reports contain no model output.
Implementation reference: [OpenAI Responses API](https://developers.openai.com/api/reference/resources/responses/methods/create).

## Persistent local review

Each project's README gives a `review_decision.py` command. Use `acknowledge`
or `request_changes`, a reviewer label and a note. SQLite records the full report
SHA256, item ID, decision, reviewer, note and UTC timestamp. Only findings marked
for review can be recorded. Duplicate identical submissions return the same
record; conflicting edits to that report/item are rejected. Revised inputs
produce a new report to review. Including changed AI commentary also changes
the full-report fingerprint and requires a new review.

This is a single-user local audit demonstration. Reviewer names are self-declared,
not authenticated, and an owner can directly modify the SQLite file. There is
no claim of tamper-proof storage or production authorization. A review never
sends messages, selects a supplier, adjusts a budget or moves money.

## Validation and pilot readiness

From repository root run `python portfolio/run_checks.py`. Project suites cover
business-rule boundaries, reconciliation, exclusion and sensitivity; shared
tests cover persistent/idempotent review, malformed model responses and failure
isolation. Test counts describe software checks, not business accuracy.

For a real pilot, obtain permissioned data, agree acceptance labels with users,
independently verify source values and compare matched manual/assisted tasks.
Measure review time and error rates before claiming impact. Add authentication,
access controls and durable service operations only when moving beyond this demo.
