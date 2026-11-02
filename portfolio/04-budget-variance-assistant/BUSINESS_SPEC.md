# Business requirements and acceptance evidence

## Problem and stakeholders

An FP&A analyst needs to explain material budget differences without treating
an attractive narrative as proven causality. The controller owns thresholds;
department owners verify quantities and prices. The demo is a proposed workflow,
not requirements gathered from an actual client.

## Process

1. Analyst supplies one-period, one-currency line data and controller thresholds.
2. Validate IDs, types and any supplied ledger totals; reject invalid batches.
3. Reconcile amounts and price/volume bridges; show every line, including unchanged ones.
4. Route material lines for review with stable evidence references and questions.
5. Analyst checks sources, optionally reads AI commentary, and records an acknowledgement
   or request for changes. Corrected input generates a new report and review identity.

## Acceptance scenarios

| Requirement | Acceptance evidence |
|---|---|
| Bridge must reconcile at line and net contribution level | `test_every_line_and_contribution_reconciles` |
| Expense increases must be unfavorable | `test_expense_and_new_spend_review` |
| Zero-budget spending must not cause division by zero | Same test, `new-service` fixture |
| Materiality must apply both policy thresholds | `test_relative_and_absolute_thresholds_both_apply` |
| Bad supplied actual total must stop the run | `test_bad_ledger_total_rejected` |
| Review must persist and reference the full report | Shared SQLite tests in `test_business_tools.py` |

## Pilot measurement plan

On permitted data, independently verify the bridge and materiality labels.
Measure analyst time for identical manual and assisted tasks, controlling for
learning/order effects. Record incorrect explanations and missed exceptions.
Do not call this pilot complete or claim time saved from the synthetic demo.

Out of scope: postings, ledger updates, full FP&A planning and causal attribution.
