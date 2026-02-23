# Denials Triage Brief v1

Source relation: `rcm-flagship.rcm.mart_workqueue_claims` (dbt-transformed mart only).

## Decision
Focus this week on the top 2 denial buckets by priority score (covers 91.1% of weighted denial exposure).

## Status + Reason
- Status: LIMITED_CONTEXT
- Reason: Payer identity is unavailable in marts; denial reason and denied dollar values are proxy-derived for directional triage.

## Top drivers (priority-ranked)
- `AUTH_ELIG` / `Noncovered`: $13,680 across 230 claims (priority $13,680).
- `OTHER_PROXY` / `Other Denial`: $6,550 across 309 claims (priority $3,930).
- `OTHER_PROXY` / `Allowed`: $2,300 across 3790 claims (priority $1,380).
- `CODING_DOC` / `Medically Unnecessary`: $230 across 42 claims (priority $230).
- `CODING_DOC` / `Bundled / No Pay`: $90 across 2 claims (priority $90).

## This week actions (reversible)
- Validate top denial buckets against sample claim evidence before scaling any process changes.
- Route top workqueue items to owner queues with evidence requirements attached.
- Re-run this triage next cycle and compare top-2 stability before committing irreversible workflow changes.

## Workqueue (25 claims)
- Output: [`exports/denials_workqueue_v1.csv`](../exports/denials_workqueue_v1.csv)
- Summary: [`exports/denials_triage_summary_v1.csv`](../exports/denials_triage_summary_v1.csv)
- Eligibility/Auth team: 25 claims in the top 25.

## Stability (Current vs Prior dataset-week)
- Current dataset-week: `2011-02-21`
- Prior dataset-week: `2011-02-14`

| denial_bucket | current_rank | prior_rank | rank_delta | current_share | prior_share | share_delta | delta_priority_score |
|---|---:|---:|---:|---:|---:|---:|---:|
| AUTH_ELIG | 1 | 1 | 0 | 70.8% | 61.0% | 9.8% | $-5,640 |
| OTHER_PROXY | 2 | 2 | 0 | 27.6% | 37.7% | -10.2% | $-6,624 |
| CODING_DOC | 3 | 3 | 0 | 1.7% | 1.2% | 0.5% | $-50 |
| DUPLICATE | 4 | 4 | 0 | 0.0% | 0.1% | -0.1% | $-30 |

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
