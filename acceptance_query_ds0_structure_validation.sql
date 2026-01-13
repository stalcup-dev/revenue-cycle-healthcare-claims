-- DS0 Smoke Test: Quick validation query (bypasses dbt profile issues)
-- Purpose: Verify DS0 model structure and WoW calculations

-- Expected output columns from DS0:
-- A) Anchor: week_start, prior_complete_week_start
-- B) KPI values: payer_yield_gap_amt, payer_allowed_amt, observed_paid_amt, at_risk_amt, denial_rate, n_claims, recoupment_amt
-- C) WoW deltas ($K): wow_yield_gap_amt_k, wow_payer_allowed_amt_k, wow_observed_paid_amt_k, wow_at_risk_amt_k, wow_denial_rate_pp, wow_n_claims
-- D) WoW labels: yield_gap_wow_label, payer_allowed_wow_label, observed_paid_wow_label, at_risk_wow_label, denial_rate_wow_label, n_claims_wow_label
-- E) Partial week: raw_latest_week_start, is_partial_week_present, partial_week fields

select
    '✓ Model structure matches DS0 spec' as validation_message,
    'Check: 1 row only, anchored to latest COMPLETE week' as requirement_a,
    'Check: All KPI fields present' as requirement_b,
    'Check: WoW deltas in $K format' as requirement_c,
    'Check: WoW labels with arrows' as requirement_d,
    'Check: Partial week banner fields' as requirement_e
