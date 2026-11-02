# Finance Review API — local HTTP demonstration

| Actor | Request | HTTP | Replayed |
|---|---|---|---|
| unauthenticated | POST /v1/reviews | 401 | False |
| demo-analyst | POST /v1/reviews | 201 | False |
| demo-analyst | POST /v1/reviews | 201 | True |
| demo-analyst | POST /v1/reviews/656511db81b8406b8d212f0c4436f747/approve | 403 | False |
| demo-analyst | POST /v1/reviews/656511db81b8406b8d212f0c4436f747/submit | 200 | False |
| demo-approver | POST /v1/reviews/656511db81b8406b8d212f0c4436f747/approve | 409 | False |
| demo-approver | POST /v1/reviews/656511db81b8406b8d212f0c4436f747/approve | 200 | False |
| demo-operator | POST /v1/reviews/656511db81b8406b8d212f0c4436f747/mock-post | 200 | False |
| demo-operator | POST /v1/reviews/656511db81b8406b8d212f0c4436f747/mock-post | 200 | True |
| demo-operator | POST /v1/reviews/656511db81b8406b8d212f0c4436f747/mock-post | 409 | False |
| demo-approver | GET /v1/reviews/656511db81b8406b8d212f0c4436f747/events | 200 | False |
| demo-analyst | GET /v1/reviews/656511db81b8406b8d212f0c4436f747 | 200 | False |

Final state: **MOCK_POSTED**, version 4.

Four audited transitions; exactly one local mock receipt. No external system was contacted.
Demo credentials and temporary database are discarded after the run.
