-- DS0 Comprehensive Integration Test
-- Purpose: Single query to validate all DS0 requirements (A-E)
-- Run this after: dbt run --select mart_exec_overview_latest_week

-- Expected result: All test_status = '✓ PASS'

with ds0_output as (
    select * from {{ ref('mart_exec_overview_latest_week') }}
),
latest_complete_from_source as (
    select max(week_start) as expected_week
    from {{ ref('mart_exec_kpis_weekly_complete') }}
    where is_complete_week
),
test_results as (
    select
        -- Test A1: Exactly 1 row
        count(*) as row_count,
        case when count(*) = 1 then '✓ PASS' else '✗ FAIL' end as test_a1_single_row,
        
        -- Test A2: Anchored to latest complete week
        max(week_start) as ds0_week,
        (select expected_week from latest_complete_from_source) as expected_week,
        case 
            when max(week_start) = (select expected_week from latest_complete_from_source) 
            then '✓ PASS' 
            else '✗ FAIL' 
        end as test_a2_correct_anchor,
        
        -- Test B: All KPI fields present and non-null
        case 
            when count(*) filter (where payer_yield_gap_amt is not null) = 1
                and count(*) filter (where payer_allowed_amt is not null) = 1
                and count(*) filter (where observed_paid_amt is not null) = 1
                and count(*) filter (where at_risk_amt is not null) = 1
                and count(*) filter (where denial_rate is not null) = 1
                and count(*) filter (where n_claims is not null) = 1
                and count(*) filter (where recoupment_amt is not null) = 1
            then '✓ PASS'
            else '✗ FAIL'
        end as test_b_kpi_fields_present,
        
        -- Test C: WoW fields structure
        case 
            when max(prior_complete_week_start) is null 
                and count(*) filter (where wow_yield_gap_amt_k is not null) = 0
            then '✓ PASS (no prior week)'
            when max(prior_complete_week_start) is not null
                and count(*) filter (where wow_yield_gap_amt_k is not null) = 1
                and count(*) filter (where wow_payer_allowed_amt_k is not null) = 1
                and count(*) filter (where wow_observed_paid_amt_k is not null) = 1
                and count(*) filter (where wow_at_risk_amt_k is not null) = 1
                and count(*) filter (where wow_denied_proxy_amt_k is not null) = 1
                and count(*) filter (where wow_denial_rate_pp is not null) = 1
                and count(*) filter (where wow_n_claims is not null) = 1
            then '✓ PASS'
            else '✗ FAIL'
        end as test_c_wow_deltas_correct,
        
        -- Test D: WoW label fields present
        case 
            when max(prior_complete_week_start) is null 
                and count(*) filter (where yield_gap_wow_label is not null) = 0
            then '✓ PASS (no prior week)'
            when max(prior_complete_week_start) is not null
                and count(*) filter (where yield_gap_wow_label is not null) = 1
                and count(*) filter (where payer_allowed_wow_label is not null) = 1
                and count(*) filter (where observed_paid_wow_label is not null) = 1
                and count(*) filter (where at_risk_wow_label is not null) = 1
                and count(*) filter (where denied_proxy_wow_label is not null) = 1
                and count(*) filter (where denial_rate_wow_label is not null) = 1
                and count(*) filter (where n_claims_wow_label is not null) = 1
            then '✓ PASS'
            else '✗ FAIL'
        end as test_d_wow_labels_present,
        
        -- Test E: Partial week banner fields present
        case 
            when count(*) filter (where raw_latest_week_start is not null) = 1
                and count(*) filter (where is_partial_week_present is not null) = 1
            then '✓ PASS'
            else '✗ FAIL'
        end as test_e_partial_week_fields
        
    from ds0_output
)

select
    '📊 DS0 Comprehensive Test Results' as test_suite,
    row_count,
    test_a1_single_row as a1_single_row,
    test_a2_correct_anchor as a2_correct_anchor,
    ds0_week,
    expected_week,
    test_b_kpi_fields_present as b_kpi_fields,
    test_c_wow_deltas_correct as c_wow_deltas,
    test_d_wow_labels_present as d_wow_labels,
    test_e_partial_week_fields as e_partial_fields,
    case 
        when test_a1_single_row = '✓ PASS'
            and test_a2_correct_anchor = '✓ PASS'
            and test_b_kpi_fields_present = '✓ PASS'
            and test_c_wow_deltas_correct like '✓ PASS%'
            and test_d_wow_labels_present like '✓ PASS%'
            and test_e_partial_week_fields = '✓ PASS'
        then '✅ ALL TESTS PASS'
        else '❌ SOME TESTS FAILED'
    end as overall_status
from test_results
