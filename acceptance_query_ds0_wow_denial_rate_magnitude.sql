-- DS0 Test: wow_denial_rate_pp magnitude matches 100×(fraction_diff)
-- Purpose: Verify denial rate WoW calculation is correct (percentage points)

with ds0 as (
    select
        week_start,
        denial_rate,
        wow_denial_rate_pp
    from {{ ref('mart_exec_overview_latest_week') }}
    where wow_denial_rate_pp is not null
),
prior_week as (
    select denial_rate as prior_denial_rate
    from {{ ref('mart_exec_kpis_weekly_complete') }}
    where is_complete_week
      and week_start = (
          select prior_complete_week_start 
          from {{ ref('mart_exec_overview_latest_week') }}
      )
)

select
    ds0.week_start,
    ds0.denial_rate,
    prior_week.prior_denial_rate,
    ds0.wow_denial_rate_pp as reported_wow_pp,
    100 * (ds0.denial_rate - prior_week.prior_denial_rate) as expected_wow_pp,
    abs(ds0.wow_denial_rate_pp - 100 * (ds0.denial_rate - prior_week.prior_denial_rate)) as magnitude_diff,
    case 
        when abs(ds0.wow_denial_rate_pp - 100 * (ds0.denial_rate - prior_week.prior_denial_rate)) < 0.01
            then '✓ PASS'
        else '✗ FAIL'
    end as test_result
from ds0
cross join prior_week
