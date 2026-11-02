# Business requirements and acceptance evidence

## Problem and stakeholders

A procurement analyst needs to compare bids consistently while the budget
owner sees cost, lead-time and payment tradeoffs. Technical reviewers own
mandatory criteria; the buyer makes the final selection. These stakeholder
requirements are authored for the portfolio, not collected from a client.

## Process

1. Agree scope, currency, mandatory criteria and weights before reading scores.
2. Analyst enters bid terms and logical source references.
3. Flag incomplete, non-comparable-currency and failed-criterion proposals.
4. Reconcile total contract cost for comparable bids and calculate disclosed scores.
5. Compare delivery/payment sensitivity scenarios and identify unstable rankings.
6. Human reviews evidence and records acknowledgement or a request for more data.

## Acceptance scenarios

| Requirement | Acceptance evidence |
|---|---|
| Exclude incomplete and failed-criterion proposals | `test_cost_reconciles_and_criteria_filter` |
| Missing mandatory answer cannot imply eligibility | `test_missing_criterion_prevents_ranking` |
| Invalid weights and string booleans rejected | `test_invalid_weights_rejected`, `test_false_string_not_coerced_to_true` |
| No division by zero for one/identical bids | `test_single_bid_safe_normalization`, `test_identical_bids_equal_score` |
| Expose weight-dependent ranking changes | `test_weight_sensitivity_changes_leader` |
| No comparable bid must produce no selection | `test_no_eligible_bid_returns_no_selection` |

## Pilot measurement plan

On permitted procurement examples, have a buyer independently reconcile costs
and verify exclusions. Compare review time and missing-term detection with a
manual method. Report disagreements and rank sensitivity; do not infer savings
from the price difference between fictional bids.

Out of scope: actual sourcing, legal review, supplier due diligence, award,
purchase orders and ERP integrations.
