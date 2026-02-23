# Denials Recovery Opportunity Brief v1

- **Source relation:** `rcm-flagship.rcm.mart_workqueue_claims` (dbt mart only)
- **Anchoring:** `DATASET_MAX_WEEK` | current `2011-02-21` | prior `2011-02-14`

## Decision
- Focus this week on top 2 denial buckets by recovery priority score.
- Top 2 buckets represent **91.1%** of current weighted exposure.

## Status + Reason
- **Status:** LIMITED_CONTEXT
- **Reason:** Ranking is directional and proxy-based; payer identity, true service dates, and CARC/RARC are not available in this mart layer.

## Recovery focus this week (top drivers)
- AUTH_ELIG / Noncovered: $13,680 weighted $6,840 (230 claims)
- OTHER_PROXY / Other Denial: $6,550 weighted $1,965 (309 claims)
- OTHER_PROXY / Allowed: $2,300 weighted $690 (3790 claims)
- CODING_DOC / Medically Unnecessary: $230 weighted $115 (42 claims)
- CODING_DOC / Bundled / No Pay: $90 weighted $45 (2 claims)

## Aging bands
| aging_band | denial_count | denied_amount_sum | priority_score_sum | priority_share |
|---|---:|---:|---:|---:|
| >90 | 4489 | $22,890 | $9,667 | 100.0% |

## Stability (Current vs Prior)
- Top2 overlap: **2/2** buckets
| denial_bucket | current_rank | prior_rank | rank_delta | current_share | prior_share | share_delta | delta_priority_score |
|---|---:|---:|---:|---:|---:|---:|---:|
| AUTH_ELIG | 1 | 1 | 0 | 70.8% | 61.0% | 9.8% | $-2,820 |
| OTHER_PROXY | 2 | 2 | 0 | 27.6% | 37.7% | -10.2% | $-3,312 |
| CODING_DOC | 3 | 3 | 0 | 1.7% | 1.2% | 0.5% | $-25 |
| DUPLICATE | 4 | 4 | 0 | 0.0% | 0.1% | -0.1% | $-15 |

## Workqueue routing
- Workqueue size: **25** claims
- Owners are bucket-mapped and include required evidence fields for first-touch.

## Falsification
- If next dataset week materially changes top-bucket ranks/shares, re-prioritize before scaling actions.

## Data gaps and proxy caveats
- `payer_dim_status='MISSING_IN_MART'` because payer identity is unavailable in current marts.
- `service_date` is proxy-derived from `aging_days`.
- `denied_amount` uses `denied_potential_allowed_proxy_amt` (proxy).

## Field mapping (proxy-aware)
| Output field | Source field | Notes |
|---|---|---|
| claim_id | `clm_id` | claim-grain identifier |
| denied_amount | `denied_potential_allowed_proxy_amt` | proxy for denied amount |
| denial_reason | `top_denial_group` / `top_denial_prcsg` | best available reason text |
| service_date | derived from `aging_days` | proxy date for dataset-week anchoring |
| payer_dim_status | constant `MISSING_IN_MART` | payer identity is unavailable |

## Generated outputs
- Summary CSV: `exports/denials_recovery_summary_v1.csv`
- Workqueue CSV: `exports/denials_recovery_workqueue_v1.csv`
- Aging bands CSV: `exports/denials_recovery_aging_bands_v1.csv`
- Stability CSV: `exports/denials_recovery_stability_v1.csv`
- Opportunity sizing CSV: `exports/denials_recovery_opportunity_sizing_v1.csv`

## Opportunity & Capacity (Directional)
- Weekly touch budget: **10.0 hours**
- Effective touch minutes: **12.0**
- Expected touches/week: **50.0**
- No outcomes file provided: capacity outputs are directional placeholders.

## Outcome Tracking (Learning Loop)
- No outcomes file provided yet (`--outcomes-csv` not supplied).
- Outcomes remain directional until sourced from adjudication/ERA-quality systems.
