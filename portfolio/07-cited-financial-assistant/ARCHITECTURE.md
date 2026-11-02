# Engineering decisions and acceptance evidence

## Goal

Help a financial analyst find inspectable evidence for a bounded factual question.
Every displayed generated draft must cite retrieved text; unsupported drafts are
rejected. This is a local portfolio prototype built with AI assistance, not an
authenticated enterprise service or investment-advice product.

## Why this implementation

| Decision | Purpose and tradeoff |
|---|---|
| Plain JSON text corpus | Easy to inspect and version; no PDF/OCR ingestion or automatic fact extraction |
| Explicit entity/period filters | Avoid obvious cross-company/year retrieval; user must choose correct metadata |
| Lexical BM25 | Reproducible and dependency-free; misses paraphrases and broad multilingual queries |
| Paragraph spans plus SHA256 | Make exact evidence verifiable; not semantic validation or tamper-proof document provenance |
| Offline extractive baseline | Useful without keys; do not misrepresent it as LLM generation |
| Structured optional generation | Real API request implementation with bounded output; requires compatible model and permitted credentials |
| Fail-closed citation checks | Hide malformed/unknown/changed evidence; may reject otherwise valid paraphrases/numeric formats |
| Separate status for unverified meaning | Avoid treating citations as proof of financial interpretation |
| No automatic retries/tools | Bound one invocation and keep source text from triggering external actions; no high-availability behavior |

## Acceptance evidence

- `test_company_and_year_are_isolated`: company/year distractor sources cannot leak across filters.
- `test_unicode_offsets_use_python_characters`: literal quotes reconstruct from Unicode source offsets.
- `test_unknown_topic_and_missing_company_abstain`: unsupported requests receive no excerpt.
- `test_no_evidence_skips_even_requested_model`: no paid call when retrieval is empty.
- `test_mocked_structured_generation_is_validated`: end-to-end mocked request, schema and local validation.
- `test_fabricated_quote_rejected`, `test_unknown_citation_rejected`: generated evidence must exist in context.
- `test_unsupported_number_year_and_currency_rejected`: limited financial token checks reject specific contradictions.
- `test_semantic_error_is_known_limit`: a real quote and matching amount cannot prove the narrative.
- `test_network_error_preserves_excerpts_and_redacts_message`: calculations/evidence remain usable without leaking error bodies.
- `evaluate.py`: separate authored development/holdout retrieval cases, including missing topics and source distractors.

## Security and scope

Question and source strings are untrusted. The model receives instructions to
ignore embedded commands, but instructions alone do not prevent prompt injection.
No tools are offered and the model cannot alter the corpus, place trades, contact
people or write to a financial system. Generated prose still requires review.
Markdown exports contain literal source text; use a trusted renderer and treat
any user-supplied source links/content as untrusted. No browser app is served.

Hashes identify bytes/text versions, not authorship or truth. There is no user
authentication, organization access control, encrypted document store, production
monitoring or service deployment. Those belong to later project work.

## Next verification steps

1. Run the optional request with a permitted model/key on this synthetic corpus.
   Record the returned model and observed telemetry; do not claim this is complete yet.
2. Independently label a fresh set of real, permissioned financial questions,
   including contradictory disclosures, multiple periods, tables and paraphrases.
3. Measure retrieval misses, false evidence returns, citation errors and expert-rated
   answer support separately. Preserve failures and reject unsupported comparisons.
4. Compare lexical retrieval against embeddings on a frozen evaluation protocol,
   rather than assuming a vector database improves quality.
5. Add authenticated API/document access and operational controls only when moving
   from this local prototype to a deployed service.
