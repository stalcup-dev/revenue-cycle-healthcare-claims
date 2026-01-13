-- DS0 Test: WoW numeric fields are NOT NULL when prior_complete_week_start exists
-- Purpose: Verify WoW deltas populated when prior week available

select
    week_start,
    prior_complete_week_start,
    wow_yield_gap_amt_k,
    wow_payer_allowed_amt_k,
    wow_observed_paid_amt_k,
    wow_at_risk_amt_k,
    wow_denial_rate_pp,
    wow_n_claims,
    case 
        when prior_complete_week_start is not null
            and wow_yield_gap_amt_k is null
            then '✗ FAIL: wow_yield_gap_amt_k is NULL but prior exists'
        when prior_complete_week_start is not null
            and wow_payer_allowed_amt_k is null
            then '✗ FAIL: wow_payer_allowed_amt_k is NULL but prior exists'
        when prior_complete_week_start is not null
            and wow_observed_paid_amt_k is null
            then '✗ FAIL: wow_observed_paid_amt_k is NULL but prior exists'
        when prior_complete_week_start is not null
            and wow_at_risk_amt_k is null
            then '✗ FAIL: wow_at_risk_amt_k is NULL but prior exists'
        when prior_complete_week_start is not null
            and wow_denial_rate_pp is null
            then '✗ FAIL: wow_denial_rate_pp is NULL but prior exists'
        when prior_complete_week_start is not null
            and wow_n_claims is null
            then '✗ FAIL: wow_n_claims is NULL but prior exists'
        when prior_complete_week_start is null
            and (wow_yield_gap_amt_k is not null 
                 or wow_payer_allowed_amt_k is not null
                 or wow_observed_paid_amt_k is not null
                 or wow_at_risk_amt_k is not null
                 or wow_denial_rate_pp is not null
                 or wow_n_claims is not null)
            then '✗ FAIL: WoW fields NOT NULL but no prior exists'
        else '✓ PASS'
    end as test_result
from {{ ref('mart_exec_overview_latest_week') }}
