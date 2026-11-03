# Finance Review API — local HTTP demonstration

| Actor | Request | HTTP | Replayed |
|---|---|---|---|
| unauthenticated | POST /v1/reviews | 401 | False |
| demo-analyst | POST /v1/reviews | 201 | False |
| demo-analyst | POST /v1/reviews | 201 | True |
| demo-analyst | POST /v1/reviews/af8a7df76acd4c6cb165439699d945fa/approve | 403 | False |
| demo-analyst | POST /v1/reviews/af8a7df76acd4c6cb165439699d945fa/submit | 200 | False |
| demo-approver | POST /v1/reviews/af8a7df76acd4c6cb165439699d945fa/approve | 409 | False |
| demo-approver | POST /v1/reviews/af8a7df76acd4c6cb165439699d945fa/approve | 200 | False |
| demo-operator | POST /v1/reviews/af8a7df76acd4c6cb165439699d945fa/mock-post | 200 | False |
| demo-operator | POST /v1/reviews/af8a7df76acd4c6cb165439699d945fa/mock-post | 200 | True |
| demo-operator | POST /v1/reviews/af8a7df76acd4c6cb165439699d945fa/mock-post | 409 | False |
| demo-approver | GET /v1/reviews/af8a7df76acd4c6cb165439699d945fa/events | 200 | False |
| demo-analyst | GET /v1/reviews/af8a7df76acd4c6cb165439699d945fa | 200 | False |

Final state: **MOCK_POSTED**, version 4.

Four audited transitions; exactly one local mock receipt. No external system was contacted.
Demo credentials and temporary database are discarded after the run.
