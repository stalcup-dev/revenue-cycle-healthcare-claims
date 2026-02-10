# Denials Triage Brief v1

Source relation: `rcm-flagship.rcm.mart_workqueue_claims` (dbt-transformed mart only).

## Decision
Focus this week on the top 2 denial buckets by priority score (covers 89.0% of weighted denial exposure).

## Status + Reason
- Status: LIMITED_CONTEXT
- Reason: Payer identity is unavailable in marts; denial reason and denied dollar values are proxy-derived for directional triage.

## Top drivers (priority-ranked)
- `AUTH_ELIG` / `Noncovered`: $17,600 across 310 claims (priority $17,600).
- `OTHER_PROXY` / `Other Denial`: $10,790 across 471 claims (priority $6,474).
- `OTHER_PROXY` / `Allowed`: $4,120 across 5716 claims (priority $2,472).
- `CODING_DOC` / `Medically Unnecessary`: $330 across 70 claims (priority $330).
- `CODING_DOC` / `Bundled / No Pay`: $90 across 2 claims (priority $90).

## This week actions (reversible)
- Validate top denial buckets against sample claim evidence before scaling any process changes.
- Route top workqueue items to owner queues with evidence requirements attached.
- Re-run this triage next cycle and compare top-2 stability before committing irreversible workflow changes.

## Workqueue (25 claims)
- Output: [`exports/denials_workqueue_v1.csv`](../exports/denials_workqueue_v1.csv)
- Summary: [`exports/denials_triage_summary_v1.csv`](../exports/denials_triage_summary_v1.csv)
- Eligibility/Auth team: 25 claims in the top 25.

## Falsification
If next cycle the top-2 buckets do not remain in the top set or weighted exposure shifts materially, we change focus and re-prioritize.

## Data Gaps / Next Data Needed
- Missing payer identity dimension (plan/carrier): not present in current marts.
- `service_date` is estimated from `aging_days` (proxy).
- `denied_amount` uses `denied_potential_allowed_proxy_amt` (proxy).
- Needed in marts: `payer_id` / `payer_name`, actual `service_from_date`, and actual denial codes (`CARC`/`RARC`) if available.

## Column mapping (required conceptual fields)
| Conceptual field | Source column used | Notes |
|---|---|---|
| claim_id | `clm_id` | direct claim identifier |
| payer_dim_status | constant `MISSING_IN_MART` | payer identity is unavailable in selected marts |
| denial_flag | derived from `p_denial/top_denial_prcsg/top_denial_group/denied_potential_allowed_proxy_amt` | deterministic OR-rule |
| denial_reason | `top_denial_group` fallback `top_denial_prcsg` | proxy reason when detailed reason absent |
| denied_amount | `denied_potential_allowed_proxy_amt` | proxy denied amount |
| service_date | `DATE_SUB(CURRENT_DATE(), INTERVAL aging_days DAY)` | estimated service date proxy |
| facility_or_service_line | `top_denial_group` | service-line proxy |

Note: This brief intentionally excludes payer-level conclusions because payer identity is missing in current marts.
