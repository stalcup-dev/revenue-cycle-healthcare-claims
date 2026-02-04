# Workqueue Playbook (Claim-level)

## Objective
Operationalize claim follow-up by prioritizing the highest expected financial impact per unit of team capacity.

## Workqueue unit
**Claim-level** (assignable). Line-level features roll up to a claim priority score with drill-down.

## Core scoring (v1)
- payer_yield_gap_amt (mature window leakage)
- denied_potential_allowed_amt (proxy dollars for denied lines with allowed=0 and paid=0)
- $at_risk_amt = payer_yield_gap_amt + denied_potential_allowed_amt

## Risk + urgency signals (v1)
- p_denial proxy: share of denial-coded lines on the claim
- aging_days: days since svc_dt
- capacity gating: take top N claims/day (configurable)

## Explainability fields (must-have)
- top_hcpcs_by_at_risk
- top_denial_code
- is_msp_cob flag
- svc_month cohort

## Success metrics
- Reduction in mature payer_yield_gap_amt
- Reduction in denial rate on comparable claims
- Faster resolution for top deciles of $at_risk
- Stability checks: mix drift, immature-period contamination, unknown PRCSG share
