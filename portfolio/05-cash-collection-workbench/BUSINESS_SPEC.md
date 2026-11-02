# Business requirements and acceptance evidence

## Problem and stakeholders

A collection lead needs an explainable daily review queue while treasury needs
clearly labeled cash scenarios. A dispute owner handles contested balances;
the account owner validates promises. These are proposed portfolio requirements,
not a client engagement or measured operating process.

## Process

1. Fix as-of date, supply customer snapshots/history and scenario rates.
2. Validate dates, balances, disputes and IDs.
3. Separate settled/current accounts, disputes and active payment promises.
4. Rank remaining overdue undisputed exposure; expose score components through formula and inputs.
5. Reviewer selects next steps and records acknowledgement or request for changes.
6. Treasury examines scenario assumptions; no external outreach or balance changes occur.

## Acceptance scenarios

| Requirement | Acceptance evidence |
|---|---|
| Disputed exposure and active promises excluded from scenarios | `test_scenarios_exclude_disputes_and_promises` |
| Empty actionable set handled safely | `test_zero_balances_do_not_divide_by_zero` |
| Amount in dispute cannot exceed balance | `test_invalid_dispute_rejected` |
| Future last-contact dates rejected | `test_future_contact_rejected` |
| Date boundaries explicit | `test_due_today_not_overdue`, `test_promise_today_is_active` |
| Ranking independent of input row order | `test_input_order_does_not_change_priority` |

## Pilot measurement plan

Test on permissioned historical snapshots without future information. Have
collection staff adjudicate whether proposed review actions are appropriate.
Measure time per reviewed account and disputed/active-promise routing errors.
Only evaluate actual cash results with a defined horizon and comparison design;
the demo's scenario rates do not establish collection effectiveness.

Out of scope: invoice aging reconstruction, credit decisions, external contact,
automatic collection, and empirical recovery prediction.
