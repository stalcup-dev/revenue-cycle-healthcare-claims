# Case Study - Denials Triage v1 (BigQuery/dbt Mart Layer)

## Problem
- Denial follow-up teams need a weekly, defensible way to prioritize limited capacity without overclaiming recovery impact.

## Input (and limits)
- Source: `rcm-flagship.rcm.mart_workqueue_claims` (dbt-transformed mart, no raw claim reprocessing).
- Grain: claim-level triage rows.
- Known limits: payer identity is not available in this mart, service date is proxy-derived, denied amount is proxy-derived.

## Method
- Rule-based denial bucketing from available reason text into `AUTH_ELIG`, `CODING_DOC`, `TIMELY_FILING`, `DUPLICATE`, `CONTRACTUAL`, `OTHER_PROXY`.
- Priority score: `denied_amount_sum * preventability_weight`.
- Stability check between current and prior dataset week using rank and share deltas, plus top-2 overlap.

## Outputs
- Exec brief (public): [`docs/denials_triage_brief_v1.html`](denials_triage_brief_v1.html)
- Weekly operator runbook: [`docs/denials_triage_runbook_1page.md`](denials_triage_runbook_1page.md)
- Tracker template: [`docs/templates/denials_workqueue_tracker_template.md`](templates/denials_workqueue_tracker_template.md)
- Generated data outputs: `exports/denials_triage_summary_v1.csv`, `exports/denials_workqueue_v1.csv`, `exports/denials_stability_v1.csv`

## Exec-safe disclaimers
- This is directional triage support, not a recovery guarantee.
- Denial reason and denied amount can be proxy fields depending on mart availability.
- No causal claims are made from this slice.

## What changes next if marts improve
- If marts add `payer_id`/`payer_name`, true service dates, and CARC/RARC denial codes, triage can move from proxy routing to payer- and reason-precise interventions.
