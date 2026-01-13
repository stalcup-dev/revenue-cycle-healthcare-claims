-- DS0 Test: week_start equals latest_complete_week_start from weekly_complete
-- Purpose: Verify DS0 is anchored to latest COMPLETE week

with ds0 as (
    select week_start
    from {{ ref('mart_exec_overview_latest_week') }}
),
expected_anchor as (
    select max(week_start) as expected_week_start
    from {{ ref('mart_exec_kpis_weekly_complete') }}
    where is_complete_week
)

select
    ds0.week_start as ds0_week_start,
    expected_anchor.expected_week_start,
    case 
        when ds0.week_start = expected_anchor.expected_week_start then '✓ PASS'
        else '✗ FAIL'
    end as test_result
from ds0
cross join expected_anchor
