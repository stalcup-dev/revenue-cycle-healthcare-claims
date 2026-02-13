# Denials Prevention Opportunity Brief v1

Source relation: `rcm-flagship.rcm.mart_workqueue_claims` (dbt mart only).

## Impact in 90 Seconds (Prevention)
- Current dataset-week: `2011-02-14`
- Prior dataset-week: `2011-02-07`
- Total denied exposure (PROXY): $11,210
- Total prevented exposure proxy: $9,134
- Top 2 buckets: AUTH_ELIG, OTHER_PROXY
- Top 2 prevented share: 91.5%
- Stability confidence: HIGH (TOP2_OVERLAP=2/2)
- Workqueue size used: 25

## Prevention scenarios (directional)
| denial_bucket | prevented_exposure_proxy | prevent_10 | prevent_20 | prevent_30 |
|---|---:|---:|---:|---:|
| AUTH_ELIG | $6,020 | $602 | $1,204 | $1,806 |
| OTHER_PROXY | $2,340 | $234 | $468 | $702 |

## Levers & owners (next week)
### AUTH_ELIG
- Owner: Eligibility/Auth team
- Levers:
  - Tighten auth-at-registration checks.
  - Route missing-auth claims to pre-bill review.
  - Apply payer-specific eligibility retry before finalization.
- Evidence needed:
  - Auth number
  - Eligibility response timestamp
### OTHER_PROXY
- Owner: RCM analyst review
- Levers:
  - Manually tag top unresolved reasons each cycle.
  - Expand mapping rules from recurring patterns.
  - Route ambiguous denials to analyst triage SLA.
- Evidence needed:
  - Denial text
  - Manual categorization note

## Data gaps and proxy caveats
- `payer_dim_status` is fixed to `MISSING_IN_MART`.
- `denied_amount` uses `denied_potential_allowed_proxy_amt` (proxy).
- Safe for directional prevention prioritization, not causal savings claims.
